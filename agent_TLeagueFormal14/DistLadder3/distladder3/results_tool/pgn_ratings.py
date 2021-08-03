from os import path
import os
import logging
from subprocess import Popen, PIPE, STDOUT
from time import sleep


class PgnRatings(object):
  """ PGN Ratings.

  Scans the watched_pgn_files_dir, processes each found pgn file and outputs the
  scores to file with the same pgn basename and .scores prefix
  """
  def __init__(self, watched_pgn_files_dir, output_dir):
    self.watched_pgn_files_dir = watched_pgn_files_dir
    self.output_dir = output_dir
    pass

  def run(self):
    logging.info('enter PgnRatings.run')
    while True:
      pgn_files = _get_pgn_files(self.watched_pgn_files_dir)
      logging.info('found {} pgn_files'.format(len(pgn_files)))

      for f in pgn_files:
        pgn_path = path.join(self.watched_pgn_files_dir, f)
        ratings_path = path.join(self.output_dir,
                                 path.splitext(f)[0] + '.ratings')
        _produce_ratings(pgn_path, ratings_path)
        logging.info('processed {}, scores output to {}'.format(
          f, ratings_path))

      t_sleep = 12
      logging.info('sleep {} secs before next scanning...'.format(t_sleep))
      sleep(t_sleep)


def _get_pgn_files(watched_pgn_dir):
  return [f for f in os.listdir(watched_pgn_dir) if f.endswith('.pgn')]


def _produce_ratings(pgn_path, ratings_path):
  """ input pgn_path, output to ratings_path """
  BAYESELO_CMD_TMPL = (
    "readpgn {}\n"
    "elo\n"
    "ratings >{}\n"
  )
  bayeselo_cmd = BAYESELO_CMD_TMPL.format(pgn_path, ratings_path)
  p = Popen(['bayeselo'], stdout=PIPE, stdin=PIPE, stderr=STDOUT)
  stdoutput = p.communicate(bayeselo_cmd.encode('utf-8'))[0]
  print(stdoutput.decode())