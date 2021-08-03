""" Run a player manager.
"""
from absl import app
from absl import flags

from distladder3.utils import Player
from distladder3.player_manager.player_manager import PlayerManager


FLAGS = flags.FLAGS
flags.DEFINE_string("port", '5526', "Player Manager port.")
flags.DEFINE_string("working_dir", '/root/work', "working idr.")
flags.DEFINE_multi_string(
  "predef_player",
  [
    "RandAgt,/root/SC2AgentsZoo/agent_Rand,",
    "Default_AI_10,/root/SC2AgentsZoo/,",
    "TStarBot,/root/SC2AgentsZoo/agent_TStarBot,tstarbot.agents.dft_config"
  ],
  "comma separated predefined player in name,dir_full_path,config "
  "can occur as many times as the number of total players."
)


def _get_players(player_name_path_config_lst):
  pnpc = [each.split(',') for each in player_name_path_config_lst]
  for each in pnpc:
    assert(len(each) == 3)  # precisely (name, dir, config)
  return [Player(name=each[0], agent_dir=each[1], agent_config=each[2]) for
          each in pnpc]


def main(_):
  predef_players = _get_players(FLAGS.predef_player)

  pm = PlayerManager(
    port=FLAGS.port,
    predef_players=predef_players,
    working_dir=FLAGS.working_dir
  )
  pm.run()


if __name__ == '__main__':
  app.run(main)
