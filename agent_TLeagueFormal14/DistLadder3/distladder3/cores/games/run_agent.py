#!/usr/bin/python
""" This file is for internal call only. """
import sys

from absl import app
from absl import flags

from distladder3.cores.games.sc2game import sc2game


FLAGS = flags.FLAGS
flags.DEFINE_string("replay_dir", '', "path to save replay")
flags.DEFINE_string("game_id", '', "uuid for each game")
flags.DEFINE_string("mode", 'sp', "{sp, host, client}")
flags.DEFINE_string("map", 'AbyssalReef', "Map Name")
flags.DEFINE_string("game_version", '4.1.2', 'StarCraftII Env Game Version')
flags.DEFINE_string("agent_name", '', "agent_name")
flags.DEFINE_string("agent_config", '', "agent_config")
flags.DEFINE_string("bot_race", 'Z', "{Z, T, P, R}")  # used only for sp mode
flags.DEFINE_integer("difficulty", 7, "{1, ..., 10}")  # used only for sp mode
flags.DEFINE_integer("port", 13800,
                     "Config port for LanSC2Env")  # used only for non-sp mode
flags.DEFINE_integer("game_steps_per_episode", 48000,
                     "Game steps per episode, independent of the step_mul."
                     "0 means no limit.")


def main(unused_argv):
  try:
    sys.path.append('./')
    print('----')
    from agent import Agent
    # First,
    print('Start agent.')
    agent = Agent(FLAGS.agent_config or None)
    # Second, do NOT change the starting order!
    env_config = 'env_config.ini'
    print('Start env.')
    game = sc2game(env_config, FLAGS.game_id, mode=FLAGS.mode, map=FLAGS.map,
                   game_version=FLAGS.game_version, port=FLAGS.port,
                   replay_dir=FLAGS.replay_dir, bot_race=FLAGS.bot_race,
                   difficulty=FLAGS.difficulty, agent_name=FLAGS.agent_name,
                   game_steps_per_episode=FLAGS.game_steps_per_episode)

    print('Start run loop.')
    try:
      result = game.run(agent)
    finally:
      game.env.close()
    print("Result: " + str(result))
  except KeyboardInterrupt:
    pass


if __name__ == "__main__":
  app.run(main)
