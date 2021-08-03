"""Run Extracting Z Statistics"""
import logging
from os import path
import os

from absl import app
from absl import flags
from pysc2 import run_configs
from s2clientprotocol import sc2api_pb2 as sc_pb

from timitate.utils_replay.rpt_master import RPTInfoCSVMaster
from timitate.utils_replay.rpt_worker import RPTWorker
from timitate.utils.rep_db import RepDBFS
from timitate.utils.rep_db import rep_info_to_unique_key
import timitate.lib6.pb2zstat_converter as pb2zstat_lib
from timitate.utils_replay import get_dft_sc2_interface


FLAGS = flags.FLAGS
flags.DEFINE_string("role", '', '[master, worker]')
flags.DEFINE_integer("master_port", 7788, "master service port")
flags.DEFINE_string("master_hostname", 'localhost', 'master hostname or IP')
flags.DEFINE_string("info_csv_path", '/root/filtered-infos.csv',
                    'path for the info csv')
flags.DEFINE_string("output_data_src_path", '/root/zstat/yymmddmmss',
                    "path where the data source writes to.")
flags.DEFINE_string("replay_dir", '/root/replays',
                    'dir where each replay files are stored')
flags.DEFINE_integer("step_mul", 2,
                     "step_mul when parsing replay. Smaller step_mul leads to "
                     "more accurate zstat and much lower speed as well.")
flags.DEFINE_string('zstat_converter', 'PB2ZStatConverterV3', 'zstat converter')
flags.DEFINE_string("sc2mv_bin_root", '/root',
                    'The root directory for multiple-version SCII game core '
                    'binaries. e.g., '
                    'setting it to /root/SC2 means it looks like: '
                    '/root/SC2/4.7.1 '
                    '/root/SC2/4.8.0 '
                    '/root/SC2/4.9.0 '
                    '...')


class MyResult(object):
  def __init__(self, replay_name, player_id, game_version, zstat, status):
    self.replay_name = replay_name
    self.player_id = player_id
    self.game_version = game_version
    self.zstat = zstat
    self.status = status


def main_master():
  n_received = 0
  def count_print(r: MyResult):
    nonlocal n_received
    logging.info('received result count {}:'.format(n_received))
    logging.info(
      'replay_name: {}, palyer_id: {}, game_version {},  status: {}'.format(
      r.replay_name, r.player_id, r.game_version, r.status)
    )
    n_received = n_received + 1

  logging.info('use master port {}'.format(FLAGS.master_port))
  m = RPTInfoCSVMaster(port=FLAGS.master_port,
                       info_csv_path=FLAGS.info_csv_path,
                       fun_result=count_print)
  m.run()


def main_worker():
  db = RepDBFS(FLAGS.output_data_src_path)

  def _extract_zstat(replay_name, player_id, game_version):
    logging.info('enter _extract_zstat')
    logging.info('replay_name: {}, player_id: {}, game_version: {}'.format(
      replay_name, player_id, game_version))

    # skip if the zstat exists in db
    if db.get(rep_info_to_unique_key(replay_name, player_id)) is not None:
      logging.info('leave _extract_z_stat, skipped.')
      return MyResult(replay_name, player_id, game_version, None,
                      'skipped writing')

    # set the correct sc2 bin path according to the game_version
    if game_version != '4.7.1' or 'SC2PATH' in os.environ:
      # os.environ['SC2PATH'] = '/root/{}'.format(game_version)
      os.environ['SC2PATH'] = path.join(FLAGS.sc2mv_bin_root, game_version)

    # what converter
    cvt_cls = getattr(pb2zstat_lib, FLAGS.zstat_converter)
    pb2zstat_cvt = cvt_cls()
    # reset analyzers
    pb2zstat_cvt.reset()

    # reset env/process replay from the beginning
    run_config = run_configs.get()
    replay_path = path.join(FLAGS.replay_dir, '%s.SC2Replay' % replay_name)
    replay_data = run_config.replay_data(replay_path)

    # step each frame w. step_mul
    with run_config.start(version=game_version) as controller:
      replay_info = controller.replay_info(replay_data)
      map_data = None
      if replay_info.local_map_path:
        map_data = run_config.map_data(replay_info.local_map_path)
        print('using local_map_path {}'.format(replay_info.local_map_path))
      assert player_id in set(p.player_info.player_id
                              for p in replay_info.player_info)
      controller.start_replay(sc_pb.RequestStartReplay(
        replay_data=replay_data,
        map_data=map_data,
        options=get_dft_sc2_interface(),
        observed_player_id=player_id,
        disable_fog=False))
      controller.step()
      while True:
        pb_obs = controller.observe()
        zstat = pb2zstat_cvt.convert(pb_obs)
        if pb_obs.player_result:
          # episode end, the zstat to this extent is what we need
          break
        # step the replay
        controller.step(FLAGS.step_mul)

    logging.info('writing to db...')
    db.put(rep_info_to_unique_key(replay_name, player_id), zstat)
    logging.info('leave _extract_z_stat')
    return MyResult(replay_name, player_id, game_version, zstat,
                    'successful writing to db')

  master_endpoint = '{}:{}'.format(FLAGS.master_hostname, FLAGS.master_port)
  logging.info('connecting to master {}'.format(master_endpoint))
  w = RPTWorker(
    master_endpoint=master_endpoint,
    fun_proc_replay=_extract_zstat,
  )
  w.run()


def main(_):
  if FLAGS.role == 'master':
    main_master()
  else:
    main_worker()


if __name__ == '__main__':
  app.run(main)