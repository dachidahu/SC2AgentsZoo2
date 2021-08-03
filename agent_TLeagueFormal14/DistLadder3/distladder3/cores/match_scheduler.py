import logging
import os
from os import path
import uuid
from time import sleep

import zmq

from distladder3.cores.match_server import MsgRequestAddMatch
from distladder3.cores.match_server import MsgRespondAddMatch
from distladder3.cores.match_server import MsgRequestGetNumFinishedMatches
from distladder3.cores.match_server import MsgRespondGetNumFinishedMatches


# AddMatchSeries
class MsgRequestAddMatchSeries(object):
  def __init__(self):
    self.players = []  # distladder3.utils.Player
    self.match_type = ''  #  {'round-robin' | 'one-vs-rest'}
    self.cycle = 0
    self.allow_redundant_matches = True


class MsgRespondAddMatchSeries(object):
  def __init__(self):
    self.status = 'success'


class MatchScheduler(object):
  """ MatchScheduler. Receives message to schedule matches. """

  def __init__(self, port, match_server_ep):
    context = zmq.Context()
    context.setsockopt(zmq.TCP_KEEPALIVE, 1)
    context.setsockopt(zmq.TCP_KEEPALIVE_CNT, 60)
    context.setsockopt(zmq.TCP_KEEPALIVE_IDLE, 60)
    context.setsockopt(zmq.TCP_KEEPALIVE_INTVL, 60)
    self._socket = context.socket(zmq.REP)
    self._socket.bind("tcp://*:{}".format(port))
    logging.info('use port {}'.format(port))

    context = zmq.Context()
    context.setsockopt(zmq.TCP_KEEPALIVE, 1)
    context.setsockopt(zmq.TCP_KEEPALIVE_CNT, 60)
    context.setsockopt(zmq.TCP_KEEPALIVE_IDLE, 60)
    context.setsockopt(zmq.TCP_KEEPALIVE_INTVL, 60)
    self._match_socket = context.socket(zmq.REQ)
    self._match_socket.connect("tcp://{}".format(match_server_ep))
    # self._match_socket.setsockopt(zmq.SNDHWM, 4)
    # self._match_socket.setsockopt(zmq.RCVHWM, 4)
    logging.info('connecting to match server {}'.format(match_server_ep))

  def run(self):
    logging.info("Enter MatchScheduler.run()")
    while True:
      # message loop
      request = self._socket.recv_pyobj()
      if isinstance(request, MsgRequestAddMatchSeries):
        response = self.respond_add_match_series(request)
      else:
        raise RuntimeError("message {} not recognized".format(request))
      self._socket.send_pyobj(response)

  def respond_add_match_series(self, request):
    logging.info('enter respond_add_match_series')

    # IMPORTANT: view the tail player as the primary player
    pairs, counts = _match_type_to_pairs_counts(
      request.match_type, request.players, request.cycle)
    self._send_match_series(pairs, counts, request.players,
                            request.allow_redundant_matches)

    logging.info('leave respond_add_match_series')
    return MsgRespondAddMatchSeries()

  def _send_match_series(self, pairs, counts, players, allow_redundant_matches):
    logging.info(
      "Enter _send_match_series: "
      "n_pairs: {}, n_counts: {}".format(len(pairs), len(counts)
    ))
    n_success_add = 0
    for (i_player0, i_player1), n_matches in zip(pairs, counts):
      logging.info('allow_redundant_matches: {}'.format(
        allow_redundant_matches))
      if not allow_redundant_matches:
        # re-calculate n_matches: rule out the finished matches
        req = MsgRequestGetNumFinishedMatches()
        req.player_names = [players[i_player0].name, players[i_player1].name]
        self._match_socket.send_pyobj(req)
        rep = self._match_socket.recv_pyobj()
        assert isinstance(rep, MsgRespondGetNumFinishedMatches)
        n_finished = rep.num
        n_matches = max(0, n_matches - n_finished)
        logging.info('n_finished: {}, new n_matches: {}'.format(
          n_finished, n_matches))
      for i in range(n_matches):
        # sleep(0.000001)
        # send msg
        request = MsgRequestAddMatch()
        request.match_id = str(uuid.uuid4())
        request.players = [players[i_player0], players[i_player1]]
        self._match_socket.send_pyobj(request)
        # recv msg
        response = self._match_socket.recv_pyobj()
        assert isinstance(response, MsgRespondAddMatch)
        if response.status == 'success':
          n_success_add += 1
    logging.info("Leave _send_match_series, successfully add {} "
                 "matches".format(n_success_add))
    pass


def _match_type_to_pairs_counts(match_type, players, cycle):
  """ Note: the tail player players[-1] is the primary player"""
  if match_type.lower() == 'round-robin':
    return _round_robin(players, cycle)
  if match_type.lower() == 'one-vs-rest':
    return _one_vs_rest(players[-1], players[0:-1], cycle)
  if match_type.lower() == 'pairwise':  # alias
    return _one_vs_rest(players[-1], players[0:-1], cycle)
  if match_type.lower() == 'self-play':
    return _self_play(players, cycle)
  raise ValueError('Unknown match type {}'.format(match_type))


def _round_robin(players, cycle):
  n_players = len(players)
  assert n_players >= 2
  pairs = []
  for i in range(n_players - 1):
    for j in range(i + 1, n_players):
      # two Default_AI cannot match
      if ('Default_AI' not in players[i].name or
          'Default_AI' not in players[j].name):
        pairs.append([i, j])
  counts = [cycle] * len(pairs)
  return pairs, counts


def _one_vs_rest(player, oppo_players, cycle):
  n_oppo = len(oppo_players)
  players = list(oppo_players)
  players.append(player)
  pairs = []
  for i in range(n_oppo):
    if ('Default_AI' not in players[n_oppo].name or
        'Default_AI' not in players[i].name):
      pairs.append([n_oppo, i])
  counts = [cycle] * n_oppo
  return pairs, counts


def _self_play(players, cycle):
  pairs = [(i, i) for i in range(len(players))]
  counts = [cycle] * len(pairs)
  return pairs, counts