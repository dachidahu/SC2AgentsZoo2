""" run web service

Example:
"""
import os
import argparse

from flask import Flask
from flask_autoindex import AutoIndex
from flask_restful import Api
from flask_restful import Resource
from flask_restful import reqparse


parser = argparse.ArgumentParser()
parser.add_argument("--watched_dir", type=str,
                    default="/root/eval_results/evYYMMDD",
                    help="watched working dir.")
parser.add_argument("--port", type=int, default=8888, help="web service port")
args = parser.parse_args()


app = Flask(__name__)
apis = Api(app)
idx = AutoIndex(app, browse_root=args.watched_dir, add_url_rules=False)


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
    # TODO(pengsun): impl
    return [
      'Default_AI_6',
      'IL-model_20190304175321',
      'init_model:0004_20190812135521',
      'init_model:0002_20190812135511',
      '0004:0012_20190813213408',
      '0002:0010_20190813220825',
      '0012:0018_20190814155534',
      '0012:0018_20190814165218'
    ]


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
    # TODO(pengsun): impl
    mm_args = self.p.parse_args()
    player_name0 = mm_args['player_name0']
    player_name1 = mm_args['player_name1']
    n_matched_scheduled = mm_args['n_matches_scheduled']
    return {
      'player_name0': player_name0,
      'player_name1': player_name1,
      'n_successful_matches_scheduled': n_matched_scheduled
    }

  def get(self):
    # TODO(pengsun): impl
    mm_args = self.p.parse_args()
    player_name0 = mm_args['player_name0']
    player_name1 = mm_args['player_name1']
    return {
      'player_name0': player_name0,
      'player_name1': player_name1,
      'n_matches_finished': 42,
      'player0_winrate': 0.9,
      'player1_winrate': 0.1
    }


API_PREFIX = '/api/v1'
apis.add_resource(PlayerNames, API_PREFIX + '/player-names')
apis.add_resource(MatchManager, API_PREFIX + '/match-manager')


# auto-index: view the raw dir
# ----------------------------
@app.route('/')
@app.route('/<path:path>')
def autoindex(path='.'):
  recognized_suffix = ['.pgn', '.elo.ratings', '.ratings', '.ini', '.log',
                       '.err', '.txt', '.list']
  mimetype = ('text/plain' if any([path.endswith(s) for s in recognized_suffix])
              else None)
  return idx.render_autoindex(path, sort_by='name', order=1, mimetype=mimetype)


if __name__ == "__main__":
  app.run(debug=False, port=args.port, host='0.0.0.0')
