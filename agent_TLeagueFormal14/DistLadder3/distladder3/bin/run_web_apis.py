""" run web service

Example:
"""
import os
import argparse
import logging

import zmq
from flask import Flask
from flask_restful import Api
from flask_restful import Resource
from flask_restful import reqparse

from distladder3.player_manager.player_manager import MsgRequestGetPlayers
from distladder3.player_manager.player_manager import MsgRespondGetPlayers
from distladder3.cores.match_scheduler import MsgRequestAddMatchSeries
from distladder3.cores.match_scheduler import MsgRespondAddMatchSeries
from distladder3.cores.match_server import MsgRequestGetNumFinishedMatches
from distladder3.cores.match_server import MsgRespondGetNumFinishedMatches
from distladder3.results_tool.results_collector import MsgRequestGetScores
from distladder3.results_tool.results_collector import MsgRespondGetScores
from distladder3.utils import unique_match_key


parser = argparse.ArgumentParser()
parser.add_argument("--player_manager_endpoint", type=str,
                    default="localhost:5526",
                    help="player_manager_endpoint")
parser.add_argument("--match_scheduler_endpoint", type=str,
                    default="localhost:6688",
                    help="match_scheduler_endpoint")
parser.add_argument("--match_server_endpoint", type=str,
                    default='localhost:6788',
                    help="match server Endpoint")
parser.add_argument("--results_collector_endpoint", type=str,
                    default="localhost:6888",
                    help="results_collector_endpoint")
parser.add_argument("--port", type=int, default=8828, help="web api port")
args = parser.parse_args()


app = Flask(__name__)
apis = Api(app)

# internal socket
context = zmq.Context()
context.setsockopt(zmq.TCP_KEEPALIVE, 1)
context.setsockopt(zmq.TCP_KEEPALIVE_CNT, 60)
context.setsockopt(zmq.TCP_KEEPALIVE_IDLE, 60)
context.setsockopt(zmq.TCP_KEEPALIVE_INTVL, 60)
_pm_socket = context.socket(zmq.REQ)
_pm_socket.connect("tcp://{}".format(args.player_manager_endpoint))
_pm_socket.setsockopt(zmq.SNDHWM, 4)
_pm_socket.setsockopt(zmq.RCVHWM, 4)
logging.info('connecting to player manager {}'.format(
  args.player_manager_endpoint))

context = zmq.Context()
context.setsockopt(zmq.TCP_KEEPALIVE, 1)
context.setsockopt(zmq.TCP_KEEPALIVE_CNT, 60)
context.setsockopt(zmq.TCP_KEEPALIVE_IDLE, 60)
context.setsockopt(zmq.TCP_KEEPALIVE_INTVL, 60)
_msche_socket = context.socket(zmq.REQ)
_msche_socket.connect("tcp://{}".format(args.match_scheduler_endpoint))
_msche_socket.setsockopt(zmq.SNDHWM, 4)
_msche_socket.setsockopt(zmq.RCVHWM, 4)
logging.info('connecting to match scheduler {}'.format(
  args.match_scheduler_endpoint))

context = zmq.Context()
context.setsockopt(zmq.TCP_KEEPALIVE, 1)
context.setsockopt(zmq.TCP_KEEPALIVE_CNT, 60)
context.setsockopt(zmq.TCP_KEEPALIVE_IDLE, 60)
context.setsockopt(zmq.TCP_KEEPALIVE_INTVL, 60)
_mser_socket = context.socket(zmq.REQ)
_mser_socket.connect("tcp://{}".format(args.match_server_endpoint))
_mser_socket.setsockopt(zmq.SNDHWM, 4)
_mser_socket.setsockopt(zmq.RCVHWM, 4)
logging.info('connecting to match server {}'.format(
  args.match_server_endpoint))

context = zmq.Context()
context.setsockopt(zmq.TCP_KEEPALIVE, 1)
context.setsockopt(zmq.TCP_KEEPALIVE_CNT, 60)
context.setsockopt(zmq.TCP_KEEPALIVE_IDLE, 60)
context.setsockopt(zmq.TCP_KEEPALIVE_INTVL, 60)
_rc_socket = context.socket(zmq.REQ)
_rc_socket.connect("tcp://{}".format(args.results_collector_endpoint))
_rc_socket.setsockopt(zmq.SNDHWM, 4)
_rc_socket.setsockopt(zmq.RCVHWM, 4)
logging.info('connecting to results collector {}'.format(
  args.results_collector_endpoint))

# internal funcs
def _get_all_players():
  """ request Player Manager for all players  """
  _pm_socket.send_pyobj(MsgRequestGetPlayers())
  rep = _pm_socket.recv_pyobj()
  assert isinstance(rep, MsgRespondGetPlayers)
  all_players = rep.players
  logging.info('get {} players:'.format(len(all_players)))
  for p in all_players:
    logging.info('{},{},{}'.format(p.name, p.agent_dir, p.agent_config))
  return all_players


def _get_n_matches_finished(player_name0, player_name1):
  """ request Match Server for finished matches """
  req = MsgRequestGetNumFinishedMatches()
  req.player_names = [player_name0, player_name1]
  _mser_socket.send_pyobj(req)
  rep = _mser_socket.recv_pyobj()
  assert isinstance(rep, MsgRespondGetNumFinishedMatches)
  return rep.num


def _get_score(player_name0, player_name1):
  req = MsgRequestGetScores()
  req.ratings_filename_patterns = [unique_match_key(player_name0, player_name1)]
  _rc_socket.send_pyobj(req)
  rep = _rc_socket.recv_pyobj()
  assert isinstance(rep, MsgRespondGetScores)
  dict_s = rep.scores[0]
  assert player_name0 in dict_s and player_name1 in dict_s
  return dict_s


# APIs exposed
# ------------
class PlayerNames(Resource):
  """ Player Names Resource.

  The format of each player name:
  case1: parent-id:current-id_yyyymmddHHMMSS
  e.g., init_model:0003_20190803142145, 0003:0012_20190804093422,...

  case2: IL-model_yyyymmddHHMMSS
  e.g., IL-model_20181007142325

  case3: just plain names consisting of characters and numbers
  e.g., Default_AI_6, AgentJones, 0925-R1, ....
  """
  def get(self):
    """ get the list of all player names """
    all_players = _get_all_players()
    return [p.name for p in all_players]


class MatchManager(Resource):
  """ Match Manager Resource """
  def __init__(self):
    self.p = reqparse.RequestParser()
    self.p.add_argument('player_name0', type=str, help='the first player name')
    self.p.add_argument('player_name1', type=str, help='the second player name')
    self.p.add_argument('n_matches_scheduled', type=int,
                        help='number of matches to be scheduled')

  def put(self):
    """ schedule additional n_matches_scheduled over the pair
    player_name0, player_name1.
    NOTE: the same with the pair player_name1, player_name0.
    It's symmetrical match. """
    # parse args
    mm_args = self.p.parse_args()
    player_name0 = mm_args['player_name0']
    player_name1 = mm_args['player_name1']
    n_matched_scheduled = mm_args['n_matches_scheduled']
    # request Match Scheduler to start matches
    all_players = _get_all_players()
    all_player_names = [p.name for p in all_players]
    req = MsgRequestAddMatchSeries()
    req.players = [all_players[all_player_names.index(player_name0)],
                   all_players[all_player_names.index(player_name1)]]
    req.match_type = 'one-vs-rest'
    req.cycle = n_matched_scheduled
    req.allow_redundant_matches = False
    _msche_socket.send_pyobj(req)
    rep = _msche_socket.recv_pyobj()
    # check return value
    assert isinstance(rep, MsgRespondAddMatchSeries)
    n_successful_matches_scheduled = (n_matched_scheduled if
      rep.status == 'success' else 0)
    return {
      'player_name0': player_name0,
      'player_name1': player_name1,
      'n_successful_matches_scheduled': n_successful_matches_scheduled,
    }

  def get(self):
    """ get match pair results """
    mm_args = self.p.parse_args()
    player_name0 = mm_args['player_name0']
    player_name1 = mm_args['player_name1']
    # all players
    n_matches_finished = _get_n_matches_finished(player_name0, player_name1)
    # scores
    score = _get_score(player_name0, player_name1)
    return {
      'player_name0': player_name0,
      'player_name1': player_name1,
      'n_matches_finished': n_matches_finished,
      'player0_winrate': score[player_name0],
      'player1_winrate': score[player_name1]
    }


API_PREFIX = '/api/v1'
apis.add_resource(PlayerNames, API_PREFIX + '/player-names')
apis.add_resource(MatchManager, API_PREFIX + '/match-manager')


if __name__ == "__main__":
  app.run(debug=False, port=args.port, host='0.0.0.0')
