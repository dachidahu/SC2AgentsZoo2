""" Run a PgnRatings.

It watches png files dir and writes pairwise pgn file and elo score files to
the the corresponding sub dir.

Example:

python3 run_pgn_ratings.py \
  --watched_pgn_files_dir /root/eval_results
"""
import logging

from absl import app
from absl import flags

from distladder3.results_tool.pgn_ratings import PgnRatings


FLAGS = flags.FLAGS
flags.DEFINE_string("watched_pgn_files_dir", '/root/eval_results',
                    "Watched pgn files dir during training."
                    "The output files go into the same dir. ")
flags.DEFINE_string("output_dir", '/root/eval_results',
                    "output dir where the scores files go.")


def main(_):
  logging.info('start watching {}'.format(FLAGS.watched_pgn_files_dir))
  pgn = PgnRatings(watched_pgn_files_dir=FLAGS.watched_pgn_files_dir,
                   output_dir=FLAGS.output_dir)
  pgn.run()


if __name__ == '__main__':
  app.run(main)