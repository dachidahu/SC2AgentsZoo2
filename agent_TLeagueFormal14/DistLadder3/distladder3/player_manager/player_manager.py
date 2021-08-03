import logging
from os import path

import zmq


# AppendPlayer
class MsgRequestAppendPlayer(object):
  def __init__(self):
    self.player = None

class MsgRespondAppendPlayer(object):
  def __init__(self):
    self.status = 'success'


# GetPlayers
class MsgRequestGetPlayers(object):
  def __init__(self):
    pass


class MsgRespondGetPlayers(object):
  def __init__(self):
    self.players = []


# Impl
class PlayerManager(object):
  """ Player Manager that maintains a list of distladder3.utils.Players.

  Each player is distladder3.utils.Player and can be
  * Checkpoint Player (each player corresponds to an NN model checkpoint)
  * Predefined Player
  It also write all players to the file working_dir/all_players.txt for
  convenient viewing.
  """

  def __init__(self, port, predef_players=(), working_dir='./'):
    self.players = list(predef_players)
    self.working_dir = working_dir
    # self._rewrite_all_players()
    self._append_write_players(self.players)

    context = zmq.Context()
    context.setsockopt(zmq.TCP_KEEPALIVE, 1)
    context.setsockopt(zmq.TCP_KEEPALIVE_CNT, 60)
    context.setsockopt(zmq.TCP_KEEPALIVE_IDLE, 60)
    context.setsockopt(zmq.TCP_KEEPALIVE_INTVL, 60)
    self._socket = context.socket(zmq.REP)
    self._socket.bind("tcp://*:{}".format(port))
    logging.info('serving at port {}'.format(port))

  def run(self):
    logging.info("Enter PlayerManager.run")
    while True:
      # message loop
      request = self._socket.recv_pyobj()
      if isinstance(request, MsgRequestAppendPlayer):
        response = self.respond_append_player(request)
      elif isinstance(request, MsgRequestGetPlayers):
        response = self.respond_get_players(request)
      else:
        raise RuntimeError("message {} not recognized".format(request))
      self._socket.send_pyobj(response)

  def respond_append_player(self, request):
    logging.info('entering respond_append_player')
    response = MsgRespondAppendPlayer()
    if request.player is None:
      response.status = 'fail, player is None'
      logging.info('leaving respond_append_player')
      return response
    self.players.append(request.player)
    # self._rewrite_all_players()
    self._append_write_players([request.player])
    logging.info('leaving respond_append_player')
    return response

  def respond_get_players(self, request):
    logging.info('entering respond_get_players')
    response = MsgRespondGetPlayers()
    response.players = self.players
    logging.info('leaving respond_get_players')
    return response

  def _rewrite_all_players(self):
    with open(path.join(self.working_dir, 'all_players.txt'), 'w') as f:
      logging.info('rewriting all players to {}'.format(f.name))
      for p in self.players:
        f.write("{},{},{}\n".format(p.name, p.agent_dir, p.agent_config))
      f.flush()

  def _append_write_players(self, players):
    with open(path.join(self.working_dir, 'all_players.txt'), 'at') as f:
      logging.info('append writing {} players to {}'.format(
        len(players), f.name))
      for p in players:
        f.write("{},{},{}\n".format(p.name, p.agent_dir, p.agent_config))
      f.flush()
