""" One-Vs-Rest (OVR) win-rate viewer. """
import logging
from os import path
from time import sleep
from datetime import datetime
from collections import OrderedDict

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
from distladder3.utils import find_first_matched_pattern
from distladder3.utils import find_all_matched_pattern
from distladder3.utils import split_model_filename
from distladder3.utils import get_parent_me


class BaseOVRWinrateViewer(object):
  """ Base One-vs-Rest Winrate Viewer, Abstract Class

  Presume the player name in the format "parent:me_timestamp", e.g.,
  "0002:0008_091213", "0003:0012_091314",...
  Given a list of primary player names, start matches for each one playing
  against each opponent player.
  """
  def __init__(self, player_manager_endpoint, match_scheduler_endpoint,
               results_collector_endpoint, oppo_player_names, cycle,
               output_dir):
    self.oppo_player_names = oppo_player_names
    self.cycle = cycle
    self.output_dir = output_dir
    self._tsleep = None

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
    logging.info('enter BaseOVRWinrateViewer.run')

    all_players = self._get_all_players()
    all_player_names = [p.name for p in all_players]
    # extract the opponent players
    oppo_players = [all_players[all_player_names.index(oppo_name)]
                    for oppo_name in self.oppo_player_names]

    primary_player_names = self._get_primary_player_names(all_player_names)

    self._send_match_series(primary_player_names,
                            all_player_names,
                            all_players,
                            oppo_players)

    # loop: plot/write winrates by querying results_collector_endpoint
    while True:
      winrates = {}
      for oname in self.oppo_player_names:
        curve = self._get_winrate_curve(primary_player_names, oname)
        # curve name
        winrates['vs_{}'.format(oname)] = curve
      self._write_winrates(winrates)
      self._plot_winrates(winrates)

      tsleep = self._tsleep or 17
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

  def _get_primary_player_names(self, all_player_names):
    """ impl in derived class for various logic that create primary player
    names. """
    raise NotImplementedError

  def _send_match_series(self, primary_player_names, all_player_names,
                         all_players, oppo_players):
    """ send matches to match_scheduler_endpoint (avoid redundant matches) """
    for cur_pname in primary_player_names:
      cur_pplayer = all_players[all_player_names.index(cur_pname)]
      req = MsgRequestAddMatchSeries()
      req.players = oppo_players + [cur_pplayer]
      req.match_type = 'one-vs-rest'
      req.cycle = self.cycle
      req.allow_redundant_matches = False
      self._ms_socket.send_pyobj(req)
      rep = self._ms_socket.recv_pyobj()
      assert isinstance(rep, MsgRespondAddMatchSeries)
      logging.info('add match series for {}, status: {}'.format(
        cur_pname, rep.status))

  def _get_winrate_curve(self, primary_player_names, oppo_player_name):
    """ 'x' data the player model names, 'y' data the scores """
    req = MsgRequestGetScores()
    req.ratings_filename_patterns = [unique_match_key(pname, oppo_player_name)
                                     for pname in primary_player_names]
    self._rc_socket.send_pyobj(req)
    rep = self._rc_socket.recv_pyobj()
    assert isinstance(rep, MsgRespondGetScores)
    return {
      'x': primary_player_names,
      'y': [s[pname] if pname in s else np.nan
            for pname, s in zip(primary_player_names, rep.scores)]
    }

  def _write_winrates(self, winrates):
    def _write_list(fhandle, lst):
      fhandle.write(' '.join([str(each) for each in lst]) + "\n")

    for cname, cdata in winrates.items():
      with open(path.join(self.output_dir, cname + '.txt'), 'wt') as f:
        _write_list(f, cdata['x'])
        _write_list(f, cdata['y'])
        f.flush()
        logging.info('written winrate curve to {}'.format(f.name))

  def _plot_winrates(self, winrates):
    fig = plt.figure()
    p_handles = []
    # draw each curve
    for name, data in winrates.items():
      y = data['y']
      x = [i + 1 for i in range(len(y))]  # one-based indexing
      handle, = plt.plot(x, y, marker='o', figure=fig)
      p_handles.append(handle)
    # draw a unified xticks
    tick_names =   winrates[list(winrates.keys())[0]]['x']  # the first one suffices
    #plt.xticks([i + 1 for i in range(len(tick_names))],
    #           [tn for tn in tick_names], rotation=20)
    plt.xticks([i + 1 for i in range(len(tick_names))],
               [tn for tn in tick_names])
    # draw the legend
    plt.legend(p_handles, [name for name in winrates],
               bbox_to_anchor=(1.0, 0.75))
    # other trimming
    plt.xlabel('#checkpoints')
    plt.ylabel('win-rate')
    plt.grid(True, 'major')
    # saving to html
    fig.autofmt_xdate(rotation=-30, ha='left')
    plt.tight_layout()
    plt.savefig(path.join(self.output_dir, 'winrate_plot.png'))
    html = '<img src=\'winrate_plot.png\'>'
    output_path = path.join(self.output_dir, 'winrate_plot.html')
    with open(output_path, 'w') as f:
      f.write(html)
    logging.info('saving winrate_plot html to {}'.format(output_path))
    return fig


class BaseWatchingOVRWinrateViewer(BaseOVRWinrateViewer):
  """ Base Watching One-vs-Rest Winrate Viewer .

  It over-watches a directory, finding players and plotting curves on and on.
  """
  def __init__(self, player_manager_endpoint, match_scheduler_endpoint,
               results_collector_endpoint, oppo_player_names, cycle,
               output_dir):
    super(BaseWatchingOVRWinrateViewer, self).__init__(
      player_manager_endpoint, match_scheduler_endpoint,
      results_collector_endpoint, oppo_player_names, cycle, output_dir
    )

  def run(self):
    logging.info('enter BaseWatchingOVRWinrateViewer.run')

    all_players = self._get_all_players()
    all_player_names = [p.name for p in all_players]
    # extract the opponent players
    oppo_players = [all_players[all_player_names.index(oppo_name)]
                    for oppo_name in self.oppo_player_names]
    sorted_primary_player_names = []

    # loop: plot/write winrates by querying results_collector_endpoint
    while True:
      # re-scanning all players and trying to find new
      all_players = self._get_all_players()
      all_player_names = [p.name for p in all_players]
      cur_primary_player_names = self._get_primary_player_names(
        all_player_names)
      new_primary_player_names = list(set(cur_primary_player_names) -
                                      set(sorted_primary_player_names))
      sorted_primary_player_names += _sort_player_names(
        new_primary_player_names)

      if new_primary_player_names:
        logging.info('found new primary players:')
        for pn in new_primary_player_names:
          logging.info('  ' + pn)
        self._send_match_series(new_primary_player_names,
                                all_player_names,
                                all_players,
                                oppo_players)
      else:
        logging.info('not found any new primary player...')

      winrates = {}
      for oname in self.oppo_player_names:
        curve = self._get_winrate_curve(sorted_primary_player_names, oname)
        # curve name
        winrates['vs_{}'.format(oname)] = curve
      self._write_winrates(winrates)
      self._plot_winrates(winrates)

      tsleep = self._tsleep or 61
      logging.info('sleep {} secs until next scanning...'.format(tsleep))
      sleep(tsleep)

  def _get_primary_player_names(self, all_player_names):
    raise NotImplementedError


class SpecListOVRWinrateViewer(BaseOVRWinrateViewer):
  """ Specified List One-vs-Rest Winrate Viewer.

  Presume the player name in the format "parent:me_timestamp", e.g.,
  "0002:0008_091213", "0003:0012_091314",...
  Given a player name patterns list, start matches for each one playing against
   each opponent player.
  """

  def __init__(self, player_manager_endpoint, match_scheduler_endpoint,
               results_collector_endpoint, primary_player_name_patterns,
               oppo_player_names, cycle, output_dir):
    super(SpecListOVRWinrateViewer, self).__init__(
      player_manager_endpoint, match_scheduler_endpoint,
      results_collector_endpoint, oppo_player_names, cycle, output_dir
    )
    self.primary_player_name_patterns = primary_player_name_patterns

  def _get_primary_player_names(self, all_player_names):
    """ get model keys as primary player names """
    pp_names = []
    for ptn in self.primary_player_name_patterns:
      m = find_first_matched_pattern(ptn, all_player_names)
      if m is not None:
        pp_names.append(m)
    return pp_names


class BackwardBranchOVRWinrateViewer(BaseOVRWinrateViewer):
  """ Backward Branch One-vs-Rest Winrate Viewer.

  Presume the player name in the format "parent:me_timestamp", e.g.,
  "0002:0008_091213", "0003:0012_091314",...
  Given a player name pattern as the leaf node,
  it traverse to the root player name and view the winrates over the branch.
  """

  def __init__(self, player_manager_endpoint, match_scheduler_endpoint,
               results_collector_endpoint, primary_player_name_pattern,
               oppo_player_names, cycle, timestamp_criterion, output_dir):
    super(BackwardBranchOVRWinrateViewer, self).__init__(
      player_manager_endpoint, match_scheduler_endpoint,
      results_collector_endpoint, oppo_player_names, cycle, output_dir
    )
    self.timestamp_criterion = timestamp_criterion
    self.primary_player_name_pattern = primary_player_name_pattern

  def _get_primary_player_names(self, all_player_names):
    """ traverse the tree branch backwards & get model keys as primary
    player names """
    branch = _find_backward_branch(all_player_names,
                                   self.primary_player_name_pattern)
    _sort_branch_timstamps(branch)
    logging.info('found branch {}:'.format(branch))
    # trimmed branch with sorted and non-overlapped timestamps
    model_keys, timestamps = _trim_sorted_branch_by_timestamps(
      branch, self.primary_player_name_pattern
    )
    logging.info('trimmed and sorted model keys and timestamps:')
    for m, t in zip(model_keys, timestamps):
      logging.info("{} {}".format(m, t))

    # prune further when necessary
    if self.timestamp_criterion == 'latest':
      model_keys, timestamps = _pick_latest_timestamps(model_keys, timestamps)
      logging.info('after picking latest model keys and timestamps:')
      for m, t in zip(model_keys, timestamps):
        logging.info('{} {}'.format(m, t))
    return ['{}_{}'.format(m, t) for m, t in zip(model_keys, timestamps)]


def _find_backward_branch(player_names, player_name_pattern):
  """ return, e.g.,
  {'0001:0002': ['082311', '082312', '082413'],
   '0002:0005': ['082411', '082412']}  """
  branch = {}
  pattern = player_name_pattern
  while True:
    fns = find_all_matched_pattern(pattern, player_names)
    k, timestamps = _extract_key_timestamps(fns)
    if not k and not timestamps:
      # reached root, break
      break
    # updating
    branch[k] = timestamps
    # and move on to its parent node
    parent, dummy_current = get_parent_me(k)
    pattern = ':' + parent

  return branch


def _find_forward_branch(player_names, player_name_pattern):
  """ return, e.g.,
  {'0001:0002': ['082311', '082312', '082413'],
   '0002:0005': ['082411', '082412']}  """
  branch = OrderedDict()
  pattern = player_name_pattern[0]
  count = 0
  while True:
    # pass one: over all player names
    fns = find_all_matched_pattern(pattern, player_names)
    if not fns:
      # reached a leaf
      break

    # pass two: pick only one branch in case of multiple branches
    if count < len(player_name_pattern):
      # pick the corresponding one from the player_name_pattern
      branch_key_pattern = player_name_pattern[count]
    else:
      # simply pick the first branch
      branch_key_pattern, _dummy_timestamp = split_model_filename(fns[0])
    fns = find_all_matched_pattern(branch_key_pattern, fns)

    # now safe to extract the key (model key) and value (timestamps)
    k, timestamps = _extract_key_timestamps(fns)
    if not k and not timestamps:
      # reached a leaf
      break

    # updating
    branch[k] = timestamps
    count += 1
    # and move on to its child node
    dummy_current, child = get_parent_me(k)
    pattern = child + ':'


  return branch


def _extract_key_timestamps(model_filenames):
  k = None
  timestamps = []
  for mf in model_filenames:
    key, timestamp = split_model_filename(mf)
    if k is None:
      k = key
    else:
      assert k == key
    timestamps.append(timestamp)
  return k, timestamps


def _sort_branch_timstamps(branch):
  for k in branch:
    branch[k].sort()


def _sort_player_names(player_names):
  return sorted(player_names, key=lambda p: split_model_filename(p)[1])


def _trim_sorted_branch_by_timestamps(branch, leaf_model_key):
  """
  model_keys = ['0001:0002', '0001:0002', '0002:0005', '0002:0005', ]
  timestamps = ['082311', '082312', '082411', '082412']
  """
  def _find_first_matched_node(_branch, _pattern):
    for node in _branch:
      if _pattern in node:
        return node
    return None

  model_keys, timestamps = [], []
  pattern = leaf_model_key
  if pattern in branch:
    cur_max_timestamp = branch[leaf_model_key][-1]
    # recurse the tree backward to the root
    while True:
      cur_model_key = _find_first_matched_node(branch, pattern)
      # has reached root node?
      if cur_model_key is None:
        break

      # get the timestamps <= current_max_timestamp
      for t in reversed(branch[cur_model_key]):
        if t <= cur_max_timestamp:
          # update
          model_keys = [cur_model_key] + model_keys
          timestamps = [t] + timestamps
          cur_max_timestamp = t
      # update the pattern
      pattern = ':' + get_parent_me(cur_model_key)[0]

  return model_keys, timestamps


def _pick_latest_timestamps(model_keys, timestamps):
  new_m, new_t = [], []
  for m, t in zip(model_keys, timestamps):
    if len(new_m) == 0:
      new_m.append(m)
      new_t.append(t)
      continue
    if new_m[-1] != m:
      new_m.append(m)
      new_t.append(t)
      continue
    if t > new_t[-1]: # always keep the newer timestamp
      new_t[-1] = t
  return new_m, new_t


class ForwardSearchOVRWinrateViewer(BaseWatchingOVRWinrateViewer):
  """ Forward-Search One-vs-Rest Winrate Viewer .

  It forward-search the models based on name pattern and timestamps.
  """
  def __init__(self, player_manager_endpoint, match_scheduler_endpoint,
               results_collector_endpoint, oppo_player_names, cycle,
               primary_player_name_pattern, start_timestamp, freq_secs,
               output_dir, tsleep=61):
    super(ForwardSearchOVRWinrateViewer, self).__init__(
      player_manager_endpoint, match_scheduler_endpoint,
      results_collector_endpoint, oppo_player_names, cycle, output_dir
    )
    self.primary_player_name_pattern = primary_player_name_pattern
    self.start_timestamp = start_timestamp
    self.freq_secs = freq_secs
    self._tsleep = tsleep

  def _get_primary_player_names(self, all_player_names):
    sorted_all_player_names = _sort_player_names(all_player_names)
    spnames = []
    for p in sorted_all_player_names:
      if self.primary_player_name_pattern not in p:
        continue
      _, timestamp = split_model_filename(p)
      if timestamp >= self.start_timestamp:
        # when empty, let's push the first one
        if not spnames:
          spnames.append(p)
          continue
        # if timestamp frequency satisfied?
        _, prev_timestamp = split_model_filename(spnames[-1])
        t2 = datetime.strptime(timestamp, '%Y%m%d%H%M%S')
        t1 = datetime.strptime(prev_timestamp, '%Y%m%d%H%M%S')
        if (t2 - t1).total_seconds() >= self.freq_secs:
          spnames.append(p)
    return spnames


class ForwardBranchOVRWinrateViewer(BaseWatchingOVRWinrateViewer):
  """ Forward Branch One-vs-Rest Winrate Viewer.

  Presume the player name in the format "parent:me_timestamp", e.g.,
  "0002:0008_091213", "0003:0012_091314",...
  Given a player name patterns as a branch starting from the root,
  it traverse to the leaf player name. When there are multiple branches, it
  picks a random one. It then views the winrates over the branch.
  """

  def __init__(self, player_manager_endpoint, match_scheduler_endpoint,
               results_collector_endpoint, primary_player_name_patterns,
               oppo_player_names, cycle, timestamp_criterion, output_dir,
               freq_secs=-1, tsleep=88):
    super(ForwardBranchOVRWinrateViewer, self).__init__(
      player_manager_endpoint, match_scheduler_endpoint,
      results_collector_endpoint, oppo_player_names, cycle, output_dir
    )
    self.timestamp_criterion = timestamp_criterion
    self.primary_player_name_patterns = primary_player_name_patterns
    self._tsleep = tsleep  # needs a longer sleeping time
    # frequency in seconds, minimal seconds between two checked models
    self._freq_secs = freq_secs

  def _get_primary_player_names(self, all_player_names):
    """ traverse the tree branch forwards & get model keys as primary
    player names """
    branch = _find_forward_branch(all_player_names,
                                  self.primary_player_name_patterns)
    _sort_branch_timstamps(branch)
    logging.info('found branch {}:'.format(branch))

    if self.timestamp_criterion == 'latest':
      # delete the last model-key as it may not yet finish
      last_model_key = list(branch.keys())[-1]  # as it is an OrderDict
      branch.pop(last_model_key)
      logging.info('deleted the last model-key {}'.format(last_model_key))

    # trimmed branch with sorted and non-overlapped timestamps
    leaf_model_key = list(branch.keys())[-1]
    model_keys, timestamps = _trim_sorted_branch_by_timestamps(
      branch, leaf_model_key
    )
    logging.info('trimmed and sorted model keys and timestamps:')
    for m, t in zip(model_keys, timestamps):
      logging.info("{} {}".format(m, t))

    # prune further when necessary
    if self.timestamp_criterion == 'latest':
      # pick the last model in a branch
      model_keys, timestamps = _pick_latest_timestamps(model_keys, timestamps)
      logging.info('after picking the latest model keys and timestamps:')
      for m, t in zip(model_keys, timestamps):
        logging.info('  {} {}'.format(m, t))
    elif self.timestamp_criterion == 'all':
      # pick all the models in a branch
      pass
    else:
      raise ValueError('Unknown timestamp criterion {}'.format(
        self.timestamp_criterion
      ))

    # prune further by frequency (minimal interval between two models) when
    # necessary
    if self._freq_secs > 0:
      model_keys_original, timestamps_original = model_keys, timestamps
      model_keys, timestamps = [], []
      prev_ts = None  # previous timestamp
      for mk, ts in zip(model_keys_original, timestamps_original):
        should_collect = False
        if prev_ts is None:
          # always collect the first one
          should_collect = True
        else:
          t_current = datetime.strptime(ts, '%Y%m%d%H%M%S')
          t_prev = datetime.strptime(prev_ts, '%Y%m%d%H%M%S')
          if (t_current - t_prev).total_seconds() >= self._freq_secs:
            # large enough interval, collect it
            should_collect = True
        if should_collect:
          model_keys.append(mk)
          timestamps.append(ts)
          # update
          prev_ts = ts

      logging.info('after trimming using freq_secs {}:'.format(self._freq_secs))
      for m, t in zip(model_keys, timestamps):
        logging.info("  {} {}".format(m, t))

    return ['{}_{}'.format(m, t) for m, t in zip(model_keys, timestamps)]
