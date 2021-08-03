"""Run Extracting Infos

Iterate the replay directory and generate a CSV file.
Each line corresponds to the info of the replay."""
import logging
from os import path
import os

from absl import app
from absl import flags
from pysc2 import run_configs
from s2clientprotocol.common_pb2 import NoRace, Zerg, Terran, Protoss, Random
from s2clientprotocol.sc2api_pb2 import Result
from s2clientprotocol import sc2api_pb2 as sc_pb

from timitate.utils_replay.rpt_master import RPTMaster
from timitate.utils_replay.rpt_worker import RPTWorker
from timitate.utils.utils import get_player_info_by_player_id
from timitate.utils_replay import get_dft_sc2_interface


FLAGS = flags.FLAGS
flags.DEFINE_string("role", '', '[master, worker]')
flags.DEFINE_integer("master_port", 7788, "master service port")
flags.DEFINE_string("master_hostname", 'localhost', 'master hostname or IP')
flags.DEFINE_string("output_data_csv_path", '/root/zstat/yymmddmmss',
                    "path where the data source writes to.")
flags.DEFINE_string("replay_dir", '/root/replays',
                    'dir where each replay files are stored')
flags.DEFINE_string("game_version", '4.7.1', 'StarCraftII Env Game Version')
flags.DEFINE_string("sc2mv_bin_root", '/root/SC2',
                    'The root directory for multiple-version SCII game core '
                    'binaries. e.g., '
                    'setting it to /root/SC2 means it looks like: '
                    '/root/SC2/4.7.1 '
                    '/root/SC2/4.8.0 '
                    '/root/SC2/4.9.0 '
                    '...')


class MyResult(object):
  def __init__(self, replay_name, player_id, map_name, race_actual,
               race_requested, result, mmr, apm, game_duration_loops,
               game_version, start_pos_x, start_pos_y, status):
    self.replay_name = replay_name
    self.player_id = player_id
    self.map_name = map_name
    self.race_actual = race_actual
    self.race_requested = race_requested
    self.result = result
    self.mmr = mmr
    self.apm = apm
    self.game_duration_loops = game_duration_loops
    self.game_version = game_version
    self.start_pos_x = start_pos_x
    self.start_pos_y = start_pos_y
    self.status = status


_PB_RACE_TO_STR = {
  NoRace: 'NoRace',
  Zerg: 'Zerg',
  Terran: 'Terran',
  Protoss: 'Protoss',
  Random: 'Random'
}


_PB_RESULT_TO_STR = {
  Result.Victory: 'Victor',
  Result.Defeat: 'Defeat',
  Result.Tie: 'Tie',
  Result.Undecided: 'Undecided'
}


def main_master():
  with open(FLAGS.output_data_csv_path, 'wt') as f:
    header = ','.join([
      'replay_name',
      'player_id',
      'map_name',
      'race_actual',
      'race_requested',
      'result',
      'mmr',
      'apm',
      'game_duration_loops',
      'game_version',
      'start_pos_x',
      'start_pos_y'
    ])
    f.write(header + "\n")

  n_received = 0
  def write_to_csv(r: MyResult):
    nonlocal n_received
    logging.info('received result count {}, status: {}:'.format(n_received,
                                                                r.status))
    n_received = n_received + 1
    if r.status != 'success':
      logging.info('skip writing due to the corrupted status')
    with open(FLAGS.output_data_csv_path, 'at') as f:
      tmp = [
        r.replay_name,
        r.player_id,
        r.map_name,
        r.race_actual,
        r.race_requested,
        r.result,
        r.mmr,
        r.apm,
        r.game_duration_loops,
        r.game_version,
        '{:.1f}'.format(r.start_pos_x),
        '{:.1f}'.format(r.start_pos_y)
      ]
      f.write(','.join([str(each) for each in tmp])  +'\n')

  logging.info('use master port {}'.format(FLAGS.master_port))
  m = RPTMaster(port=FLAGS.master_port,
                replay_dir=FLAGS.replay_dir,
                fun_result=write_to_csv)
  m.run()


def main_worker():

  def _extract_info(replay_name, player_id):
    logging.info('enter _extract_info')
    logging.info('replay_name: {}, player_id: {}'.format(
      replay_name, player_id))

    # set the correct sc2 bin path according to the game_version
    game_version = FLAGS.game_version
    if game_version != '4.7.1' or 'SC2PATH' in os.environ:
      # os.environ['SC2PATH'] = '/root/{}'.format(game_version)
      os.environ['SC2PATH'] = path.join(FLAGS.sc2mv_bin_root, game_version)

    # reset env/process replay from the beginning
    run_config = run_configs.get()
    replay_path = path.join(FLAGS.replay_dir, '%s.SC2Replay' % replay_name)
    replay_data = run_config.replay_data(replay_path)

    # read once
    with run_config.start(version=FLAGS.game_version) as controller:
      replay_info = controller.replay_info(replay_data)
      assert player_id in set(p.player_info.player_id
                              for p in replay_info.player_info)
      player_info = get_player_info_by_player_id(replay_info, player_id)

      # collect all infos before starting the replay
      map_name = str(replay_info.map_name)
      race_actual = _PB_RACE_TO_STR[player_info.player_info.race_actual]
      race_requested = _PB_RACE_TO_STR[
        player_info.player_info.race_requested]
      result = _PB_RESULT_TO_STR[player_info.player_result.result]
      mmr = player_info.player_mmr
      apm = player_info.player_apm
      game_duration_loops = replay_info.game_duration_loops
      game_version = replay_info.game_version

      map_data = None
      if replay_info.local_map_path:
        map_data = run_config.map_data(replay_info.local_map_path)
        print('using local_map_path {}'.format(replay_info.local_map_path))

      # collect all infos after starting the replay
      controller.start_replay(sc_pb.RequestStartReplay(
        replay_data=replay_data,
        map_data=map_data,
        options=get_dft_sc2_interface(),
        observed_player_id=player_id,
        disable_fog=False))
      game_info = controller.game_info()
      start_pos = game_info.start_raw.start_locations[0]

      # and deem as success
      status = 'success'

    logging.info('leave _extract_info')
    return MyResult(
      replay_name=replay_name,
      player_id=player_id,
      map_name=map_name,
      race_actual=race_actual,
      race_requested=race_requested,
      result=result,
      mmr=mmr,
      apm=apm,
      game_duration_loops=game_duration_loops,
      game_version=game_version,
      start_pos_x=start_pos.x,
      start_pos_y=start_pos.y,
      status=status
    )

  master_endpoint = '{}:{}'.format(FLAGS.master_hostname, FLAGS.master_port)
  logging.info('connecting to master {}'.format(master_endpoint))
  w = RPTWorker(
    master_endpoint=master_endpoint,
    fun_proc_replay=_extract_info,
  )
  w.run()


def main(_):
  if FLAGS.role == 'master':
    main_master()
  else:
    main_worker()


if __name__ == '__main__':
  app.run(main)