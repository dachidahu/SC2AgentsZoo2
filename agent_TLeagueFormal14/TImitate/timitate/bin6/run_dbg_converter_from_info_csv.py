"""Run dbg"""
import logging
import os
from os import path
import subprocess

from absl import app
from absl import flags

from timitate.utils_replay.rpt_master import RPTInfoCSVMaster
from timitate.utils_replay.rpt_worker import RPTWorker


FLAGS = flags.FLAGS
flags.DEFINE_string("role", '', '[master, worker]')
flags.DEFINE_integer("master_port", 7788, "master service port")
flags.DEFINE_string("master_hostname", 'localhost', 'master hostname or IP')
flags.DEFINE_string("info_csv_path", '/root/filtered-infos.csv',
                    'path for the info csv')
flags.DEFINE_string("output_path", '/root/dbgyymmddmmss',
                    "path where the content goes.")
flags.DEFINE_string("replay_dir", '/root/replays',
                    'dir where each replay files are stored')
flags.DEFINE_string("zstat_data_src", './', "zstat_data_src")
flags.DEFINE_integer("step_mul", 1,
                     "step_mul when parsing replay")
flags.DEFINE_string("sc2mv_bin_root", '/root',
                    'The root directory for multiple-version SCII game core '
                    'binaries. e.g., '
                    'setting it to /root/SC2 means it looks like: '
                    '/root/SC2/4.7.1 '
                    '/root/SC2/4.8.0 '
                    '/root/SC2/4.9.0 '
                    '...')


class MyResult(object):
  def __init__(self, replay_name, player_id, game_version, stdout_str,
               stderr_str):
    self.replay_name = replay_name
    self.player_id = player_id
    self.game_version = game_version
    self.stdout_str = stdout_str
    self.stderr_str = stderr_str


def main_master():
  n_received = 0

  def write_result(r: MyResult):
    nonlocal n_received
    logging.info('received result count {}:'.format(n_received))
    msg = 'replay_name: {}, palyer_id: {}, game_version {}'.format(
      r.replay_name, r.player_id, r.game_version)
    logging.info(msg)
    n_received = n_received + 1

    with open(FLAGS.output_path, 'a') as f:
      f.write(msg + '\n')
      f.write(r.stdout_str + '\n')
      #f.write(r.stderr_str + '\n')

  logging.info('use master port {}'.format(FLAGS.master_port))
  m = RPTInfoCSVMaster(port=FLAGS.master_port,
                       info_csv_path=FLAGS.info_csv_path,
                       fun_result=write_result)
  m.run()


def main_worker():

  def _dbg_converter(replay_name, player_id, game_version):
    logging.info('enter _dbg_converter')
    logging.info('replay_name: {}, player_id: {}, game_version: {}'.format(
      replay_name, player_id, game_version))

    cmd = [
      'python3', '-m', 'timitate.bin6.debug_converters_v2',
      '--replay_dir', FLAGS.replay_dir,
      '--replay_name', replay_name,
      '--game_version', game_version,
      '--zstat_data_src', FLAGS.zstat_data_src,
      '--step_mul', str(FLAGS.step_mul),
      '--player_id', str(player_id)
    ]
    cmd = ' '.join(cmd)

    basename = path.join('/root', '{}-{}'.format(replay_name, player_id))
    log_file = open(basename + '.log', 'w')
    err_file = open(basename + '.err', 'w')
    log_file.write(cmd + '\n')
    log_file.flush()
    # our sc2 bin path
    my_env = os.environ.copy()
    my_env['SC2PATH'] = os.path.join(FLAGS.sc2mv_bin_root, game_version)
    child = subprocess.Popen(cmd, stdout=log_file, stderr=err_file,
                             shell=True, env=my_env)
    child.wait()
    log_file.close()
    err_file.close()

    # read the file contents
    with open(basename + '.log', 'rt') as f:
      stdout_str = f.read()
    with open(basename + '.err', 'rt') as f:
      stderr_str = f.read()

    return MyResult(replay_name, player_id, game_version, stdout_str,
                    stderr_str)

  master_endpoint = '{}:{}'.format(FLAGS.master_hostname, FLAGS.master_port)
  logging.info('connecting to master {}'.format(master_endpoint))
  w = RPTWorker(
    master_endpoint=master_endpoint,
    fun_proc_replay=_dbg_converter,
  )
  w.run()


def main(_):
  if FLAGS.role == 'master':
    main_master()
  else:
    main_worker()


if __name__ == '__main__':
  app.run(main)