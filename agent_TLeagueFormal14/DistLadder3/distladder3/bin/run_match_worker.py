""" Run a match worker. """
from absl import app
from absl import flags

from distladder3.cores.match_worker import SC2MatchWorker


FLAGS = flags.FLAGS
# flags.log_dir has been defined to this extent
flags.DEFINE_string("match_server_endpoint", "127.0.0.1:6788",
                    "mathch server endpoint")
flags.DEFINE_integer("game_port", 13800, "SC2 game Config port.")
flags.DEFINE_string("game_version", '4.1.2', 'StarCraftII Env Game Version')
flags.DEFINE_string("map", 'AbyssalReef', 'Game Map Name.')
flags.DEFINE_integer("timeout", -1,
                     "timeout in seconds. "
                     "Setting it to -1 means no timeout, wait forever.")
flags.DEFINE_integer("game_steps_per_episode", 48000,
                     "Game steps per episode, independent of the step_mul."
                     "0 means no limit.")


def main(_):
  worker = SC2MatchWorker(FLAGS.match_server_endpoint,
                          FLAGS.game_version,
                          FLAGS.map,
                          log_dir=FLAGS.log_dir,
                          timeout=FLAGS.timeout,
                          game_steps_per_episode=FLAGS.game_steps_per_episode)
  worker.run(port=FLAGS.game_port)


if __name__ == "__main__":
  app.run(main)