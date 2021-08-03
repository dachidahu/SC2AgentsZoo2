import logging
from os import path
import os

import zmq


# GetRatings
class MsgRequestGetScores(object):
  def __init__(self):
    self.ratings_filename_patterns = []  # list of string


class MsgRespondGetScores(object):
  def __init__(self):
    self.scores = []  # each item is a dict {'p0name': r0, 'p1name': r1 ...}


# Impl
class ResultsCollector(object):
  """ Collector that collects various results.

  It watches the results_dir, receives messages to collect the scores.
  """

  def __init__(self, port, watched_results_dir):
    self.watched_results_dir = watched_results_dir

    context = zmq.Context()
    context.setsockopt(zmq.TCP_KEEPALIVE, 1)
    context.setsockopt(zmq.TCP_KEEPALIVE_CNT, 60)
    context.setsockopt(zmq.TCP_KEEPALIVE_IDLE, 60)
    context.setsockopt(zmq.TCP_KEEPALIVE_INTVL, 60)
    self._socket = context.socket(zmq.REP)
    self._socket.bind("tcp://*:{}".format(port))
    logging.info('serving at port {}'.format(port))

  def run(self):
    logging.info("Enter Collector.run")
    while True:
      # message loop
      request = self._socket.recv_pyobj()
      if isinstance(request, MsgRequestGetScores):
        response = self.respond_get_scores(request)
      else:
        raise RuntimeError("message {} not recognized".format(request))
      self._socket.send_pyobj(response)

  def respond_get_scores(self, request):
    logging.info('entering respond_get_scores')
    response = MsgRespondGetScores()
    ratings_files = _get_ratings_files(self.watched_results_dir)
    for p in request.ratings_filename_patterns:
      fn = _find_first_matched_fn(p, ratings_files)
      d_scores = {} if fn is None else (
        _extract_scores(path.join(self.watched_results_dir, fn))
      )
      response.scores.append(d_scores)
    logging.info('leaving respond_get_scores')
    return response


def _get_ratings_files(watched_results_dir):
  return [f for f in os.listdir(watched_results_dir)
          if path.isfile(path.join(watched_results_dir, f))
          and f.endswith('.ratings')]


def _find_first_matched_fn(p, ratings_files):
  for f in ratings_files:
    if p in f:
      return f
  return None


def _extract_scores(ratings_path):
  STR_Name = 'Name'
  STR_score = 'score' # Note: the bayeselo format
  percentage_to_float = lambda x: float(x.strip('%')) / 100

  d_scores = {}
  try:
    j_name, j_score = None, None
    with open(ratings_path, 'rt') as f:
      for i_row, line in enumerate(f):
        trimmed_line = ' '.join(line.split())  # long whitespace as one space
        items = trimmed_line.split(' ')
        if i_row == 0:
          j_name = items.index(STR_Name)
          j_score = items.index(STR_score)
          continue
        d_scores[items[j_name]] = percentage_to_float(items[j_score])
  except Exception as e:
    logging.info('error during _extract_scores: {}'.format(e))
  return d_scores