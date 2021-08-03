import socket
from os import path


class Player(object):
  def __init__(self, name, agent_dir, agent_config):
    self.name = name
    self.agent_dir = agent_dir
    self.agent_config = agent_config


class Match(object):
  def __init__(self, players, match_id):
    self.players = players
    self.match_id = match_id


class PgnMatch(object):
  def __init__(self):
    self.event = None
    self.site = None
    self.date = None
    self.round = None
    self.white = None
    self.black = None
    self.result = None


def split_model_filename(model_filename):
  """ e.g., '0001:0008_201908334455' -> ('0001:0008', '201908334455') """
  fn, dummy_ext = path.splitext(model_filename)
  parts = fn.split('_')
  # can be 'init_model:0001_yymmddss' or '0005:0012_yymmddss'
  if len(parts) <= 1:
    model_key = parts[0]
    timestamp = ''
  else:
    model_key = '_'.join(parts[0:-1])
    timestamp = parts[-1]
  return model_key, timestamp


def get_parent_me(model_key):
  """ e.g., 0001:0009 -> 0001, 0009"""
  return model_key.split(':')


def find_all_matched_pattern(pattern, lst):
  return [f for f in lst if pattern in f]


def find_first_matched_pattern(ptn, lst):
  for item in lst:
    if ptn in item:
      return item
  return None


def unique_match_key(p0name, p1name):
  return (p0name + '_vs_' + p1name if p0name < p1name
          else p1name + '_vs_' + p0name)


def get_ip_address():
  s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  s.connect(("8.8.8.8", 80))
  return s.getsockname()[0]


def get_num_lines(filename):
  """ get number of lines. borrowed from
  https://stackoverflow.com/questions/845058/how-to-get-line-count-cheaply-in-python """
  f = open(filename, 'rb')
  lines = 0
  buf_size = 1024 * 1024
  read_f = f.raw.read

  buf = read_f(buf_size)
  while buf:
    lines += buf.count(b'\n')
    buf = read_f(buf_size)
  return lines


def to_cmd_str(cmds):
  if isinstance(cmds, (list, tuple)):
    # cmds = " ".join(shlex_quote(str(v)) for v in cmds)
    cmds = ' '.join(str(v) for v in cmds)
  return cmds


def create_sc2_cmd(player: Player, mode, replay_dir='./', port=None, bot_level=None,
                   bot_race='Z', map='AbyssalReef', game_version='4.1.2',
                   game_steps_per_episode=0):
  python_bin = path.join(player.agent_dir, 'myenv/bin/python')
  cmds = ["cd " + player.agent_dir + ';',
          'export http_proxy= ;',
          'export https_port= ;',
          python_bin,
          '-m distladder3.cores.games.run_agent',
          '--mode', mode,
          '--map', map,
          '--game_version', game_version,
          '--game_steps_per_episode', str(game_steps_per_episode),
          '--replay_dir=' + replay_dir,
          '--agent_name=' + str(player.name),
          '--agent_config=' + str(player.agent_config)]
  if mode == 'sp':
    assert bot_level is not None
    cmds += ['--bot_race', bot_race,
             '--difficulty', bot_level]
  elif mode in ['host', 'client']:
    assert port is not None
    cmds += ['--port', str(port)]
  else:
    raise ValueError('unknown mode %s'.format(mode))
  return to_cmd_str(cmds)