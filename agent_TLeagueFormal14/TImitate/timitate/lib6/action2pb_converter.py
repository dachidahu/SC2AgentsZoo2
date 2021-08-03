from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from math import sqrt
from collections import OrderedDict

import numpy as np
from gym import spaces
from pysc2.lib.typeenums import ABILITY_ID
from tleague.utils import logger

from timitate.base_converter import BaseConverter
from timitate.utils.const import IDEAL_BASE_POS_DICT, IDEAL_BASE_POS_CROP_DICT
from timitate.utils.const import z_skill_tar_map
from timitate.utils.const import z_train_tar_map_v6
from timitate.utils.const import z_morph_tar_map_v6
from timitate.utils.utils import CoorSys, map_name_transform
from timitate.utils.mask_fn import find_nearest_buildable_pos
from timitate.lib6.z_actions import ZERG_ABILITIES
from timitate.lib6.z_actions import ABILITY_TYPES
from timitate.lib6.z_actions import z_name_map
from timitate.lib6.z_actions import noop
from timitate.lib6.z_actions import ActionSpec
from timitate.utils.commands import select_units_by_pos, select_units_by_tags
from timitate.lib6.zstat_utils import BUILD_ORDER_ABILITY_CANDIDATES
from timitate.lib6.zstat_utils import EFFECT_ABILITY_CANDIDATES
from timitate.lib6.zstat_utils import RESEARCH_ABILITY_CANDIDATES


sid2uid_map = dict([(ZERG_ABILITIES[z_name_map[skill_name]][2], z_skill_tar_map[skill_name][0])
                    for skill_name in z_skill_tar_map])
tid2uid_map = dict([(ZERG_ABILITIES[z_name_map[train_name]][2], z_train_tar_map_v6[train_name])
                    for train_name in z_train_tar_map_v6])
mid2uid_map = dict([(ZERG_ABILITIES[z_name_map[morph_name]][2], z_morph_tar_map_v6[morph_name][0])
                    for morph_name in z_morph_tar_map_v6])


class Action2PBConverter(BaseConverter):
  def __init__(self, map_padding_size=(152, 168), dict_space=False,
               max_unit_num=600, max_noop_num=128, correct_pos_radius=2.0,
               verbose=40, correct_building_pos=False, crop_to_playable_area=False):
    self._map_padding_size = map_padding_size
    self._coorsys = CoorSys(r_max=map_padding_size[1], c_max=map_padding_size[0])
    self._dict_space = dict_space
    self._max_unit_num = max_unit_num
    self._correct_pos_radius = correct_pos_radius
    self._correct_building_pos = correct_building_pos
    self._crop_to_playable_area = crop_to_playable_area
    self._action_spec = ActionSpec(max_unit_num, max_noop_num, map_padding_size)
    self.ideal_positions = None
    with logger.scoped_configure(dir=None, format_strs=['stderr']):
      logger.set_level(verbose)
      self.logger = logger.Logger.CURRENT

  @property
  def space(self):
    sps = self._action_spec.space
    if self._dict_space:
      return spaces.Dict(OrderedDict(zip(self.tensor_names, sps)))
    else:
      return spaces.Tuple(sps)

  @property
  def tensor_names(self):
    return self._action_spec.tensor_names

  def _find_unit_by_tag(self, tag, units):
    for u in units:
        if u.tag == tag:
          return u
    return None

  def _transform_coor(self, x, y, ori_x, ori_y):
    return ((x + 0.5) * ori_x / float(self._map_padding_size[0]),
            (y + 0.5) * ori_y / float(self._map_padding_size[1]))

  def convert(self, action, pb=None):
    if self._dict_space:
      a_ab, a_noop, a_sft, a_s, a_cmd_u, a_cmd_pos = [action[name] for name in self.tensor_names]
    else:
      assert len(action) == 6, 'action len should be 6'
      a_ab, a_noop, a_sft, a_s, a_cmd_u, a_cmd_pos = action

    obs_pb, game_info = pb
    units = obs_pb.observation.raw_data.units
    creep = obs_pb.observation.raw_data.map_state.creep
    ori_x, ori_y = creep.size.x, creep.size.y
    selected_units = [units[idx] for idx in a_s if idx != self._max_unit_num]
    selected_tags = [u.tag for u in selected_units]

    ab_name = ZERG_ABILITIES[a_ab][0]
    ab_type = ZERG_ABILITIES[a_ab][1]
    ab_sub_id = ZERG_ABILITIES[a_ab][2]
    action2pb_fn = ZERG_ABILITIES[a_ab][-1]
    pos_mask_fn = ZERG_ABILITIES[a_ab][-4]

    # logging the watched abilities
    if ab_sub_id in (BUILD_ORDER_ABILITY_CANDIDATES
                     + RESEARCH_ABILITY_CANDIDATES
                     + [ABILITY_ID.CANCEL.value, ABILITY_ID.CANCEL_LAST.value]):
      level = logger.WARN
    elif ab_sub_id in EFFECT_ABILITY_CANDIDATES:
      level = logger.INFO
    else:
      level = logger.DEBUG
    game_loop = obs_pb.observation.game_loop
    self.logger.log(
      'Execute action {} at game_loop {}.'.format(ab_name, game_loop),
      level=level
    )

    if ab_type == ABILITY_TYPES.NO_OP:
      return action2pb_fn()
    elif ab_type == ABILITY_TYPES.CMD_POS:
      x, y = self._coorsys.loc_to_xy(a_cmd_pos)
      x, y = self._transform_coor(x=x, y=y, ori_x=ori_x, ori_y=ori_y)
      # sub_id that needs hacking or special treatment
      x_origin, y_origin = x, y
      self.logger.log(
        f'CMD_POS {ab_name} at {(x_origin, y_origin)}.', level=level-5
      )
      if ab_sub_id == ABILITY_ID.BUILD_HATCHERY.value:
        x, y = self._correct_to_ideal_base_pos(obs_pb, x, y)
        self.logger.log(
          f'Correct building hatchery from {(x_origin, y_origin)} to {(x, y)}.',
          level=level
        )
      elif self._correct_building_pos:
        x, y = find_nearest_buildable_pos(ab_sub_id, x, y, obs_pb, game_info,
                                          pos_mask_fn, self._correct_pos_radius)
        if (x, y) != (x_origin, y_origin):
          self.logger.log(
            f'Correct building pos from {(x_origin, y_origin)} to {(x, y)}.',
            level=level
          )
      return action2pb_fn(ab_sub_id, a_sft, selected_tags, (x, y))
    elif ab_type == ABILITY_TYPES.CMD_UNIT:
      if a_cmd_u <= len(units):
        return action2pb_fn(ab_sub_id, a_sft, selected_tags, units[a_cmd_u].tag)
      else:
        self.logger.log('Predicted target unit outside max_unit_num. Ignore this action as noop.')
        return noop()
    elif ab_type == ABILITY_TYPES.CMD_QUICK:
        return action2pb_fn(ab_sub_id, a_sft, tags=selected_tags)
    else:
      raise BaseException('wtf ab_type: {}'.format(ab_type))

  def _correct_to_ideal_base_pos(self, obs_pb, x, y):
    """correct the coord (x, y) to an ideal base position when falling into the
     neighborhood"""
    for (ix, iy) in self.ideal_positions:
      d = sqrt((x - ix)**2 + (y - iy)**2)
      if d < self._correct_pos_radius:
        x, y = ix, iy
        break
    return x, y

  def reset(self, obs, **kwargs):
    if obs.game_info is not None:
      map_name = obs.game_info.map_name
    elif 'map_name' in kwargs:
      map_name = kwargs['map_name']
    else:
      map_name = 'KairosJunction'
    map_name = map_name_transform(map_name)
    # NOTE: can get from obs using timitate.utils.find_idea_base_pos.find_all_base_position
    self.ideal_positions = IDEAL_BASE_POS_CROP_DICT[map_name] \
      if self._crop_to_playable_area else IDEAL_BASE_POS_DICT[map_name]