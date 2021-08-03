from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import copy
import numpy as np
from absl import app
from collections import OrderedDict
from gym import spaces
from pysc2 import run_configs
from pysc2.lib import point
from pysc2.lib.features import PlayerRelative
from pysc2.lib.typeenums import UNIT_TYPEID
from s2clientprotocol import sc2api_pb2 as sc_pb
from timitate.base_converter import BaseConverter

from timitate.lib6.z_actions import select_unit_type_list
from timitate.lib6.z_actions import ZERG_ABILITIES, ABILITY_TYPES, ALLIANCE, ActionSpec
from timitate.lib6.z_actions import z_quick_ab_map, z_name_map, z_pos_ab_map, z_unit_ab_map
from timitate.lib6.z_actions import z_sub2gen_map

from timitate.utils.const import NEUTRAL_MINERAL_SET, BUILDINGS_SET, BASES_SET, EGGS_SET, executor_pre_order
from timitate.utils.utils import find_nearest_KJ_base, find_nearest_base, CoorSys
from timitate.utils.utils import map_name_transform


class PB2ActionConverter(BaseConverter):

  def __init__(self, map_resolution=(200, 176), max_unit_num=600,
               max_noop_num=10, dict_space=False, sort_executors=None,
               hack_smart2rally_hatchery_screen=False):
    self._resolution_c, self._resolution_r = map_resolution
    self._max_unit_num = max_unit_num
    self._coorsys = CoorSys(self._resolution_r, self._resolution_c)
    self._map_name = None
    self._dict_space = dict_space
    self._sort_executors = sort_executors
    self._action_spec = ActionSpec(max_unit_num, max_noop_num, map_resolution)
    if self._dict_space:
      self._seq_max_num = self.space['A_SELECT'].shape[0]
    else:
      self._seq_max_num = self.space.spaces[3].shape[0]
    self._hack_smart2rally_hatchery_screen = hack_smart2rally_hatchery_screen
    self._dbg_hack_prefix = 'pb2act6dbg'

  def reset(self, map_name: str):
    self._map_name = map_name_transform(map_name)

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

  def to_tensors(self, action):
    if self._dict_space:
      return OrderedDict([(sp[0], np.array(a, dtype=sp[1].dtype))
                          for a, sp in zip(action, self.space.spaces.items())])
    else:
      return tuple(np.array(a, dtype=sp.dtype) for a, sp in zip(action, self.space.spaces))

  def pos2label(self, pos):
    # resize image
    return self._coorsys.xy_to_loc(int(pos[0]*self._resolution_c/self.ori_x),
                                   int(pos[1]*self._resolution_r/self.ori_y))

  def label2pos(self, label):
    return self._coorsys.loc_to_xy(label)

  def _default_action(self):
    return [z_name_map['no_op'], 0, 0,
            np.array([self._max_unit_num]*self._seq_max_num, dtype=np.int32), 0, 0]

  def _no_op(self):
    action = self._default_action()
    action[0] = z_name_map['no_op']
    return action

  def is_noop(self, action):
    return action[0] == z_name_map['no_op']

  def _executors2selection(self, cmd, obs_pb):
    units = [(i, u) for i, u in enumerate(obs_pb.observation.raw_data.units[:self._max_unit_num])
             if u.tag in cmd.unit_tags]
    if not self._sort_executors:
      pass
    elif self._sort_executors == 'v1':
      units.sort(key=lambda x: (x[1].unit_type, x[1].pos.x+x[1].pos.y))
    elif self._sort_executors == 'v2':
      # Sort by predefined unit_type order and pos to ave_pos
      safe_order = copy.deepcopy(executor_pre_order)
      safe_order.extend([u[1].unit_type for u in units if u[1].unit_type not in executor_pre_order])
      ave_pos = [np.average([u[1].pos.x for u in units]), np.average([u[1].pos.y for u in units])]
      units.sort(key=lambda x: (safe_order.index(x[1].unit_type),
                                (x[1].pos.x-ave_pos[0])**2+(x[1].pos.y-ave_pos[1])**2))
    else:
      raise NotImplementedError('Unknown sort_executors type'
                                ' {}.'.format(self._sort_executors))
    executors = [u[0] for u in units]
    if len(executors) < self._seq_max_num:
      executors += [self._max_unit_num] * (self._seq_max_num - len(executors))
    else:
      executors[self._seq_max_num:] = []
    return np.asarray(executors, dtype=np.int32)

  def _action_pos(self, raw_command, queue, obs_pb):
    action = self._default_action()
    action[0] = z_pos_ab_map[raw_command.ability_id]
    action[2] = int(queue)
    action[3] = self._executors2selection(raw_command, obs_pb)
    pb_tar_loc = raw_command.target_world_space_pos
    pos = (pb_tar_loc.x, pb_tar_loc.y)
    creep = obs_pb.observation.raw_data.map_state.creep
    self.ori_y, self.ori_x = creep.size.y, creep.size.x
    action[5] = self.pos2label(pos)

    # Post rule for label correction
    if raw_command.ability_id == ZERG_ABILITIES[z_name_map['Smart_screen']][2]:
      executor_units = [obs_pb.observation.raw_data.units[i]
                        for i in action[3] if i < self._max_unit_num]
      # hack pure morphing selection; note that mixed morphing must not be hacked
      if all([u.unit_type in EGGS_SET for u in executor_units]):
        action[0] = z_name_map['Rally_Morphing_Unit_screen']
        print(', '.join([
          self._dbg_hack_prefix,
          'gal:{}'.format(obs_pb.observation.game_loop),
          'hack Smart_screen to Rally_Morphing_Unit_screen'
        ]))
      else:
        # hack base rally pos
        if self._hack_smart2rally_hatchery_screen:
          if all([u.unit_type in BASES_SET for u in executor_units]):
            action[0] = z_name_map['Rally_Hatchery_Units_screen']
            print(', '.join([
              self._dbg_hack_prefix,
              'gal:{}'.format(obs_pb.observation.game_loop),
              'hack Smart_screen to Rally_Hatchery_Units_screen'
            ]))
    return action

  def _action_unit(self, raw_command, queue, obs_pb):
    # obs_pb should be the last frame
    tags = [u.tag for u in obs_pb.observation.raw_data.units[:self._max_unit_num]]
    action = self._default_action()
    if raw_command.target_unit_tag in tags:
      action[0] = z_unit_ab_map[raw_command.ability_id]
      action[2] = int(queue)
      action[3] = self._executors2selection(raw_command, obs_pb)
      action[4] = tags.index(raw_command.target_unit_tag)

      # Post rule for label correction
      executor_units = [obs_pb.observation.raw_data.units[i]
                        for i in action[3] if i < self._max_unit_num]
      target_unit = obs_pb.observation.raw_data.units[action[4]]
      if raw_command.ability_id == ZERG_ABILITIES[z_name_map['Smart_unit']][2]:
        # hack pure morphing selection; note that mixed morphing must not be hacked
        if all([u.unit_type in EGGS_SET for u in executor_units]):
          action[0] = z_name_map['Rally_Morphing_Unit_on_unit']
          print(', '.join([
            self._dbg_hack_prefix,
            'gal:{}'.format(obs_pb.observation.game_loop),
            'hack Smart_unit to Rally_Morphing_Unit_on_unit'
          ]))
        # hack rally, gather and attack
        elif (target_unit.unit_type in NEUTRAL_MINERAL_SET or
             (target_unit.unit_type == UNIT_TYPEID.ZERG_EXTRACTOR.value and
              target_unit.alliance == ALLIANCE.SELF.value)):
          # when target is resource
          if all([u.unit_type == UNIT_TYPEID.ZERG_DRONE.value for u in executor_units]):
            action[0] = z_name_map['Harvest_Gather_Drone_screen']
            print(', '.join([
              self._dbg_hack_prefix,
              'gal:{}'.format(obs_pb.observation.game_loop),
              'hack Smart_unit to Rally_Morphing_Unit_on_unit'
            ]))
          elif all([u.unit_type in BASES_SET for u in executor_units]):
            action[0] = z_name_map['Rally_Hatchery_Workers_on_unit']
            print(', '.join([
              self._dbg_hack_prefix,
              'gal:{}'.format(obs_pb.observation.game_loop),
              'hack Smart_unit to Rally_Hatchery_Workers_on_unit'
            ]))
        elif target_unit.alliance == ALLIANCE.SELF.value:
          # when target is self unit and the executors contain base
          if all([u.unit_type in BASES_SET for u in executor_units]):
            action[0] = z_name_map['Rally_Hatchery_Units_on_unit']
            print(', '.join([
              self._dbg_hack_prefix,
              'gal:{}'.format(obs_pb.observation.game_loop),
              'hack Smart_unit to Rally_Hatchery_Units_on_unit'
            ]))
        elif target_unit.alliance == ALLIANCE.ENEMY.value:
          # when target is enemy
          action[0] = z_name_map['Attack_Attack_unit']
          print(', '.join([
            self._dbg_hack_prefix,
            'gal:{}'.format(obs_pb.observation.game_loop),
            'hack Smart_unit to Attack_Attack_unit'
          ]))
      return action
    else:  # unit died in last frame?
      return self._no_op()

  def _action_quick(self, cmd, queue, obs_pb):
    action = self._default_action()
    action[0] = z_quick_ab_map[cmd.ability_id]
    action[2] = int(queue)
    action[3] = self._executors2selection(cmd, obs_pb)
    return action

  def reverse_action(self, raw_action, last_obs_pb):
    cmd = raw_action.unit_command
    queue = int(cmd.queue_command)
    # Convert sub_id action to gen_id action
    if cmd.ability_id in z_sub2gen_map:
      cmd.ability_id = z_sub2gen_map[cmd.ability_id]
    if cmd.HasField('target_world_space_pos'):
      if cmd.ability_id in z_pos_ab_map:
        return self._action_pos(cmd, queue, last_obs_pb)
    elif cmd.HasField('target_unit_tag'):
      if cmd.ability_id in z_unit_ab_map:
        return self._action_unit(cmd, queue, last_obs_pb)
    else:
      if cmd.ability_id in z_quick_ab_map:
        return self._action_quick(cmd, queue, last_obs_pb)
    return self._no_op()

  def convert(self, last_obs_pb, obs_pb):
    actions = obs_pb.actions
    raw_actions = [a.action_raw for a in actions if a.HasField('action_raw')]
    if len(raw_actions) > 0:
      ext_actions = [self.reverse_action(a, last_obs_pb) for a in raw_actions]
      # if there are more than one raw_actions, return the first?
      if len(ext_actions) > 1:
        print('WARN: more than one raw actions in one frame. Only select the first.')
      ret = ext_actions[0]
    else:
      ret = self._no_op()
    return ret


def main(argv):
  pb2act = PB2ActionConverter(map_resolution=(200, 176),
                              max_unit_num=512,
                              max_noop_num=128,
                              dict_space=True)
  print(pb2act.space)


if __name__ == '__main__':
  app.run(main)
