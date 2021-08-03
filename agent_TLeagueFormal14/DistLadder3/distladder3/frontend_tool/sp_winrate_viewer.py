""" Self-Play (SP) win-rate viewer. """
import logging
from os import path
from time import sleep

import zmq
import numpy as np
import matplotlib.pyplot as plt

from distladder3.player_manager.player_manager import MsgRequestGetPlayers
from distladder3.player_manager.player_manager import MsgRespondGetPlayers
from distladder3.cores.match_scheduler import MsgRequestAddMatchSeries
from distladder3.cores.match_scheduler import MsgRespondAddMatchSeries
from distladder3.results_tool.results_collector import MsgRequestGetScores
from distladder3.results_tool.results_collector import MsgRespondGetScores
from distladder3.utils import unique_match_key


class SpecListSPWinrateViewer(object):
  """Self-Play Winrate Viewer for the specified players.

  For players [p1, p2, ..., pn], it schedules matchess for p1 vs p1, p2 vs p2,
  ... pn vs pn. Currently, it does NOT record any match winrates. You may use it
   to make self-play matches and view the logs for your interested information.
  TODO(pengsun): common base class with other (e.g., rr) winrate viewer
  """
  def __init__(self, player_manager_endpoint, match_scheduler_endpoint,
               results_collector_endpoint, player_names, cycle,
               output_dir):
    self.player_names = player_names
    self.cycle = cycle
    self.output_dir = output_dir

    context = zmq.Context()
    context.setsockopt(zmq.TCP_KEEPALIVE, 1)
    context.setsockopt(zmq.TCP_KEEPALIVE_CNT, 60)
    context.setsockopt(zmq.TCP_KEEPALIVE_IDLE, 60)
    context.setsockopt(zmq.TCP_KEEPALIVE_INTVL, 60)
    self._pm_socket = context.socket(zmq.REQ)
    self._pm_socket.connect("tcp://{}".format(player_manager_endpoint))
    self._pm_socket.setsockopt(zmq.SNDHWM, 4)
    self._pm_socket.setsockopt(zmq.RCVHWM, 4)
    logging.info('connecting to player manager {}'.format(
      player_manager_endpoint))

    context = zmq.Context()
    context.setsockopt(zmq.TCP_KEEPALIVE, 1)
    context.setsockopt(zmq.TCP_KEEPALIVE_CNT, 60)
    context.setsockopt(zmq.TCP_KEEPALIVE_IDLE, 60)
    context.setsockopt(zmq.TCP_KEEPALIVE_INTVL, 60)
    self._ms_socket = context.socket(zmq.REQ)
    self._ms_socket.connect("tcp://{}".format(match_scheduler_endpoint))
    self._ms_socket.setsockopt(zmq.SNDHWM, 4)
    self._ms_socket.setsockopt(zmq.RCVHWM, 4)
    logging.info('connecting to match scheduler {}'.format(
      match_scheduler_endpoint))

    context = zmq.Context()
    context.setsockopt(zmq.TCP_KEEPALIVE, 1)
    context.setsockopt(zmq.TCP_KEEPALIVE_CNT, 60)
    context.setsockopt(zmq.TCP_KEEPALIVE_IDLE, 60)
    context.setsockopt(zmq.TCP_KEEPALIVE_INTVL, 60)
    self._rc_socket = context.socket(zmq.REQ)
    self._rc_socket.connect("tcp://{}".format(results_collector_endpoint))
    self._rc_socket.setsockopt(zmq.SNDHWM, 4)
    self._rc_socket.setsockopt(zmq.RCVHWM, 4)
    logging.info('connecting to results collector {}'.format(
      results_collector_endpoint))

  def run(self):
    logging.info('enter SPWinrateViewer.run')

    all_players = self._get_all_players()
    all_player_names = [p.name for p in all_players]

    players = [all_players[all_player_names.index(pn)]
               for pn in self.player_names]
    if not players:
      logging.info('empty players, exit')
      return
    self._send_match_series(players)

    # loop: write winrate matrix by querying results_collector_endpoint
    while True:
      raw_vec = self._get_raw_winrate_vec()

      # write player names
      with open(path.join(self.output_dir, 'player_names.txt'), 'wt') as f:
        for p in self.player_names:
          f.write(p + ' ')
        f.flush()

      # write the winrate vector. TODO(pengsun): the impl

      tsleep = 17
      logging.info('sleep {} secs until next scanning...'.format(tsleep))
      sleep(tsleep)

  def _get_all_players(self):
    """ get all players by querying player_manager_endpoint """
    self._pm_socket.send_pyobj(MsgRequestGetPlayers())
    rep = self._pm_socket.recv_pyobj()
    assert isinstance(rep, MsgRespondGetPlayers)
    all_players = rep.players
    logging.info('get {} players:'.format(len(all_players)))
    for p in all_players:
      logging.info('{},{},{}'.format(p.name, p.agent_dir, p.agent_config))
    return all_players

  def _send_match_series(self, players):
    """ send matches to match_scheduler_endpoint (avoid redundant matches) """
    req = MsgRequestAddMatchSeries()
    req.players = players
    req.match_type = 'self-play'
    req.cycle = self.cycle
    req.allow_redundant_matches = False
    self._ms_socket.send_pyobj(req)
    rep = self._ms_socket.recv_pyobj()
    assert isinstance(rep, MsgRespondAddMatchSeries)
    logging.info('add match series for the players:')
    for p in players:
      logging.info('{}'.format(p.name))
    logging.info('add match status: {}'.format(rep.status))

  def _get_raw_winrate_vec(self):
    # TODO(pengsun): the impl
    return None