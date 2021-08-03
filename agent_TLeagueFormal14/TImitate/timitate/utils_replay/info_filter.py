"""closures for replay info filtering"""
from typing import List

from s2clientprotocol.sc2api_pb2 import ResponseReplayInfo
from s2clientprotocol.sc2api_pb2 import PlayerInfoExtra
from s2clientprotocol.common_pb2 import Zerg


# player-level filters
def player_mmr_gte(mmr_threshold=0):
  """Match Making Rating greater-than-or-equal-to"""
  def impl(p: PlayerInfoExtra):
    return p.player_mmr >= mmr_threshold

  return impl


def player_apm_gte(apm_threshold=0):
  """Action Per Minute greater-than-or-equal-to"""
  def impl(p: PlayerInfoExtra):
    return p.player_apm >= apm_threshold

  return impl


# replay-level filters
def replay_game_duration_seconds_gte(seconds_threshold=60):
  """Game Duration Seconds greater-than-or-equal-to"""
  def impl(ri: ResponseReplayInfo):
    return ri.game_duration_seconds >= seconds_threshold

  return impl


def replay_map_name(map_name='', loose_matching=True):
  """Is allowed map name"""
  def impl(ri: ResponseReplayInfo):
    if loose_matching:
      loose = lambda x: str(x).lower().strip()
      a, b = loose(map_name), loose(ri.map_name)
      return a in b or b in a
    else:
      return map_name == ri.map_name

  return impl


def replay_allowed_race_pattern(pattern='zvz'):
  """Allowed Race Pattern, e.g., zvz, zvt, pvz, ..."""
  def impl_zvz(ri: ResponseReplayInfo):
    return (ri.player_info[0].player_info.race_actual == Zerg and
            ri.player_info[1].player_info.race_actual == Zerg)

  if pattern == 'zvz':
    return impl_zvz
  else:
    raise NotImplementedError('pattern {} not yet implemented'.format(pattern))


# other general filters
def or_filters(f_list):
  """ Or operation over the filter list """
  def impl(x):
    return any([f(x) for f in f_list])

  return impl