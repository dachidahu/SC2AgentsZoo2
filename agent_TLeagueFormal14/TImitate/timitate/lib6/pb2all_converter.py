from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np
from gym import spaces
from collections import OrderedDict
import copy

from timitate.lib6.pb2action_converter import PB2ActionConverter
from timitate.lib6.pb2feature_converter import PB2FeatureConverter
from timitate.lib6.pb2mask_converter import PB2MaskConverter
from timitate.lib6.z_actions import ZERG_ABILITIES, BASES_SET, EGGS_SET
from timitate.utils.const import SAMPLING_WEIGHT_LIB6, IDEAL_BASE_POS_DICT
from timitate.utils.utils import map_name_transform


def _flatten_to_space_list(*args):
  """flatten to a list of spaces. depth-first recursion

  Example:
  sp0 = Tuple([
    Box(shape=(2,3),low=0,high=1,dtype=np.float32),
    Box(shape=(5,7),low=0,high=1,dtype=np.float32)
  ])
  sp1 = Box(shape=(21,),low=0,high=1,dtype=np.float32)
  sp2 = Tuple([
    Box(shape=(32,2),low=0,high=1,dtype=np.float32),
    Box(shape=(56,),low=0,high=1,dtype=np.float32)
  ])

  Then we have:
  _flatten_to_space_list([sp0, sp1, sp2])
  [Box(2, 3), Box(5, 7), Box(21,), Box(32, 2), Box(56,)]

  _flatten_to_space_list(Tuple([sp0, sp1, sp2]))
  [Box(2, 3), Box(5, 7), Box(21,), Box(32, 2), Box(56,)]
  """
  ret_sps = []
  for item in args:
    if isinstance(item, list):
      ret_sps += _flatten_to_space_list(*item)
    elif isinstance(item, spaces.Tuple):
      ret_sps += _flatten_to_space_list(item.spaces)
    elif isinstance(item, spaces.Box):
      ret_sps.append(item)
    else:
      raise ValueError('Unknown item {}, type {}'.format(item, type(item)))
  return ret_sps


class PB2AllConverter(object):
  def __init__(self, noop_nums=tuple((i+1 for i in range(128))),
               max_unit_num=600,
               input_map_size=(128, 128),  # KJ original size 152, 168
               output_map_size=(128, 128),
               max_bo_count=50,
               max_bobt_count=50,
               zstat_data_src=None,
               zstat_zeroing_prob=0.1,
               addon_sam_w_dict=None,
               dict_space=False,
               sort_executors=None,  # {None}|'v1'|'v2'
               add_cargo_to_units=False,
               game_version='4.7.1',
               zmaker_version='v3',
               hack_smart2rally_hatchery_screen=False,
               delete_dup_action=None,
               crop_to_playable_area=False,
               inj_larv_rule=False,
               ab_dropout_list=None):
    self._pb2mask_converter = PB2MaskConverter(
      max_unit_num=max_unit_num,
      map_resolution=output_map_size,
      add_cargo_to_units=add_cargo_to_units,
      game_version=game_version,
      inj_larv_rule=inj_larv_rule,
      ab_dropout_list=ab_dropout_list)
    self._pb2action_converter = PB2ActionConverter(
      max_unit_num=max_unit_num,
      max_noop_num=len(noop_nums),
      map_resolution=output_map_size,
      sort_executors=sort_executors,
      hack_smart2rally_hatchery_screen=hack_smart2rally_hatchery_screen)
    self._pb2feature_converter = PB2FeatureConverter(
      max_unit_num=max_unit_num,
      max_bo_count=max_bo_count,
      max_bobt_count=max_bobt_count,
      map_resolution=input_map_size,
      zstat_data_src=zstat_data_src,
      game_version=game_version,
      add_cargo_to_units=add_cargo_to_units,
      crop_to_playable_area=crop_to_playable_area,
      zstat_version=zmaker_version)

    self._zstat_zeroing_prob = zstat_zeroing_prob
    self._noop_nums = sorted(noop_nums)
    self._cached_frames = []
    self._last_game_loop = 0
    self._map_name = None
    self._arg_mask = self._pb2mask_converter.get_arg_mask()
    self._max_unit_num = max_unit_num
    self._max_bases_num = max([len(IDEAL_BASE_POS_DICT[key]) for key in IDEAL_BASE_POS_DICT])
    self._base_mask = {}
    self._base_mask['Unknown'] = [False]*self._max_bases_num
    self._dict_space = dict_space
    self._addon_sam_w_dict = addon_sam_w_dict
    for key in IDEAL_BASE_POS_DICT:
      self._base_mask[key] = [True]*len(IDEAL_BASE_POS_DICT[key])+\
                             [False]*(self._max_bases_num-len(IDEAL_BASE_POS_DICT[key]))
    self._delete_dup_action = delete_dup_action
    self._dbg_prefix = 'pb2all6dbg'

  def _check_compatibility(self, action, mask, obs, correct_selection=False):
    ab_mask, len_mask, selection_mask, cmd_unit_mask, cmd_pos_mask = mask
    ab_action = action[0]
    s_action = action[3]
    cmd_u_action = action[4]
    cmd_pos_action = action[5]

    if not ab_mask[ab_action]:
      print('WARN: ability action in replay conflict with mask: {}'.format(
        ZERG_ABILITIES[ab_action][0]
      ))
      print('av_acts in gamecore: {}'.format(obs.observation.abilities))
      print('player_common: ', obs.observation.player_common)
      return False
    if self._arg_mask[ab_action, 3-1]:
      remove_idx = []
      for i in s_action:
        if i != self._max_unit_num and not selection_mask[ab_action, i]:
          if correct_selection:
            remove_idx.append(i)
          else:
            print('WARN: selection action in replay conflict with mask.')
            return False
      corrected_s_action = list(s_action)
      for i in remove_idx:
        corrected_s_action.remove(i)
      corrected_s_action += [self._max_unit_num]*(self._pb2action_converter._seq_max_num-len(corrected_s_action))
      corrected_s_action = np.asarray(corrected_s_action, dtype=np.int32)
      if np.sum(corrected_s_action == self._max_unit_num) == self._pb2action_converter._seq_max_num:
        print('WARN: selection action is empty after mask correction and is conflict with replay.')
        return False
      # converted action from pb2action is a list, and its elements can be rewritten by directly =
      action[3] = corrected_s_action
    if self._arg_mask[ab_action, 4-1] and not cmd_unit_mask[ab_action, cmd_u_action]:
      print('WARN: cmd_u action in replay conflict with mask.')
      print('target_u:', obs.observation.raw_data.units[cmd_u_action])
      return False
    reshaped_mask = np.reshape(cmd_pos_mask[ab_action, :, :], (-1,))
    if self._arg_mask[ab_action, 5-1]:
      if not reshaped_mask[cmd_pos_action]:
        print('WARN: cmd_pos action in replay conflict with mask.')
        print('ab_action: {}, pos_action: {}'.format(ZERG_ABILITIES[ab_action][0], cmd_pos_action))
        # import matplotlib.pyplot as plt
        # plt.imshow(cmd_pos_mask[ab_action, :, :])
        # plt.show()
        # input("press to close")
        # plt.close()
        # from PIL import Image
        # array = np.array(cmd_pos_mask[ab_action, :, :]*255, dtype=np.int8)
        # im = Image.fromarray(array, mode='L')
        # im = im.convert('RGB')
        # im.save('mask.jpg')
        return False
    return True

  def _similar_to_last_v1(self, action, pb_obs, radius=1.0):
    if len(self._cached_frames) == 0:
      return False
    a_ab1, a_noop1, a_shift1, a_select1, a_cmd_u1, a_cmd_pos1 = action
    a_ab2, a_noop2, a_shift2, a_select2, a_cmd_u2, a_cmd_pos2 = self._cached_frames[-1]['action']
    select_set1 = set([pb_obs.observation.raw_data.units[i].tag
                       for i in a_select1 if i < self._max_unit_num])
    select_set2 = set([self._cached_frames[-1]['pb'][0].observation.raw_data.units[i].tag
                       for i in a_select2 if i < self._max_unit_num])
    x1, y1 = self._pb2action_converter.label2pos(a_cmd_pos1)
    x2, y2 = self._pb2action_converter.label2pos(a_cmd_pos2)
    # the following condition: same ability, current shift=False,
    # same selection tags (must be tags), same cmd_u tag or similar cmd_pos
    if a_ab1 == a_ab2 and (
            ZERG_ABILITIES[a_ab1][0].startswith('Rally') or
            ZERG_ABILITIES[a_ab1][0].startswith('Smart')):
      if not a_shift1 and not a_shift2 and self._arg_mask[a_ab1][2] and select_set1 == select_set2:
        if (self._arg_mask[a_ab1][3] and pb_obs.observation.raw_data.units[a_cmd_u1].tag ==
            self._cached_frames[-1]['pb'][0].observation.raw_data.units[a_cmd_u2].tag) or \
           (self._arg_mask[a_ab2][4] and ((x1-x2)**2+(y1-y2)**2)**0.5 < radius):
          return True
    return False

  def _similar_to_last_v2(self, action, pb_obs):
    if len(self._cached_frames) == 0:
      return False
    a_ab1, a_noop1, a_shift1, a_select1, a_cmd_u1, a_cmd_pos1 = action
    a_ab2, a_noop2, a_shift2, a_select2, a_cmd_u2, a_cmd_pos2 = self._cached_frames[-1]['action']

    units1 = pb_obs.observation.raw_data.units
    units2 = self._cached_frames[-1]['pb'][0].observation.raw_data.units

    select_set1 = set([units1[i].tag for i in a_select1 if i < self._max_unit_num])
    select_set2 = set([units2[i].tag for i in a_select2 if i < self._max_unit_num])
    # the following condition: same ability, same shift=False,
    # same selection tags (must be tags)
    if a_ab1 == a_ab2 and (
            ZERG_ABILITIES[a_ab1][0].startswith('Rally') or
            ZERG_ABILITIES[a_ab1][0].startswith('Smart')) and \
            (all([units1[i].unit_type in BASES_SET
                  for i in a_select1 if i < self._max_unit_num]) or
             all([units1[i].unit_type in EGGS_SET
                  for i in a_select1 if i < self._max_unit_num])):
      if not a_shift1 and not a_shift2 and self._arg_mask[a_ab1][2] and select_set1 == select_set2:
        if pb_obs.observation.game_loop - self._cached_frames[-1]['game_loop'] <= len(self._noop_nums):
          # rewrite last action's cmd_u and cmd_pos heads if possible,
          # but no matter what, we need to delete the current action
          if self._arg_mask[a_ab1][3]:
            tags2 = [u.tag for u in units2]
            if units1[a_cmd_u1].tag in tags2:
              index2 = tags2.index(units1[a_cmd_u1].tag)
              if index2 < self._max_unit_num:
                ori_last_action = copy.deepcopy(self._cached_frames[-1]['action'])
                # try to rewrite last action's cmd_u here
                self._cached_frames[-1]['action'][4] = index2
                # but need to check compatibility again
                if not self._cached_frames[-1]['mask'][3][a_ab1, index2]:
                  # if fail to pass the check, recover to the original action
                  self._cached_frames[-1]['action'] = ori_last_action
          elif self._arg_mask[a_ab1][4]:
            self._cached_frames[-1]['action'][5] = action[5]
          print(', '.join([self._dbg_prefix,
                          'gal:{}'.format(pb_obs.observation.game_loop),
                          'sim2lastv2:True']))
          return True
    print(', '.join([self._dbg_prefix,
                    'gal:{}'.format(pb_obs.observation.game_loop),
                    'sim2lastv2:False']))
    return False

  def _generate_sample(self, frame):
    obs = (
      *frame['feature'],
      *frame['mask'],
      *self._pb2action_converter.to_tensors(frame['last_action']),
    )
    act = self._pb2action_converter.to_tensors(frame['action'])
    w = self._get_ability_weight(frame['action'][0])
    if self._dict_space:
      return (dict(zip(self.tensor_names, obs)),
              dict(zip(self._pb2action_converter.tensor_names, act))), w
    else:
      return (obs, act), w

  def _get_ability_weight(self, ab_id):
    # TODO: get weight according to ability.
    if ZERG_ABILITIES[ab_id][0] in SAMPLING_WEIGHT_LIB6:
      w = SAMPLING_WEIGHT_LIB6[ZERG_ABILITIES[ab_id][0]]
    elif self._addon_sam_w_dict is not None:
      w = 1.0
      for key in self._addon_sam_w_dict:
        if ZERG_ABILITIES[ab_id][0].startswith(key):
          w = self._addon_sam_w_dict[key]
          break
    else:
      if ZERG_ABILITIES[ab_id][0].startswith('Research'):
        w = 5.0
      elif ZERG_ABILITIES[ab_id][0].startswith('Effect'):
        w = 5.0
      else:
        w = 1.0
    return w

  def reset(self, replay_name, player_id, mmr, map_name, **kwargs):
    """reset the current replay and player id that this converter works on.
    It affects the z stat, mmr, etc"""
    self._cached_frames = []
    self._last_game_loop = 0
    self._pb2feature_converter.reset(
      replay_name=replay_name,
      player_id=player_id,
      mmr=mmr,
      map_name=map_name,
      zstat_zeroing_prob=self._zstat_zeroing_prob
    )
    self._pb2action_converter.reset(map_name)
    self._map_name = map_name_transform(map_name)

  def convert(self, pb, next_pb):
    game_loop = pb[0].observation.game_loop
    # terminal frame
    if next_pb is None:
      self.cache_frame({"action": None,
                        "mask": None,
                        "feature": None,
                        "pb": None,
                        "game_loop": game_loop})
      return self._make_samples()

    action = self._pb2action_converter.convert(pb[0], next_pb[0])
    if self._pb2action_converter.is_noop(action):
      if game_loop < self._last_game_loop + self._noop_nums[-1]:
        return []

    if self._delete_dup_action in ['v2', 'all']:
      if self._similar_to_last_v2(action, pb[0]):
        action = self._pb2action_converter._no_op()
      if self._pb2action_converter.is_noop(action):
        if game_loop < self._last_game_loop + self._noop_nums[-1]:
          return []
    elif self._delete_dup_action in ['v1', 'all']:
      if self._similar_to_last_v1(action, pb[0]):
        action = self._pb2action_converter._no_op()
      if self._pb2action_converter.is_noop(action):
        if game_loop < self._last_game_loop + self._noop_nums[-1]:
          return []

    mask = self._pb2mask_converter.convert(pb)

    if not self._check_compatibility(action, mask, pb[0], correct_selection=True):
      print(next_pb[0].actions)
      print(game_loop)
      # label incompatible sample as no_op
      action = self._pb2action_converter._no_op()
      if game_loop < self._last_game_loop + self._noop_nums[-1]:
        return []

    self._last_game_loop = game_loop
    frame = {"action": action,
             "mask": mask,
             "feature": None,
             "pb": pb,
             "game_loop": game_loop}
    self.cache_frame(frame)
    return self._make_samples()

  def cache_frame(self, frame):
    # if first frame, set last_action to noop
    if len(self._cached_frames) == 0 and frame["pb"] is not None:
      frame["last_action"] = self._pb2action_converter._no_op()
      frame["feature"] = self._pb2feature_converter.convert(frame["pb"], None, None, None)
    self._cached_frames.append(frame)

  def should_return(self):
    return len(self._cached_frames) > 1

  def _make_samples(self):
    if not self.should_return():
      return []

    for i in range(len(self._cached_frames)-1):
      noop_duration = self._cached_frames[i+1]["game_loop"] - self._cached_frames[i]["game_loop"]
      noop_label = max(sum([n <= noop_duration for n in self._noop_nums]), 1)
      self._cached_frames[i]["action"][1] = noop_label - 1

    for i in range(1, len(self._cached_frames)):
      if self._cached_frames[i]["pb"] is not None:
        last_action = self._cached_frames[i-1]["action"]
        last_units = self._cached_frames[i-1]["pb"][0].observation.raw_data.units
        last_tar_tag = last_units[last_action[4]].tag if self._arg_mask[last_action[0], 4-1] else None
        last_selected_unit_tags = []
        for idx in last_action[3]:
          if idx != self._max_unit_num:
            last_selected_unit_tags.append(last_units[idx].tag)
        self._cached_frames[i]["last_action"] = last_action
        self._cached_frames[i]["feature"] = self._pb2feature_converter.convert(
          self._cached_frames[i]["pb"], last_tar_tag, last_units, last_selected_unit_tags)
    ret = [self._generate_sample(frame) for frame in self._cached_frames[:-1]]
    self._cached_frames = self._cached_frames[-1:]
    return ret

  @property
  def space(self):
    input_sps = list(
      self._pb2feature_converter.space.spaces +
      self._pb2mask_converter.space.spaces +
      self._pb2action_converter.space.spaces
    )
    if self._dict_space:
      return spaces.Tuple([
        spaces.Dict(OrderedDict(zip(self.tensor_names, input_sps))),  # space from current-step feature
        spaces.Dict(OrderedDict(zip(self._pb2action_converter.tensor_names, self._pb2action_converter.space.spaces)))  # space from last-step action
      ])
    else:
      return spaces.Tuple([
        spaces.Tuple(input_sps),  # space from current-step feature
        self._pb2action_converter.space  # space from last-step action
      ])

  @property
  def tensor_names(self):
    return self._pb2feature_converter.tensor_names + \
           self._pb2mask_converter.tensor_names + \
           self._pb2action_converter.tensor_names


if __name__=='__main__':
  pb2all = PB2AllConverter(
    noop_nums=tuple((i+1 for i in range(128))),
    max_unit_num=600,
    input_map_size=(128, 128),
    output_map_size=(128, 128),
    max_bo_count=50,
    max_bobt_count=50,
    zstat_data_src=None,
    zstat_zeroing_prob=0.1,
    addon_sam_w_dict=None,
    dict_space=True,
    game_version='4.7.1',
    zmaker_version='v3'
  )
  for sp in pb2all.space.spaces:
    assert isinstance(sp.spaces, dict)
    for e in sp.spaces:
      print('{}: {}'.format(e, sp.spaces[e]))
