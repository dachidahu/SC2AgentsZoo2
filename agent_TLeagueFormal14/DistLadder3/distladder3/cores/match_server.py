from collections import deque
import logging
from os import path

import zmq

from distladder3.utils import Match
from distladder3.utils import unique_match_key
from distladder3.utils import get_num_lines

# AddMatch
class MsgRequestAddMatch(object):
  def __init__(self):
    self.match_id = None
    self.players = []


class MsgRespondAddMatch(object):
  def __init__(self):
    self.status = 'success'


# GetNumFinishedMatches
class MsgRequestGetNumFinishedMatches(object):
  def __init__(self):
    self.player_names = []


class MsgRespondGetNumFinishedMatches(object):
  def __init__(self):
    self.num = 0


# StartMatchOnWorker
class MsgRequestStartMatchOnWorker(object):
  def __init__(self):
    pass


class MsgRespondStartMatchOnWorker(object):
  def __init__(self):
    self.match = None


# SendMatchResultFromWorker
class MsgRequestSendMatchResultFromWorker(object):
  def __init__(self):
    self.pgn_match = None
    self.info = None


class MsgRespondSendMatchResultFromWorker(object):
  def __init__(self):
    self.status = 'success'


class MatchServer(object):
  def __init__(self, port, output_pgn_dir='/root/pgn_results'):
    self.output_pgn_dir = output_pgn_dir

    context = zmq.Context()
    context.setsockopt(zmq.TCP_KEEPALIVE, 1)
    context.setsockopt(zmq.TCP_KEEPALIVE_CNT, 60)
    context.setsockopt(zmq.TCP_KEEPALIVE_IDLE, 60)
    context.setsockopt(zmq.TCP_KEEPALIVE_INTVL, 60)
    self._match_socket = context.socket(zmq.REP)
    self._match_socket.bind("tcp://0.0.0.0:{}".format(port))
    # self._match_socket.setsockopt(zmq.SNDHWM, 4)
    # self._match_socket.setsockopt(zmq.RCVHWM, 4)

    self._match_q = deque()  # matched to be run
    pass

  def run(self):
    logging.info("Enter MatchServer.run")
    while True:
      # message loop
      request = self._match_socket.recv_pyobj()
      if isinstance(request, MsgRequestAddMatch):
        response = self.respond_add_match(request)
      elif isinstance(request, MsgRequestGetNumFinishedMatches):
        response = self.respond_get_num_finished_matches(request)
      elif isinstance(request, MsgRequestStartMatchOnWorker):
        response = self.respond_start_match_over_worker(request)
      elif isinstance(request, MsgRequestSendMatchResultFromWorker):
        response = self.respond_send_match_result_from_worker(request)
      else:
        raise RuntimeError("message {} not recognized".format(request))
      self._match_socket.send_pyobj(response)

  def respond_add_match(self, request):
    logging.info('Entering respond_add_match, len(_match_q): {}'.format(
      len(self._match_q)))
    response = MsgRespondAddMatch()

    # check players validity
    players = request.players
    if 'Default_AI' in players[0].name and 'Default_AI' in players[1].name:
      response.status = "fail: cannot add a match with both players " \
                        "being Default_AI"
      return response

    match = Match(players=players, match_id=request.match_id)
    self._match_q.appendleft(match)

    logging.info('Leaving respond_add_match, len(_match_q): {}'.format(
      len(self._match_q))
    )
    return response

  def respond_get_num_finished_matches(self, request):
    logging.info('Entering respond_get_num_finished_matches')
    num_finished = 0
    pgn_fn = self._get_pgn_path(request.player_names[0],
                                request.player_names[1])
    try:
      # TODO(pengsun): a tricky impl that hacks the pgn format, improve it...
      n_lines = get_num_lines(pgn_fn)
      num_finished = int(n_lines / 10)
    except Exception as e:
      logging.info('error during processing {}, error: {}'.format(pgn_fn, e))
      logging.info('deeming n_finished = 0')

    response = MsgRespondGetNumFinishedMatches()
    response.num = num_finished
    logging.info('Leaving respond_get_num_finished_matches')
    return response

  def respond_start_match_over_worker(self, request):
    if len(self._match_q) <= 0:
      return MsgRespondStartMatchOnWorker()

    logging.info(
      'Entering respond_start_match_over_worker, len(_match_q): {}'.format(
      len(self._match_q))
    )
    match = self._match_q.pop()
    response = MsgRespondStartMatchOnWorker()
    response.match = match
    logging.info(
      "Leaving respond_start_match_over_worker, len(_match_q): {}, "
      "popped match:\n match_id: {}\n player_names {}\n" .format(
        len(self._match_q), match.match_id, [p.name for p in match.players])
    )
    return response

  def respond_send_match_result_from_worker(self, request):
    logging.info('Entering respond_send_match_result_from_worker')
    response = MsgRespondSendMatchResultFromWorker()
    if request.pgn_match.result is None:
      response.status = 'fail: pgn_match.result is None'
      return response

    self._write_match(request)

    logging.info('Leaving respond_send_match_result_from_worker')
    return response

  def _write_match(self, request):
    assert isinstance(request, MsgRequestSendMatchResultFromWorker)
    pgn_match = request.pgn_match
    s = ''
    s += '[Event "%s"]\n' % pgn_match.event
    s += '[Site "%s"]\n' % pgn_match.site
    s += '[Date "%s"]\n' % pgn_match.date
    s += '[Round "%s"]\n' % pgn_match.round
    s += '[White "%s"]\n' % pgn_match.white
    s += '[Black "%s"]\n' % pgn_match.black
    result = '1/2-1/2'
    if pgn_match.result == 1:
      result = '1-0'
    elif pgn_match.result == -1:
      result = '0-1'
    s += '[Result "%s"]\n' % result
    s += '\nInfo: %s\n\n' % request.info
    logging.info("\n" + s)

    # append to file
    pgn_fn = self._get_pgn_path(pgn_match.white, pgn_match.black)
    logging.info('append to {}'.format(pgn_fn))
    with open(pgn_fn, "at") as f:
      f.write(s)
      f.flush()

  def _get_pgn_path(self, p0_name, p1_name):
    match_key = unique_match_key(p0_name, p1_name)
    return path.join(self.output_pgn_dir, match_key + '.pgn')
