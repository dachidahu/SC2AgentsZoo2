import logging
from os import path
import math
import random

import numpy as np
from collections import OrderedDict
from distutils.version import LooseVersion
from arena.interfaces.sc2full_formal.zerg_obs_int import ZergUnitProg
from gym import spaces
from skimage.transform import resize
from pysc2.lib.tech_tree import TechTree
from pysc2.lib.typeenums import RACE
from pysc2.lib.features import Effects
from pysc2.lib.data_raw import get_data_raw

from timitate.base_converter import BaseConverter
from timitate.lib6.z_actions import z_ability2index, z_buff2index
from timitate.lib6.zstat_utils import BUILD_ORDER_ABILITY_CANDIDATES
from timitate.lib6.pb2zstat_converter import PB2ZStatConverterV2
from timitate.lib6.pb2zstat_converter import PB2ZStatConverterV3
from timitate.lib6.pb2zstat_converter import PB2ZStatConverterV4
from timitate.lib6.pb2zstat_converter import PB2ZStatConverterV5
from timitate.utils.const import ATTACK_FORCE
from timitate.utils.const import BUILDINGS
from timitate.utils.const import UNITS_MULTIPLIER, UNITS
from timitate.utils.const import MapReflectPoint, MapReflectPoint_CROP, MAP_PLAYABLE_AREA_DICT
from timitate.utils.utils import _get_minimaps, norm_img
from timitate.utils.utils import type2index, map_name_transform
from timitate.utils.utils import zero_one_array_to_int
from timitate.utils.rep_db import RepDBFS
from timitate.utils.rep_db import RepDBFSKeysIndex
from timitate.utils.rep_db import rep_info_to_unique_key
from timitate.utils.const import IDEAL_BASE_POS_DICT

TYPE_MAP = type2index()
ABILITY_MAP = z_ability2index
BUFF_MAP = z_buff2index
EFFECTS_USED = [Effects.BlindingCloud, Effects.CorrosiveBile,
                Effects.LurkerSpines]


def one_hot(v, depth):
  res = [0] * depth
  res[min(v, depth - 1)] = 1
  return res


def resize_img_simple(img, img_size, **kwargs):
  ori_size = img.shape
  if ori_size[0] == img_size[0] and ori_size[1] == img_size[1]:
    return img
  ori_nnz_idx = np.asarray(np.nonzero(img))
  if len(ori_size) == 3:
    resized_img = np.zeros(shape=img_size + (img.shape[-1],))
    resized_nnz_idx = np.stack([ori_nnz_idx[0, :] * img_size[0] / ori_size[0],
                                ori_nnz_idx[1, :] * img_size[1] / ori_size[1],
                                ori_nnz_idx[2, :]], axis=0)
  else:
    resized_img = np.zeros(shape=img_size)
    resized_nnz_idx = np.stack([ori_nnz_idx[0, :] * img_size[0] / ori_size[0],
                                ori_nnz_idx[1, :] * img_size[1] / ori_size[1]],
                               axis=0)
  for i in range(np.shape(ori_nnz_idx)[-1]):
    idx = ori_nnz_idx[:, i]
    new_idx = resized_nnz_idx[:, i]
    if len(ori_size) == 3:
      resized_img[int(new_idx[0]), int(new_idx[1]), int(new_idx[2])] = img[
        idx[0], idx[1], idx[2]]
    else:
      resized_img[int(new_idx[0]), int(new_idx[1])] = img[idx[0], idx[1]]
  return resized_img


# tried cv2; cv2 needs an image it defines...
def resize_img_skimage(img, img_size, order=0, **kwargs):
  return np.asarray(resize(img, img_size, anti_aliasing=False, order=order))


resize_img = resize_img_skimage


class FeatMaker(BaseConverter):
  _space = None
  _tensor_names = []

  def make(self, **k_args):
    return None

  @property
  def space(self):
    return self._space

  @property
  def tensor_names(self):
    return self._tensor_names


class UnitsFeatMaker(FeatMaker):
  def __init__(self, max_units, rc_size, reorder_units=False,
               add_cargo_to_units=False, game_version='4.10.0',
               dtype=np.float32):
    self._max_units = max_units
    self._dtype = dtype
    self._rc_size = rc_size
    self._reorder_units = reorder_units
    self._add_cargo_to_units = add_cargo_to_units
    self._unit_attr_dict = self._get_unit_type_attributes(game_version)
    self._space = spaces.Tuple([
      spaces.Box(low=0, high=0, shape=(self._max_units,
                 335 + len(BUILD_ORDER_ABILITY_CANDIDATES)), dtype=self._dtype),  # dense
      spaces.Box(low=0, high=0, shape=(self._max_units, 2), dtype=self._dtype),
      # coor
      spaces.Box(low=0, high=0, shape=(self._max_units,), dtype=self._dtype),
      # buff
      spaces.Box(low=0, high=0, shape=(self._max_units,), dtype=self._dtype),
      # order
      spaces.Box(low=0, high=0, shape=(self._max_units,), dtype=self._dtype),
      # u_type
    ])
    self._tensor_names = ['X_UNIT_FEAT',
                          'X_UNIT_COOR',
                          'X_UNIT_BUFF',
                          'X_UNIT_ORDER',
                          'X_UNIT_TYPE']

  def _get_unit_type_attributes(self, game_version):
    data_raw = get_data_raw(game_version)
    unit_attr_dict = {}
    for unit in data_raw.units:
      attrs = np.zeros((13,))
      attrs[[attr % 11 for attr in unit.attributes]] = 1
      for weapon in unit.weapons:
        # Ground = 1; Air = 2; Any = 3;
        if weapon.type == 1:
          attrs[-2] = 1
        elif weapon.type == 2:
          attrs[-1] = 1
        elif weapon.type == 3:
          attrs[-2:] = 1
        else:
          print('Warning: weapon.type not defined!')
      unit_attr_dict[unit.unit_id] = attrs
    return unit_attr_dict

  def order_pb_units(self, pb_units):
    # TODO: this func should not be used currently. Many other
    ##  usage of pb[0].units remain the raw order. pb should be replaced
    self_units = []
    enemy_units = []
    other_units = []
    for u in pb_units:
      if u.alliance == 1:
        self_units.append(u)
      elif u.alliance == 4:
        enemy_units.append(u)
      else:
        other_units.append(u)
    # shuffle allows possibility to see everything
    random.shuffle(enemy_units)
    random.shuffle(self_units)
    random.shuffle(other_units)
    return enemy_units+self_units+other_units

  def make(self, pb, last_tar_tag, last_selected_unit_tags):
    map_ori_size = (pb[0].observation.raw_data.map_state.creep.size.x,
                    pb[0].observation.raw_data.map_state.creep.size.y)
    cargo_units = []
    if self._add_cargo_to_units:
      for u in pb[0].observation.raw_data.units:
        cargo_units.extend(self._extract_cargo_u(u, last_tar_tag, map_ori_size,
                                                 last_selected_unit_tags))
    # order units from player 1's view (pb[0])
    if self._reorder_units:
      ordered_pb_units = self.order_pb_units(pb[0].observation.raw_data.units)
    else:
      ordered_pb_units = pb[0].observation.raw_data.units
    if len(ordered_pb_units) > self._max_units:
      ordered_pb_units = ordered_pb_units[:self._max_units+1]  # +1 for printing WARN
    # features, coors, buff_type, order_type, unit_type for each entry
    u_entries = [self._extract_u(u, last_tar_tag, map_ori_size, last_selected_unit_tags) for u in
                 ordered_pb_units]
    b_arrays = [np.stack(b) for b in zip(*u_entries, *cargo_units)]
    n = self._max_units - b_arrays[0].shape[0]
    if n < 0:
      print("WARN: number of units exceeds the max unit length. Abandon the rest.")
      b_arrays = [b[0:self._max_units] for b in b_arrays]
    else:
      b_arrays = [
        np.pad(b, [(0, n), (0, 0)], 'constant') if len(b.shape) == 2 else
        np.pad(b, [0, n], 'constant') for b in b_arrays]  # super stupid bug by lxhan! extremely harmful to previous training!
    res = tuple([np.asarray(b.squeeze(), dtype=self._dtype) for b in b_arrays])
    return self._check_space(res)

  def _extract_cargo_u(self, u, last_tar_tag, map_ori_size, last_selected_unit_tags):
    ori_x, ori_y = map_ori_size
    coors = [u.pos.x * self._rc_size[1] / ori_x,
             u.pos.y * self._rc_size[0] / ori_y]
    coor_x = [int(i) for i in '{0:09b}'.format(int(u.pos.x * 2))]
    coor_y = [int(i) for i in '{0:09b}'.format(int(u.pos.y * 2))]
    ret = []
    for v in u.passengers:
      features = []
      features.extend(self._unit_attr_dict[v.unit_type])
      alliance = [0] * 4
      # v hasn't alliance attribute
      alliance[u.alliance - 1] = 1
      features.extend(alliance)
      features.append(v.health / v.health_max if v.health_max > 0 else 0)
      features.extend(
        one_hot(v=int(pow(min(v.health, 1500), 0.5)),
                depth=int(pow(1500, 0.5))))
      features.append(v.energy / v.energy_max if v.energy_max > 0 else 0)
      features.extend(
        one_hot(v=int(pow(min(v.energy, 200), 0.5)), depth=int(pow(200, 0.5))))
      features.extend(one_hot(v=0, depth=9))
      features.extend(one_hot(v=0, depth=9))
      features.extend(one_hot(v=0, depth=9))
      features.append(0)
      features.extend(coor_x)
      features.extend(coor_y)
      features.extend([0]*11)
      # is_in_cargo
      features.append(1)
      features.extend(one_hot(v=0, depth=19))
      features.extend(one_hot(v=0, depth=26))

      features.extend([0]*2)
      features.extend(one_hot(v=0, depth=24))
      features.extend(one_hot(v=0, depth=17))
      features.extend(one_hot(v=0, depth=32))
      features.extend(one_hot(v=0, depth=9))
      features.extend(one_hot(v=0, depth=4))
      features.extend(one_hot(v=0, depth=4))
      features.extend(one_hot(v=0, depth=32))
      features.extend(one_hot(v=0, depth=32))
      features.append(0)

      if last_selected_unit_tags is None:
        features.append(0)
      else:
        features.append(v.tag in last_selected_unit_tags)
      features.append(v.tag == last_tar_tag)
      features.extend([0]*(len(BUILD_ORDER_ABILITY_CANDIDATES)+2))
      if v.unit_type not in TYPE_MAP:
        unit_type = len(TYPE_MAP)
      else:
        unit_type = TYPE_MAP[v.unit_type]
      ret.append([np.array(features, dtype=self._dtype),
                  np.array(coors, dtype=self._dtype),
                  np.array(0, dtype=self._dtype),
                  np.array(len(ABILITY_MAP), dtype=self._dtype),
                  np.array(unit_type, dtype=self._dtype)])

    return ret

  def _extract_u(self, u, last_tar_tag, map_ori_size, last_selected_unit_tags):
    # Below are dense features
    features = []

    features.extend(self._unit_attr_dict[u.unit_type])

    alliance = [0] * 4
    alliance[u.alliance - 1] = 1
    features.extend(alliance)

    features.append(u.health / u.health_max if u.health_max > 0 else 0)
    features.extend(
      one_hot(v=int(pow(min(u.health, 1500), 0.5)), depth=int(pow(1500, 0.5))))
    features.append(u.energy / u.energy_max if u.energy_max > 0 else 0)
    features.extend(
      one_hot(v=int(pow(min(u.energy, 200), 0.5)), depth=int(pow(200, 0.5))))

    # TODO: is the cargo space of nydus network unlimited?
    # features.append(u.cargo_space_taken / float(u.cargo_space_max) if u.cargo_space_max > 0 else 0)
    features.extend(one_hot(v=int(u.cargo_space_taken), depth=9))
    features.extend(one_hot(v=int(u.cargo_space_max), depth=9))
    features.extend(one_hot(v=int(math.sqrt(len(u.passengers))), depth=9))

    features.append(u.build_progress)

    coor_x = [int(i) for i in '{0:09b}'.format(
      int(u.pos.x * 2))]  # binary encoding and 2x resolution
    coor_y = [int(i) for i in '{0:09b}'.format(int(u.pos.y * 2))]
    features.extend(coor_x)
    features.extend(coor_y)

    # AStar did not use the following 4 features
    # features.append(u.facing / 3.1415 / 2.0)
    # features.append(u.radius / 3.0)
    # features.append(u.detect_range / 10.0)
    # features.append(u.radar_range / 10.0)

    cloak_state = [0] * 5
    cloak_state[u.cloak] = 1
    features.extend(cloak_state)

    features.append(int(u.is_powered))
    features.append(int(u.is_active))
    features.append(int(u.is_flying))
    features.append(int(u.is_burrowed))
    features.append(int(u.is_hallucination))
    features.append(int(u.is_blip))
    # is_in_cargo
    features.append(0)

    features.extend(one_hot(v=int(u.mineral_contents / 100.0), depth=19))
    features.extend(one_hot(v=int(u.vespene_contents / 100.0), depth=26))

    features.append(u.assigned_harvesters / float(
      u.ideal_harvesters) if u.ideal_harvesters > 0 else 0)
    features.append(1 if u.assigned_harvesters > u.ideal_harvesters > 0 else 0)
    features.extend(one_hot(v=int(u.assigned_harvesters), depth=24))
    features.extend(one_hot(v=int(u.ideal_harvesters), depth=17))

    features.extend(one_hot(v=int(u.weapon_cooldown), depth=32))

    # features.append(pb_unit.add_on_tag)

    features.extend(one_hot(v=len(u.orders), depth=9))
    features.extend(one_hot(v=u.attack_upgrade_level, depth=4))
    features.extend(one_hot(v=u.armor_upgrade_level, depth=4))
    # features.append(u.shield_upgrade_level)  # useless for zerg
    features.extend(one_hot(v=u.buff_duration_remain, depth=32))
    features.extend(one_hot(v=u.buff_duration_max, depth=32))
    features.append(
      u.buff_duration_remain / u.buff_duration_max if u.buff_duration_max > 0 else 0)

    # is_on_screen should be used along with move_camera action
    # if self._use_on_screen:
    #     features.append(int(pb_u.is_on_screen))

    # TODO: display_type should be useful and AStar used this feature
    #  but we mistakenly removed it a long time ago (since lib1)...
    # display_type should be used along with move_camera
    # display_type = [0] * 3
    # display_type[pb_unit.display_type - 1] = 1
    # features.extend(display_type)

    # Notice: AStar like space should not use u.is_selected from game core;
    # must use whether in last selection action
    if last_selected_unit_tags is None:
      features.append(0)
    else:
      features.append(u.tag in last_selected_unit_tags)
    features.append(u.tag == last_tar_tag)
    build_order = [0] * len(BUILD_ORDER_ABILITY_CANDIDATES)
    ubop = 0
    if len(u.orders) > 0:
      uop = u.orders[0].progress
      features.append(uop)
      for order in u.orders:
        if order.ability_id in BUILD_ORDER_ABILITY_CANDIDATES:
          build_order[BUILD_ORDER_ABILITY_CANDIDATES.index(order.ability_id)] = 1
          ubop = order.progress
          break
    else:
      features.append(0)
    features.extend(build_order)
    features.append(ubop)
    # features in AlphaStar that we do not have
    # unit_attributes, current_shields, current_shield_ratio, display_type, is_on_screen
    # mined_minerals, mined_vespene, order_queue_length, order_2-4
    # addon_type, order_progress_1, order_progress_2

    # Below are id-type features; will be learned with embeddings
    # coor
    ori_x, ori_y = map_ori_size
    coors = [u.pos.x * self._rc_size[1] / ori_x,
             u.pos.y * self._rc_size[0] / ori_y]
    # buff
    buff_id = 0
    if len(u.buff_ids) > 0:
      buff_id = u.buff_ids[0]
      if buff_id not in BUFF_MAP:
        print(
          "WARN: Buff id %i not found in BUFF_ID, use as Invalid" % u.buff_ids[
            0])
        buff_id = 0
    buff_type = BUFF_MAP[buff_id]
    # the first order
    if len(u.orders) == 0 or u.orders[0].ability_id not in ABILITY_MAP:
      order_type = len(ABILITY_MAP)
    else:
      order_type = ABILITY_MAP[u.orders[0].ability_id]
    # unit type
    if u.unit_type not in TYPE_MAP:
      unit_type = len(TYPE_MAP)
    else:
      unit_type = TYPE_MAP[u.unit_type]

    return np.array(features, dtype=self._dtype), \
           np.array(coors, dtype=self._dtype), \
           np.array(buff_type, dtype=self._dtype), \
           np.array(order_type, dtype=self._dtype), \
           np.array(unit_type, dtype=self._dtype)


class ImgFeatMaker(FeatMaker):
  def __init__(self, rc_size, dtype=np.float32, game_version='4.7.1'):
    self._rc_size = rc_size
    self._dtype = dtype
    self._space = spaces.Box(low=0, high=0, shape=self._rc_size + (15,),
                             dtype=self._dtype)
    self._tensor_names = ['X_IMAGE']
    # self._flip = LooseVersion(game_version) >= LooseVersion('4.8.6')
    # Only work for linux
    # pathing_grid flips before 4.8.2,
    # pathing_grid and placement_grid are reversed in y-axis after 4.8.2(include)
    # Mac flips creep/visibility from 4.9.0, pathing/placement from 4.8.6
    self._flip = (game_version not in ['4.7.1', '4.8.0'])

  def make(self, pb, last_units):
    assert self._flip, "4.7.1/4.8.0 are not supported any more!"
    obs, game_info = pb
    feature_minimap = _get_minimaps(obs)
    # visibility0 = np.equal(visibility_map, 0)  # Hidden
    visibility1 = np.equal(feature_minimap.visibility_map, 1)  # Fogged
    visibility2 = np.equal(feature_minimap.visibility_map, 2)  # Visible
    visibility3 = np.equal(feature_minimap.visibility_map, 3)  # FullHidden
    # 0: self, 1: neutral, 2: enemy
    alliance_grid0 = feature_minimap.player_relative == 1
    alliance_grid1 = feature_minimap.player_relative == 3
    alliance_grid2 = feature_minimap.player_relative == 4
    y, x = visibility1.shape

    engage_grid = np.zeros((y, x), dtype=self._dtype)
    for unit in obs.observation.raw_data.units:
      # self units has engaged_target_tag when combat (checked 4.7.1)
      engage_grid[y - 1 - int(unit.pos.y), int(
        unit.pos.x)] = 1.0 if unit.engaged_target_tag else 0.0

    # hand-craft alerts (checked 4.7.1, do not affect speed much)
    # alerts_grid = np.zeros((y, x), dtype=self._dtype)
    # if last_units is not None:
    #   tag2idx = dict([(unit.tag, i) for i, unit in
    #                   enumerate(obs.observation.raw_data.units)])
    #   last_tag2idx = dict([(unit.tag, i) for i, unit in enumerate(last_units)])
    #   for last_tag in last_tag2idx:
    #     if last_tag in tag2idx:
    #       unit = obs.observation.raw_data.units[tag2idx[last_tag]]
    #       last_unit = last_units[last_tag2idx[last_tag]]
    #       if unit.alliance == 1 and unit.health - last_unit.health < 0:
    #         # print("under attack alert!")
    #         unit = obs.observation.raw_data.units[tag2idx[last_tag]]
    #         alerts_grid[y - 1 - int(unit.pos.y), int(unit.pos.x)] = 1.0

    effect_grid = np.zeros((y, x, len(EFFECTS_USED)), dtype=self._dtype)
    for e in obs.observation.raw_data.effects:
      if e.effect_id in EFFECTS_USED:
        ind = EFFECTS_USED.index(e.effect_id)
        for p in e.pos:
          effect_grid[y - 1 - int(p.y), int(p.x), ind] = 1.0


    image_features = (norm_img(feature_minimap.height_map),
                      norm_img(feature_minimap.pathable),
                      norm_img(feature_minimap.buildable),
                      norm_img(feature_minimap.creep),
                      norm_img(visibility1),
                      norm_img(visibility2),
                      norm_img(visibility3),
                      norm_img(alliance_grid0),
                      norm_img(alliance_grid1),
                      norm_img(alliance_grid2),
                      norm_img(engage_grid),
                      norm_img(feature_minimap.alerts),
                      norm_img(effect_grid))

    # if use_alerts_feature:
    #   if hasattr(obs.observation, 'feature_minimap'):
    #     alerts_grid = obs.feature_minimap.alerts
    #   elif hasattr(obs.observation, 'feature_layer_data'):
    #     alerts_grid = obs.observation.feature_layer_data.minimap_renders.alerts
    #     alerts_grid = bitmap2array(alerts_grid)
    #   else:
    #     raise KeyError
    #   image_features += (alerts_grid,)

    # features in AlphaStar that we do not have
    # camera

    ## for debug
    # debug_names = ('height', 'pathable',
    #                'buildable', 'creep',
    #                'vis1', 'vis2', 'vis3',
    #                'alliance1', 'alliance2',
    #                'alliance3', 'engage',
    #                'alerts', 'effect1',
    #                'effect2', 'effect3')
    # import matplotlib.pyplot as plt
    # plt.imshow(cmd_pos_mask[ab_action, :, :])
    # plt.show()
    # input("press to close")
    # plt.close()
    # from PIL import Image
    # for i in range(len(debug_names)):
    #   array = np.array(np.dstack(image_features)[:, :, i]*255, dtype=np.int8)
    #   im = Image.fromarray(array, mode='L')
    #   im = im.convert('RGB')
    #   im.save(debug_names[i]+'.jpg')

    res = resize_img(np.dstack(image_features), img_size=self._rc_size).astype(
      self._dtype)
    return self._check_space(res)


class PositionalEncoding(object):
  def __init__(self, d_model):
    self.d_model = d_model
    self.div_term = np.power(10000, -np.arange(0, d_model, 2) / d_model)

  def encode(self, pos):
    pe = np.zeros(self.d_model)
    pe[0::2] = np.sin(pos * self.div_term)
    pe[1::2] = np.cos(pos * self.div_term)
    return pe


class GlobalFeatMaker(FeatMaker):
  def __init__(self, game_version, dtype=np.float32):
    self._tech_tree = TechTree()
    self._tech_tree.update_version(game_version)
    self._upgrades = self._zerg_upgrades()
    self._buildings = self._zerg_buildings()
    self._zerg_unitprog_func = ZergUnitProg(self._tech_tree, True, None,
                                            self._buildings, self._upgrades)
    self._dtype = dtype
    self._pe = PositionalEncoding(64)
    self._space = spaces.Tuple([
      # player_feat
      spaces.Box(low=0, high=0, shape=(10,), dtype=self._dtype),
      # upgrade_feat
      spaces.Box(low=0, high=0, shape=(28,), dtype=self._dtype),
      # game_progress
      spaces.Box(low=0, high=0, shape=(64,), dtype=self._dtype),
      # self_count_feat
      spaces.Box(low=0, high=0, shape=(len(UNITS+BUILDINGS),), dtype=self._dtype),
      # enemy_count_feat
      spaces.Box(low=0, high=0, shape=(len(UNITS+BUILDINGS),), dtype=self._dtype),
      # attack_flying_counts
      spaces.Box(low=0, high=0, shape=(4,), dtype=self._dtype),
      # building/tech progress
      spaces.Box(low=0, high=0, shape=(92,), dtype=self._dtype),
      # cumulative_score
      spaces.Box(low=0, high=0, shape=(12,), dtype=self._dtype),
    ])
    self._tensor_names = ['X_VEC_PLAYER_STAT',
                          'X_VEC_UPGRADE',
                          'X_VEC_GAME_PROG',
                          'X_VEC_S_UNIT_CNT',
                          'X_VEC_E_UNIT_CNT',
                          'X_VEC_AF_UNIT_CNT',
                          'X_VEC_PROG',
                          'X_VEC_SCORE']

  def _zerg_upgrades(self):
    upgrade_list = []
    for upgrade in self._tech_tree.m_upgradeData:
      if self._tech_tree.m_upgradeData[upgrade].race == RACE.Zerg:
        upgrade_list.append(upgrade)
    return sorted(upgrade_list)

  def _zerg_buildings(self):
    building_list = []
    for unit_type in sorted(self._tech_tree.m_unitTypeData.keys()):
      data = self._tech_tree.m_unitTypeData[unit_type]
      if data.race == RACE.Zerg and data.isBuilding:
        building_list.append(unit_type)
    return sorted(building_list)

  def make(self, pb):
    obs_pb, game_info_pb = pb
    # player stat: log process
    player_feat = [math.log(obs_pb.observation.player_common.minerals + 1),
                   math.log(obs_pb.observation.player_common.vespene + 1),
                   math.log(obs_pb.observation.player_common.food_cap + 1),
                   math.log(obs_pb.observation.player_common.food_used + 1),
                   obs_pb.observation.player_common.food_cap -
                   obs_pb.observation.player_common.food_used <= 0,
                   math.log(obs_pb.observation.player_common.food_army + 1),
                   math.log(obs_pb.observation.player_common.food_workers + 1),
                   math.log(
                     obs_pb.observation.player_common.idle_worker_count + 1),
                   math.log(obs_pb.observation.player_common.army_count + 1),
                   math.log(obs_pb.observation.player_common.larva_count + 1),
                   # math.log(obs_pb.observation.game_loop + 1),
                   ]

    # upgraded techs
    # TODO: how to get enemy upgrades?
    upgrade_feat = [0] * len(self._upgrades)
    for upgrade in obs_pb.observation.raw_data.player.upgrade_ids:
      if upgrade in self._upgrades:
        upgrade_feat[self._upgrades.index(upgrade)] = 1

    # pyramid one-hot for game progress
    # def _onehot(value, n_bins):
    #   bin_width = 43200 // n_bins
    #   features = [0] * n_bins
    #   idx = int(value // bin_width)
    #   idx = n_bins - 1 if idx >= n_bins else idx
    #   features[idx] = 1.0
    #   return features
    #
    # game_progress = _onehot(obs_pb.observation.game_loop, 45) + \
    #                 _onehot(obs_pb.observation.game_loop, 15) + \
    #                 _onehot(obs_pb.observation.game_loop, 9) + \
    #                 _onehot(obs_pb.observation.game_loop, 5)
    game_progress = self._pe.encode(obs_pb.observation.game_loop / 22.4)

    # unit counts
    def _get_counts(units):
      count = {t: 0 for t in UNITS + BUILDINGS}
      for u in units:
        if u.unit_type in count:
          count[u.unit_type] += 1
        for passenger in u.passengers:
          count[passenger.unit_type] += 1
      for t in count.keys():
        # sqrt process
        count[t] = math.sqrt(count[t])
      return [count[t] for t in UNITS + BUILDINGS]

    self_units = [u for u in obs_pb.observation.raw_data.units
                  if u.alliance == 1]
    enemy_units = [u for u in obs_pb.observation.raw_data.units
                   if u.alliance == 4]
    self_count_feat = _get_counts(self_units)
    enemy_count_feat = _get_counts(enemy_units)

    # attack_air, attack_ground, is_flying, is_on_ground
    n_enemy_is_flying, n_enemy_is_on_ground = 0, 0
    for u in enemy_units:
      if u.unit_type in UNITS_MULTIPLIER:
        if u.is_flying:
          n_enemy_is_flying += UNITS_MULTIPLIER[u.unit_type]
        else:
          n_enemy_is_on_ground += UNITS_MULTIPLIER[u.unit_type]

    n_can_attack_air, n_can_attack_ground = 0, 0
    for u in self_units:
      if u.unit_type in UNITS_MULTIPLIER and u.unit_type in ATTACK_FORCE:
        if ATTACK_FORCE[u.unit_type].can_attack_ground:
          n_can_attack_ground += UNITS_MULTIPLIER[u.unit_type]
        if ATTACK_FORCE[u.unit_type].can_attack_air:
          n_can_attack_air += UNITS_MULTIPLIER[u.unit_type]

    attack_flying_counts = [math.sqrt(n_enemy_is_flying),
                            math.sqrt(n_enemy_is_on_ground),
                            math.sqrt(n_can_attack_air),
                            math.sqrt(n_can_attack_ground)]

    # features = player_feat + upgrade_feat + game_progress + self_count_feat + \
    #     enemy_count_feat + attack_flying_counts
    # features = [np.array(features, dtype=self._dtype)]

    # if self._use_score_feature:
    #   features.append(self.score_feature(obs_pb.observation.score))

    progress = self._zerg_unitprog_func.observation_transform(None, obs_pb)
    # features.append(progress[0])

    score_details = obs_pb.observation.score.score_details
    scores = [math.log(score_details.idle_production_time + 1),
              math.log(score_details.idle_worker_time + 1),
              math.log(score_details.total_value_units + 1),
              math.log(score_details.total_value_structures + 1),
              math.log(score_details.killed_value_units + 1),
              math.log(score_details.killed_value_structures + 1),
              math.log(score_details.collected_minerals + 1),
              math.log(score_details.collected_vespene + 1),
              math.log(score_details.collection_rate_minerals + 1),
              math.log(score_details.collection_rate_vespene + 1),
              math.log(score_details.spent_minerals + 1),
              math.log(score_details.spent_vespene + 1),
              ]

    # features in AlphaStar that we do not have
    # race, mmr, last_repeat_queued

    # available_actions is given in our mask and input to the policy
    # last_delay and last_action_type have been input to the policy as la

    # AlphaStar creates many small nets for each type of these global features,
    # so they should not be concatenated here
    # res = np.concatenate(features)
    res = (np.array(player_feat, dtype=self._dtype),
           np.array(upgrade_feat, dtype=self._dtype),
           np.array(game_progress, dtype=self._dtype),
           np.array(self_count_feat, dtype=self._dtype),
           np.array(enemy_count_feat, dtype=self._dtype),
           np.array(attack_flying_counts, dtype=self._dtype),
           np.array(progress[0], dtype=self._dtype),
           np.array(scores, dtype=self._dtype),
           )
    return self._check_space(res)


class CargoFeatMaker(FeatMaker):
  def __init__(self, max_cargo_num, dtype):
    self._max_cargo_num = max_cargo_num
    self._dtype = dtype
    self._space = spaces.Tuple([
      spaces.Box(low=0, high=0, shape=(self._max_cargo_num,),
                 dtype=self._dtype),
      spaces.Box(low=0, high=0, shape=(self._max_cargo_num, 56),
                 dtype=self._dtype),
    ])
    self._tensor_names = ['X_CARGO_MASK',
                          'X_CARGO']

  def make(self, pb):
    def _extract_cargo_feat_per_unit(u):
      features = []
      if u.unit_type not in TYPE_MAP:
        features.append(len(TYPE_MAP))
      else:
        features.append(TYPE_MAP[u.unit_type])
      features.append(u.build_progress)
      features.append(u.health / u.max_health if u.max_health > 0 else 0)
      features.extend(one_hot(v=int(pow(min(u.health, 1500), 0.5)),
                              depth=int(pow(1500, 0.5))))
      features.append(u.energy / u.max_energy if u.max_energy > 0 else 0)
      features.extend(
        one_hot(v=int(pow(min(u.energy, 200), 0.5)), depth=int(pow(200, 0.5))))
      res = np.array(features, dtype=self._dtype)
      return res

    unit_feat_list = [_extract_cargo_feat_per_unit(pb_unit)
                      for pb_unit in pb[0].observation.ui_data.cargo.passengers]
    n = len(unit_feat_list)
    mask = np.zeros(shape=(self._max_cargo_num,), dtype=self._dtype)
    if n > 0:
      mask[0:n] = 1.0
      cargo_features = np.stack(unit_feat_list)
      if n > self._max_cargo_num:
        cargo_features = cargo_features[0:self._max_cargo_num, :]
      else:
        cargo_features = np.pad(cargo_features,
                                [(0, self._max_cargo_num - n), (0, 0)],
                                'constant')
    else:
      cargo_features = np.zeros(shape=self.space.spaces[1].shape,
                                dtype=self._dtype)
    res = mask, cargo_features
    return self._check_space(res)


class TargetZStatMaker(FeatMaker):
  """Z Statistics Maker. See AlphaStar Nature paper.

  Presume the zstat has been pre-saved in a db specified by a data_src path.
  """
  IND_UNIT_COUNT = 0
  IND_BUILD_ORDER = 1
  IND_BUILD_ORDER_COORD = 2
  IND_BUILD_ORDER_BUILD_TECH = 3
  IND_BUILD_ORDER_BUILD_TECH_COORD = 4

  def __init__(self, zstat_data_src='', max_bo_count=100, max_bobt_count=100,
               dtype=np.float32, zstat_version='v3', crop=False):
    self.zstat_db = self._create_db(zstat_data_src, name='zstat')
    self.zstat_keys_index = self._create_ki(zstat_data_src)
    self._max_bo_count = max_bo_count
    self._max_bobt_count = max_bobt_count
    self._zstat_db_keys = None
    self._zstat_db_keys_fms = None  # filtered by map_name, start_pos
    self._zstat = None
    self._dtype = dtype
    self._zstat_version = zstat_version
    self._crop = crop
    if zstat_version == 'v5':
      self._cvt = PB2ZStatConverterV5(max_bo_count=max_bo_count,
                                      max_bobt_count=max_bobt_count)
    elif zstat_version == 'v4':
      self._cvt = PB2ZStatConverterV4(max_bo_count=max_bo_count,
                                      max_bobt_count=max_bobt_count)
    elif zstat_version == 'v3':
      self._cvt = PB2ZStatConverterV3(max_bo_count=max_bo_count)
    elif zstat_version == 'v2':
      self._cvt = PB2ZStatConverterV2(max_bo_count=max_bo_count)
    else:
      raise NotImplemented('Unknown zstat version.')
    self._space = self._cvt.space
    self._tensor_names = self._cvt.tensor_names

  def reset(self, replay_name: str, player_id: str, map_name: str,
            start_pos: tuple=None, zstat_zeroing_prob: float=0.0):
    # shorter names
    i_uc = TargetZStatMaker.IND_UNIT_COUNT
    i_bo = TargetZStatMaker.IND_BUILD_ORDER
    i_bo_coord = TargetZStatMaker.IND_BUILD_ORDER_COORD
    i_bobt = TargetZStatMaker.IND_BUILD_ORDER_BUILD_TECH
    i_bobt_coord = TargetZStatMaker.IND_BUILD_ORDER_BUILD_TECH_COORD

    # simply query by replay_name + player_id
    key = rep_info_to_unique_key(replay_name, player_id)
    logging.info('ZStatMaker: use key {}'.format(key))
    self._zstat = self.zstat_db.get(key)
    if self._zstat is None:
      # for debug with 'v3' zstat
      # self._zstat = [np.zeros((80,)), np.zeros((50,62)), np.zeros((50,18))]
      raise IOError(
        'db {}, failed reading data from replay_name {}, player_id {}'.format(
          self.zstat_db, replay_name, player_id)
      )

    # post-processing
    # numeric scaling for unit count
    self._zstat[i_uc] = np.sqrt(self._zstat[i_uc])
    # set build order (build tech) by desired length
    self._zstat[i_bo] = self._zstat[i_bo][:self._max_bo_count, ]
    self._zstat[i_bo_coord] = self._zstat[i_bo_coord][:self._max_bo_count, ]
    if self._zstat_version in ['v4', 'v5']:
      self._zstat[i_bobt] = self._zstat[i_bobt][:self._max_bobt_count, ]
      self._zstat[i_bobt_coord] = self._zstat[
                                    i_bobt_coord][:self._max_bobt_count, ]

    def _manipulate_coord(coord_array, real_count, reflect, crop):
      """reflect, crop the coordinates when necessary"""
      if not reflect and not crop:
        # do nothing, return as-is
        return coord_array
      ref_x, ref_y = (MapReflectPoint_CROP[map_name] if crop
                      else MapReflectPoint[map_name])
      _, n_digits = coord_array.shape
      n_digits /= 2  # for (x, y) respectively
      # TODO(pengsun): function for bin/decimal converting
      assert n_digits == 9
      for i in range(int(real_count)):
        # binary string to decimal with x(1/2) resolution
        x, y = coord_array[i, 0:9], coord_array[i, 9:]
        x, y = zero_one_array_to_int(x), zero_one_array_to_int(y)
        x, y = float(x) / 2, float(y) / 2
        if crop:
          x -= MAP_PLAYABLE_AREA_DICT[map_name][0][0]
          y -= MAP_PLAYABLE_AREA_DICT[map_name][0][1]
        if reflect:
          # the reflection
          if ref_x is not None:
            x = ref_x + (ref_x - x)
          if ref_y is not None:
            y = ref_y + (ref_y - y)
        # decimal to binary string with x2 resolution
        coord_array[i] = ([int(j) for j in '{0:09b}'.format(int(x * 2))] +
                          [int(j) for j in '{0:09b}'.format(int(y * 2))])
      return coord_array

    # shall we query also by map_name + start_pos and do further checking?
    should_reflect = False
    if map_name is not None and start_pos is not None:
      logging.info('ZStatMaker: checking for required map_name: {}, '
                   'start_pos: {}'.format(map_name, start_pos))
      # should reflect the coordinate?
      if self._crop:
        origin_pos = MAP_PLAYABLE_AREA_DICT[map_name][0]
        start_pos = (start_pos[0] + origin_pos[0],
                     start_pos[1] + origin_pos[1])
      tmp_keys = self.zstat_keys_index.get_keys_by_map_name_start_pos(map_name,
                                                                      start_pos)
      is_start_pos_consistent = (key in tmp_keys)
      logging.info(
        'ZStatMaker: is required start_pos consistent to the key: {}'.format(
          is_start_pos_consistent
        ))
      if not is_start_pos_consistent or self._crop:
        logging.info(f'ZStatMaker: {"not"*is_start_pos_consistent} reflect '
                     f' {"not"*(not self._crop)} crop the zstat coordinate')
        should_reflect = not is_start_pos_consistent
    else:
      logging.info(f'ZStatMaker: {"not" * (not self._crop)} crop the zstat coordinate')

    real_bo_count = np.sum(self._zstat[i_bo])  # as each row is one-hot
    self._zstat[i_bo_coord] = _manipulate_coord(self._zstat[i_bo_coord],
                                                real_bo_count, should_reflect,
                                                self._crop)
    if self._zstat_version in ['v4', 'v5']:
      real_bobt_count = np.sum(self._zstat[i_bobt])
      self._zstat[i_bobt_coord] = _manipulate_coord(self._zstat[i_bobt_coord],
                                                    real_bobt_count,
                                                    should_reflect, self._crop)

    # should zeroing?
    logging.info('ZStatMaker: zeroing_prob {}'.format(zstat_zeroing_prob))
    if random.random() < zstat_zeroing_prob:
      logging.info('ZStatMaker: perform zeroing the zstat')
      for i in range(len(self._zstat)):
        self._zstat[i].fill(0.0)
    else:
      logging.info('ZStatMaker: no zeoring the zstat, keep it as-is')

  def make(self):
    return self._check_space(tuple(self._zstat))

  def _create_db(self, data_src, name='mydata'):
    if data_src is None or not path.exists(data_src):
      logging.warning('path {} not exists, {} db disabled!'.format(
        data_src, name))
      return None
    return RepDBFS(data_src)

  def _create_ki(self, ki_path, name='keys_index'):
    if ki_path is None or not path.exists(ki_path):
      logging.warning('path {} not exists, {} key index disabled!'.format(
        ki_path, name))
      return None
    return RepDBFSKeysIndex(ki_path)


class ImmZStatMaker(FeatMaker):
  def __init__(self, max_bo_count=100, max_bobt_count=100,
               dtype=np.float32, zstat_version='v3'):
    self._max_bo_count = max_bo_count
    self._max_bobt_count = max_bobt_count
    if zstat_version == 'v5':
      self._pb2zstat_cvt = PB2ZStatConverterV5(max_bo_count=max_bo_count, max_bobt_count=max_bobt_count)
    elif zstat_version == 'v4':
      self._pb2zstat_cvt = PB2ZStatConverterV4(max_bo_count=max_bo_count, max_bobt_count=max_bobt_count)
    elif zstat_version == 'v3':
      self._pb2zstat_cvt = PB2ZStatConverterV3(max_bo_count=max_bo_count)
    elif zstat_version == 'v2':
      self._pb2zstat_cvt = PB2ZStatConverterV2(max_bo_count=max_bo_count)
    else:
      raise NotImplemented('Unknown zstat version.')
    self._pb2zstat_cvt.reset()
    self._dtype = dtype
    self._space = self._pb2zstat_cvt.space
    self._tensor_names = []
    for name in self._pb2zstat_cvt.tensor_names:
      if name.startswith('Z_'):
        self._tensor_names.append('IMM_'+name[2:])
      else:
        self._tensor_names.append('IMM_'+name)

  def make(self, pb):
    obs_pb, game_info_pb = pb
    zstat = self._pb2zstat_cvt.convert(obs_pb)
    # post-processing
    zstat[0] = np.sqrt(zstat[0])
    zstat = [a.astype(self._dtype) for a in zstat]
    return self._check_space(tuple(zstat))


class MMRMaker(FeatMaker):
  """PB to MMR. Return a one-hot vector to indicate the quantized value."""

  def __init__(self, dtype=np.float32):
    self._mmr_one_hot = None
    self._dtype = dtype
    self._space = spaces.Box(shape=(7,), low=0, high=1, dtype=np.float32)
    self._tensor_names = ['MMR']

  def reset(self, mmr):
    logging.info('using mmr {}'.format(mmr))
    self._mmr_one_hot = self._make_one_hot(mmr)

  def make(self):
    return self._check_space(self._mmr_one_hot)

  def _make_one_hot(self, mmr):
    mmr = max(mmr, 0)  # believe it or not, mmr can be negative
    quant_idx = min(int(float(mmr) / 1000.0), 6)  # can be 0, 1, ..., 5, 6
    mmr_feat = np.zeros(shape=(7,), dtype=self._dtype)
    mmr_feat[quant_idx] = 1
    return mmr_feat


class MapIndicatorMaker(FeatMaker):
  """PB to Map Indicator. Return a one-hot vector to indicate what map it is"""

  def __init__(self, allowed_map_names, dtype=np.float32):
    self.allowed_map_names = [name.lower() for name in allowed_map_names]
    self._n = len(self.allowed_map_names) + 1
    self._map_one_hot = None
    self._dtype = dtype
    self._space = spaces.Box(shape=(self._n,), low=0, high=1, dtype=np.float32)
    self._tensor_names = ['MAP_INDICATOR']

  def reset(self, map_name):
    self._map_one_hot = self._make_one_hot(map_name)

  def make(self):
    return self._check_space(self._map_one_hot)

  def _make_one_hot(self, map_name):
    vec = np.zeros(shape=(self._n,), dtype=self._dtype)
    stand_str = lambda x: str(x).lower().strip()
    loose_eq = lambda x, y: x in y or y in x
    for idx, amn in enumerate(self.allowed_map_names):
      if loose_eq(stand_str(amn), stand_str(map_name)):
        vec[idx] = 1
        break
    else:  # an unknown map
      print('WARN: unknown map {} in map one-hot maker.'.format(map_name))
      vec[-1] = 1
    return vec


class PB2FeatureConverter(BaseConverter):
  def __init__(self, dtype=np.float32,
               use_on_screen=False,
               max_unit_num=600,
               map_resolution=(200, 176),
               max_cargo_num=16,
               game_version='4.7.1',
               max_bo_count=50,
               max_bobt_count=50,
               zstat_data_src='',
               dict_space=False,
               zstat_version='v3',
               reorder_units=False,
               crop_to_playable_area=False,
               add_cargo_to_units=False):
    self._use_on_screen = use_on_screen
    self._rc_size = (map_resolution[1], map_resolution[0])
    # alerts are not available in 4.7.1, so disable by default
    # self._alerts = sc_pb.Alert.values()
    # radius/alliance are not available in 4.7.1, not added.
    # missing effects' alliance seems fine for Zerg
    self._units_feat_maker = UnitsFeatMaker(max_units=max_unit_num,
                                            rc_size=self._rc_size,
                                            reorder_units=reorder_units,
                                            add_cargo_to_units=add_cargo_to_units,
                                            game_version=game_version,
                                            dtype=dtype)
    self._img_feat_maker = ImgFeatMaker(rc_size=self._rc_size, dtype=dtype,
                                        game_version=game_version)
    self._global_feat_maker = GlobalFeatMaker(game_version=game_version,
                                              dtype=dtype)
    # self._cargo_feat_maker = CargoFeatMaker(max_cargo_num=max_cargo_num,
    #                                         dtype=dtype)
    self.immzstat_maker = ImmZStatMaker(dtype=dtype,
                                        max_bo_count=max_bo_count,
                                        max_bobt_count=max_bobt_count,
                                        zstat_version=zstat_version)
    # stationary features; only change when reset
    self.tarzstat_maker = TargetZStatMaker(
      max_bo_count=max_bo_count,
      max_bobt_count=max_bobt_count,
      zstat_data_src=zstat_data_src,
      dtype=dtype,
      zstat_version=zstat_version,
      crop = crop_to_playable_area,
    )
    self._mmr_maker = MMRMaker(dtype=dtype)
    self._map_ind_maker = MapIndicatorMaker(
      allowed_map_names=list(IDEAL_BASE_POS_DICT.keys()), dtype=dtype)

    self._dict_space = dict_space
    self._tensor_names = (self._units_feat_maker.tensor_names +
                          self._img_feat_maker.tensor_names +
                          self._global_feat_maker.tensor_names +
                          # self._cargo_feat_maker.tensor_names +
                          self.tarzstat_maker.tensor_names +
                          self._mmr_maker.tensor_names +
                          self._map_ind_maker.tensor_names +
                          self.immzstat_maker.tensor_names)

  def reset(self, replay_name, player_id, mmr, map_name, start_pos=None,
            zstat_zeroing_prob=0.0):
    map_name = map_name_transform(map_name)
    self.tarzstat_maker.reset(replay_name=replay_name, player_id=player_id,
                              map_name=map_name, start_pos=start_pos,
                              zstat_zeroing_prob=zstat_zeroing_prob)
    self._mmr_maker.reset(mmr=mmr)
    self._map_ind_maker.reset(map_name=map_name)

  def convert(self, pb, last_tar_tag, last_units, last_selected_unit_tags):
    unit_features = self._units_feat_maker.make(pb, last_tar_tag, last_selected_unit_tags)
    img_features = self._img_feat_maker.make(pb, last_units)
    global_features = self._global_feat_maker.make(pb)
    # cargo_features = self._cargo_feat_maker.make(pb)
    immzstat_features = self.immzstat_maker.make(pb)
    zstat_features = self.tarzstat_maker.make()
    mmr_features = self._mmr_maker.make()
    map_ind_features = self._map_ind_maker.make()
    feat = unit_features + (img_features,) + global_features + \
           zstat_features + (mmr_features, map_ind_features) + immzstat_features
    if self._dict_space:
      return OrderedDict(zip(self.tensor_names, feat))
    else:
      return feat

  @property
  def space(self):
    sps = (self._units_feat_maker.space.spaces +
           [self._img_feat_maker.space] +
           self._global_feat_maker.space.spaces +
           # self._cargo_feat_maker.space.spaces +
           self.tarzstat_maker.space.spaces +
           [self._mmr_maker.space] +
           [self._map_ind_maker.space] +
           self.immzstat_maker.space.spaces)
    if self._dict_space:
      return spaces.Dict(OrderedDict(zip(self.tensor_names, sps)))
    else:
      return spaces.Tuple(sps)

  @property
  def tensor_names(self):
    return self._tensor_names
