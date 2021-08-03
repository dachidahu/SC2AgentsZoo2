""" run a match with an agent on remote machine, modified from Deepmind PySC2 and DistLadderV1.

This needs to be called twice, once for the human, and once for the agent.

In two different machine:
The human plays on the host. There you run it as:
$ python -m distladder3.bin.play_vs_remote_agent --human --remote <agent ip>

And on the machine the agent plays on:
$ python -m distladder3.bin.play_vs_remote_agent --player_name_path_config name,agent_dir,agent_config

In a single machine:
The human plays on the host. There you **DONT** use --remote arg and run it as:
$ python -m distladder3.bin.play_vs_remote_agent --human

And on the **SAME** machine, run the agent:
$ python -m distladder3.bin.play_vs_remote_agent --player_name_path_config name,agent_dir,agent_config

"""
import time
import subprocess

from absl import app
from absl import flags
from pysc2.lib import protocol
from distladder3.utils import Player
from distladder3.utils import create_sc2_cmd
from distladder3.cores.games.sc2game import sc2game


FLAGS = flags.FLAGS
flags.DEFINE_integer("port", 6789, "game config port")
flags.DEFINE_string("remote", None,
                    "Hostname or IP indicating where to set up the ssh tunnels "
                    "to the client.")
flags.DEFINE_bool("human", False, "Whether to host a game as a human.")
flags.DEFINE_string(
  "player_name_path_config",
    "RandAgt,~/SC2AgentsZoo/agent_TStarBot/,",
  "name,dir_full_path,config ",
  short_name='p'
)
flags.DEFINE_string("race", 'Z', "Race. Z|P|T")
flags.DEFINE_string("map", 'KairosJunction', "game map")
flags.DEFINE_string("game_version", '4.7.1', "game version")
flags.DEFINE_string("replay_dir", './', "replay saving dir")
flags.DEFINE_string("replay_name", None, "replay saving dir")
flags.DEFINE_string("player_name", 'Human Player', "replay saving dir")
flags.DEFINE_integer("replay_interval", 60, "replay saving dir")


def main(_):
  if FLAGS.human:
    game = sc2game(mode='host', port=FLAGS.port, replay_dir=FLAGS.replay_dir,
                   realtime=True, remote=FLAGS.remote, map=FLAGS.map,
                   game_version=FLAGS.game_version, race=FLAGS.race,
                   agent_name=FLAGS.player_name)
    game.env.reset()
    total_sleep_time = 0
    while True:
      time.sleep(1)
      total_sleep_time += 1
      game.env._controllers[0].ping()
      status = game.env._controllers[0].status
      # print(status)
      if status == protocol.Status.ended:
        time.sleep(0.1)
        print('Game ended, save replay...')
        game.env.save_replay(replay_dir=FLAGS.replay_dir,
                             replay_name=FLAGS.replay_name)
        exit(0)
      if (FLAGS.replay_interval > 0
          and total_sleep_time % FLAGS.replay_interval == 0):
        game.env.save_replay(replay_dir=FLAGS.replay_dir,
                             replay_name=FLAGS.replay_name)
  else:
    pnpc = FLAGS.player_name_path_config.split(',')
    assert (len(pnpc) == 3)
    player = Player(name=pnpc[0], agent_dir=pnpc[1], agent_config=pnpc[2])
    cmd = create_sc2_cmd(player, mode='client', port=FLAGS.port, map=FLAGS.map,
                         game_version=FLAGS.game_version,
                         replay_dir=FLAGS.replay_dir)
    child1 = subprocess.Popen(cmd, shell=True)
    child1.wait()


if __name__ == '__main__':
  app.run(main)
