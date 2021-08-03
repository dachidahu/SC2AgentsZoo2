""" Run a match server.

Start a match server. See the Msg definition from distladder3.match_server
It receives scheduled matches and writes results to pgn file.

Example:

python3 run_match_server.py \
  --port 6788 \
  --pgn_dir /root/eval_results/evTimstamp

"""
import logging

from absl import app
from absl import flags

from distladder3.cores.match_server import MatchServer


FLAGS = flags.FLAGS
flags.DEFINE_integer("port", 6788, "service port")
flags.DEFINE_string("output_pgn_dir", '/root/evdir',
                    "dir to be written pgn files.")


def main(_):
  logging.info('use port {}'.format(FLAGS.port))
  match_server = MatchServer(port=FLAGS.port,
                             output_pgn_dir=FLAGS.output_pgn_dir)
  match_server.run()


if __name__ == '__main__':
  app.run(main)
