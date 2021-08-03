from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np
from pysc2.lib.typeenums import UNIT_TYPEID
from timitate.utils.const import IDEAL_BASE_POS_DICT, IDEAL_BASE_POS_CROP_DICT
from pysc2.lib.features import MINIMAP_FEATURES, MinimapFeatures
from pysc2.lib import named_array


def norm_img(img):
  _max = np.max(img)
  return np.array(img, np.float32) if _max <= 1.0 else np.array(img/_max, dtype=np.float32)


def bitmap2array(image):
  bit_image_dtypes = {
    1: np.uint8,
    8: np.uint8,
    16: np.uint16,
    32: np.int32,
  }
  # array = np.array([a for a in image.data])
  data = np.frombuffer(image.data, bit_image_dtypes[image.bits_per_pixel])
  if image.bits_per_pixel == 1:
    data = np.unpackbits(data)
    if data.shape[0] != image.size.x * image.size.y:
      # This could happen if the correct length isn't a multiple of 8, leading
      # to some padding bits at the end of the string which are incorrectly
      # interpreted as data.
      data = data[:image.size.x * image.size.y]
  array = np.reshape(data, (image.size.y, image.size.x))
  return array


def _get_minimaps(obs):
  # required game version >= 4.8.2, so we get all the maps from minimap
  def or_zeros(layer, size):
    if layer is not None:
      return layer.astype(np.int32, copy=False)
    else:
      return np.zeros((size.y, size.x), dtype=np.int32)
  if hasattr(obs.observation, 'feature_minimap'):
    return obs.observation.feature_minimap
  elif hasattr(obs.observation, 'feature_layer_data'):
    feature_minimap = named_array.NamedNumpyArray(
      np.stack(
        or_zeros(f.unpack(obs.observation),
                 obs.observation.feature_layer_data.minimap_renders.creep.size)
        for f in MINIMAP_FEATURES),
      names=[MinimapFeatures, None, None])
    return feature_minimap
  else:
    raise KeyError('obs.observation has no feature_minimap or feature_layer_data!')


def type2index():
  type_map, i = {}, 0
  for tys in UNIT_TYPEID:
    if str(tys).startswith(("UNIT_TYPEID.ZERG_", "UNIT_TYPEID.NEUTRAL_")):
      type_map[tys.value] = i
      i += 1
  return type_map


def find_nearest_KJ_base(pos, crop=False):
  def _dist(pos_1, pos_2):
    return abs(pos_1[0] - pos_2[0]) + abs(pos_1[1] - pos_2[1])
  base_pos = IDEAL_BASE_POS_CROP_DICT['KairosJunction']\
    if crop else IDEAL_BASE_POS_DICT['KairosJunction']
  d = [_dist(pos, p) for p in base_pos]
  return np.argmin(d)


def find_nearest_base(pos, map_name, crop=False):
  def _dist(pos_1, pos_2):
    return abs(pos_1[0] - pos_2[0]) + abs(pos_1[1] - pos_2[1])
  idea_base_pos_dict = IDEAL_BASE_POS_CROP_DICT if crop else IDEAL_BASE_POS_DICT
  if map_name not in idea_base_pos_dict:
    print('WARN in find_nearest_base: map {} not in known map_dict. Use KJ map ideal pos.'.format(map_name))
    map_name = 'KairosJunction'
  d = [_dist(pos, p) for p in idea_base_pos_dict[map_name]]
  return np.argmin(d)


def find_unit_by_tag(tag, units):
  for u in units:
    if u.tag == tag:
      return u
  return None


def find_action_pos(action, last_units):
  """find the position (x, y) for the ability id.

  Can be its own or its target's or its executor's coordinate"""
  # can get its own position?
  x, y = (action.action_raw.unit_command.target_world_space_pos.x,
          action.action_raw.unit_command.target_world_space_pos.y)
  if x + y > 0.01:
    return x, y
  # can get its target's position?
  target_unit = find_unit_by_tag(
    action.action_raw.unit_command.target_unit_tag, last_units)
  if target_unit is not None:
    return target_unit.pos.x, target_unit.pos.y
  # can get its executor's position?
  executor_unit = find_unit_by_tag(action.action_raw.unit_command.unit_tags[0],
                                   last_units)
  if executor_unit is not None:
    return executor_unit.pos.x, executor_unit.pos.y
  raise ValueError('failed finding position')


def find_unit_pos(unit):
  return unit.pos.x, unit.pos.y


def get_player_info_by_player_id(replay_info, player_id):
  for pinfo in replay_info.player_info:
    if pinfo.player_info.player_id == player_id:
      return pinfo
  raise ValueError('invalid player_id {}'.format(player_id))


class CoorSys:
  def __init__(self, r_max=176, c_max=200):
    self.map_r_max = r_max
    self.map_c_max = c_max

  def loc_to_xy(self, loc):
    r, c = self.loc_to_rc(loc)
    x, y = self.rc_to_xy(r, c)
    return x, y

  def xy_to_loc(self, x, y):
    r, c = self.xy_to_rc(x, y)
    loc = self.rc_to_loc(r, c)
    return loc

  def loc_to_rc(self, loc):
    r = loc // self.map_c_max
    # mod operator % can be problematic for gpu pre-fetching
    # c = loc % self.map_c_max
    c = loc - self.map_c_max * r
    return r, c

  def rc_to_loc(self, r, c):
    loc = r * self.map_c_max + c
    return loc

  def xy_to_rc(self, x, y):
    r = self.map_r_max - 1 - y
    c = x
    return r, c

  def rc_to_xy(self, r, c):
    x = c
    y = self.map_r_max - 1 - r
    return x, y


def zero_one_array_to_int(x):
  """convert np array (each entry 0 or 1) to an integer

  code modified from
  https://stackoverflow.com/questions/15505514/binary-numpy-array-to-list-of-integers
  https://stackoverflow.com/questions/4065737/python-numpy-convert-list-of-bools-to-unsigned-int?answertab=active#tab-top
  """
  return sum(int(1<<i) for i, b in enumerate(x[::-1]) if b)


def map_name_transform(map_name):
  """transform map_name in replay_info to map_name used in pysc2

  Remove the trailing 'LE' and spaces and quote '
  Some Chinese map names"""
  if any(['\u4e00' <= _char <= '\u9fa5' for _char in map_name]):
    return 'KairosJunction'
  words = map_name.split(' ')
  if words[-1] == 'LE':
    words = words[:-1]
  mn = ''.join(words)
  mn = mn.replace("'", "")
  return mn
