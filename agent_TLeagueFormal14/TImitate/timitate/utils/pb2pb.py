import random
import numpy as np
from timitate.utils.utils import bitmap2array
from timitate.utils.const import MapReflectPoint, MAP_ORI_SIZE_DICT, MAP_PLAYABLE_AREA_DICT
from timitate.lib6.z_actions import z_pos_ab_map
from .utils import map_name_transform


def make_aug_data(obs, map_name):
  # feature minimap
  if hasattr(obs.observation, 'feature_minimap'):
    creep = obs.observation.feature_minimap.creep
    terrain_height = obs.observation.feature_minimap.height_map
    visibility = obs.observation.feature_minimap.visibility_map
  elif hasattr(obs.observation, 'feature_layer_data'):
    creep = obs.observation.feature_layer_data.minimap_renders.creep
    trans_2d(creep, map_name)
    creep = obs.observation.raw_data.map_state.creep
    trans_2d(creep, map_name)
    terrain_height = obs.observation.feature_layer_data.minimap_renders.height_map
    trans_2d(terrain_height, map_name)
    visibility = obs.observation.feature_layer_data.minimap_renders.visibility_map
    trans_2d(visibility, map_name)
    visibility = obs.observation.raw_data.map_state.visibility
    trans_2d(visibility, map_name)
    trans_units(obs.observation.raw_data.units, map_name)
    trans_effects(obs.observation.raw_data.effects, map_name)
    trans_actions(obs.actions, map_name)
  else:
    raise KeyError('obs.observation has no feature_minimap or feature_layer_data!')
  return obs

def trans_2d(map2d, map_name):
  map_name = map_name_transform(map_name)
  playable_area = MAP_PLAYABLE_AREA_DICT[map_name]
  reflect_point = MapReflectPoint[map_name]
  map2d_array = bitmap2array(map2d).copy()
  playable = map2d_array[playable_area[0][1]:playable_area[1][1],
                         playable_area[0][0]:playable_area[1][0]]
  if reflect_point[0] is not None:
    playable = np.fliplr(playable)
  if reflect_point[1] is not None:
    playable = np.flipud(playable)
  map2d_array[playable_area[0][1]:playable_area[1][1],
              playable_area[0][0]:playable_area[1][0]] = playable
  map2d_new = map2d_array.astype(np.uint8).tobytes()
  map2d.data = map2d_new

def trans_units(units, map_name):
  for u in units:
    replace_loc(u.pos, map_name)
    if len(u.orders) != 0:
      for u_order in u.orders:
        if u_order.HasField('target_world_space_pos'):
          pb_tar_loc = u_order.target_world_space_pos
          replace_loc(pb_tar_loc, map_name)

def trans_effects(effects, map_name):
  for e in effects:
    for p in e.pos:
      replace_loc(p, map_name)

def trans_actions(actions, map_name):
  raw_actions = [a.action_raw for a in actions if a.HasField('action_raw')]
  if len(raw_actions) > 0:
    for a in actions:
      if a.HasField('action_raw'):
        raw_action = a.action_raw
        cmd = raw_action.unit_command
        if cmd.HasField('target_world_space_pos'):
          if cmd.ability_id in z_pos_ab_map:
            pb_tar_loc = cmd.target_world_space_pos
            replace_loc(pb_tar_loc, map_name)

def replace_loc(loc, map_name):
  map_name = map_name_transform(map_name)
  reflect_point = MapReflectPoint[map_name]
  if reflect_point[0] is not None:
    loc.x = 2 * reflect_point[0] - loc.x
  if reflect_point[1] is not None:
    loc.y = 2 * reflect_point[1] - loc.y