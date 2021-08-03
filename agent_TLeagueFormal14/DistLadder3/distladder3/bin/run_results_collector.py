""" Run a collector.

Example:

python3 run_results_collector.py \
  --port 6788 \
  --watched_results_dir /root/results
"""
import logging

from absl import app
from absl import flags

from distladder3.results_tool.results_collector import ResultsCollector


FLAGS = flags.FLAGS
flags.DEFINE_string("port", '6888', "port ")
flags.DEFINE_string("watched_results_dir", '/root/eval_results',
                    "output dir where the scores files reside.")


def main(_):
  logging.info('start watching {}'.format(FLAGS.watched_results_dir))
  clt = ResultsCollector(port=FLAGS.port,
                         watched_results_dir=FLAGS.watched_results_dir)
  clt.run()


if __name__ == '__main__':
  app.run(main)