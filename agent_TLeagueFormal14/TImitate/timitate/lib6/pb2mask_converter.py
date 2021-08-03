from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np
from absl import app
from collections import OrderedDict
from gym import spaces
from distutils.version import LooseVersion
from pysc2.lib.features import PlayerRelative as ALLIANCE
from pysc2.lib.features import Effects
from pysc2.lib.tech_tree import TechTree
from pysc2.lib.typeenums import UNIT_TYPEID, ABILITY_ID
from timitate.base_converter import BaseConverter

from timitate.lib6.z_actions import ZERG_ABILITIES, ABILITY_TYPES
from timitate.lib6.z_actions import z_name_map, z_ab_map
from timitate.utils.const import z_train_tar_map, z_morph_tar_map, z_skill_tar_map, \
  KJ_BORN_POS, KJ_IDEAL_BASE_POS, BUILDINGS_SET
from timitate.lib6.z_actions import select_unit_type_list, z_sub2gen_map
from timitate.lib6.pb2feature_converter import resize_img

from timitate.utils.mask_fn import creep_pos_mask_fn_new, nydus_pos_mask_fn_new, \
  one_pos_mask_fn, tumor_pos_mask_fn_new, zero_pos_mask_fn, zero_unit_mask_fn, \
  base_pos_mask_fn_new, ban_zr_fn, hidden_pos_mask_fn, hidden_base_mask_fn, \
  unknown_base_mask_fn, not_rush_fn
from timitate.utils.utils import _get_minimaps


class PB2MaskConverter(BaseConverter):

  def __init__(self, dtype=np.bool,
               max_unit_num=600,
               map_resolution=(200, 176),
               add_cargo_to_units=False,
               game_version='4.7.1',
               dict_space=False,
               inj_larv_rule=False,
               ban_zb_rule=False,
               ban_rr_rule=False,
               ban_hydra_rule=False,
               rr_food_cap=40,
               zb_food_cap=10,
               hydra_food_cap=10,
               mof_lair_rule=False,
               hydra_spire_rule=False,
               overseer_rule=False,
               expl_map_rule=False,
               baneling_rule=False,
               ab_dropout_list=None):
    self._map_resolution = tuple(map_resolution)
    self._dtype = dtype
    self._max_unit_num = max_unit_num
    self._add_cargo_to_units = add_cargo_to_units
    self._cmd_unit_mask_abs = [ab for ab in ZERG_ABILITIES
                               if ab[1] == ABILITY_TYPES.CMD_UNIT]
    self._cmd_pos_mask_abs = [ab for ab in ZERG_ABILITIES
                              if ab[1] == ABILITY_TYPES.CMD_POS]
    self._tech_tree = TechTree()
    self._tech_tree.update_version(game_version)
    # self._flip = LooseVersion(game_version) >= LooseVersion('4.8.6')
    # Only work for linux
    # Mac flips creep/visibility from 4.9.0, pathing/placement from 4.8.6
    self._flip = (game_version not in ['4.7.1', '4.8.0'])
    self._dict_space = dict_space
    self._inj_larv_rule = inj_larv_rule
    self._ban_zb_rule = ban_zb_rule
    self._ban_rr_rule = ban_rr_rule
    self._ban_hydra_rule = ban_hydra_rule
    self._rr_rood_cap = rr_food_cap
    self._zb_food_cap = zb_food_cap
    self._hydra_food_cap = hydra_food_cap
    self._mof_lair_rule = mof_lair_rule
    self._hydra_spire_rule = hydra_spire_rule
    self._overseer_rule = overseer_rule
    self._expl_map_rule = expl_map_rule
    self._baneling_rule = baneling_rule
    self._enemy_air = False
    self._enemy_lair = False
    self._enemy_lurker = False
    self._enemy_baneling = False
    self._self_lair = False
    self._self_overseer = False
    self._self_hydraliskden = False
    self._self_spire = False
    self._base_visit_time_dict = {}
    self._self_baneling = False
    self._tensor_names = ['MASK_AB',
                          'MASK_LEN',
                          'MASK_SELECTION',
                          'MASK_CMD_UNIT',
                          'MASK_CMD_POS',
                          ]
    self._ab_dropout_list = ab_dropout_list
    self._arg_mask = self._make_arg_mask()
    self._lair_units = [UNIT_TYPEID.ZERG_LAIR.value,
                        UNIT_TYPEID.ZERG_HYDRALISKDEN.value,
                        UNIT_TYPEID.ZERG_LURKERDENMP.value,
                        UNIT_TYPEID.ZERG_SPIRE.value,
                        UNIT_TYPEID.ZERG_GREATERSPIRE.value,
                        UNIT_TYPEID.ZERG_INFESTATIONPIT.value,
                        UNIT_TYPEID.ZERG_HIVE.value,
                        UNIT_TYPEID.ZERG_ULTRALISKCAVERN.value,
                        UNIT_TYPEID.ZERG_NYDUSCANAL.value,
                        UNIT_TYPEID.ZERG_NYDUSNETWORK.value,
                        UNIT_TYPEID.ZERG_HYDRALISK.value,
                        UNIT_TYPEID.ZERG_LURKERMP.value,
                        UNIT_TYPEID.ZERG_LURKERMPEGG.value,
                        UNIT_TYPEID.ZERG_OVERSEER.value,
                        UNIT_TYPEID.ZERG_OVERSEEROVERSIGHTMODE.value,
                        UNIT_TYPEID.ZERG_MUTALISK.value,
                        UNIT_TYPEID.ZERG_CORRUPTOR.value,
                        UNIT_TYPEID.ZERG_BROODLORD.value,
                        UNIT_TYPEID.ZERG_VIPER.value]


  def reset(self, **kwargs):
    super(PB2MaskConverter, self).reset(**kwargs)
    self._enemy_air = False
    self._enemy_lair = False
    self._enemy_lurker = False
    self._enemy_baneling = False
    self._self_lair = False
    self._self_overseer = False
    self._self_hydraliskden = False
    self._self_spire = False
    self._base_visit_time_dict = {}
    self._self_baneling = False

  """ functions start with _ are used for rules """
  def _update_enemy_air(self, obs):
    if not self._enemy_air:
      units = obs.observation.raw_data.units
      enemy_air_u = ((u.alliance == ALLIANCE.ENEMY.value
                      and u.unit_type in [UNIT_TYPEID.ZERG_MUTALISK.value,
                                          UNIT_TYPEID.ZERG_CORRUPTOR.value,
                                          UNIT_TYPEID.ZERG_BROODLORD.value,
                                          UNIT_TYPEID.ZERG_VIPER.value,
                                          UNIT_TYPEID.ZERG_SPIRE.value,
                                          UNIT_TYPEID.ZERG_GREATERSPIRE.value])
                     for u in units)
      self._enemy_air = any(enemy_air_u)

  def _update_enemy_lurker(self, obs):
    if not self._enemy_lurker:
      units = obs.observation.raw_data.units
      effects = (e.effect_id == Effects.LurkerSpines.value
                 for e in obs.observation.raw_data.effects)
      enemy_lurkers = ((u.alliance == ALLIANCE.ENEMY.value
                       and u.unit_type in [UNIT_TYPEID.ZERG_LURKERMP.value,
                                           UNIT_TYPEID.ZERG_LURKERDENMP.value,
                                           UNIT_TYPEID.ZERG_LURKERMPEGG.value,
                                           UNIT_TYPEID.ZERG_LURKERMPBURROWED.value,
                                           UNIT_TYPEID.ZERG_ROACHBURROWED.value])
                       for u in units)

      self._enemy_lurker = any(effects) or any(enemy_lurkers)

  def _update_enemy_lair(self, obs):
    if not self._enemy_lair:
      units = obs.observation.raw_data.units
      enemy_lair_u = ((u.alliance == ALLIANCE.ENEMY.value
                       and u.unit_type in self._lair_units) for u in units)
      self._enemy_lair = any(enemy_lair_u)

  def _update_enemy_baneling(self, obs):
    if not self._enemy_baneling:
      units = obs.observation.raw_data.units
      enemy_baneling_u = ((u.alliance == ALLIANCE.ENEMY.value
                           and u.unit_type in [UNIT_TYPEID.ZERG_BANELING.value,
                                               UNIT_TYPEID.ZERG_BANELINGNEST.value])
                          for u in units)
      self._enemy_baneling = any(enemy_baneling_u)

  def _update_self_lair(self, obs):
    units = obs.observation.raw_data.units
    self_lair_u = ((u.alliance == ALLIANCE.SELF.value and
                    u.unit_type in [UNIT_TYPEID.ZERG_LAIR.value,
                                    UNIT_TYPEID.ZERG_HIVE.value])
                   for u in units)
    self_morphing_u = ((u.unit_type == UNIT_TYPEID.ZERG_HATCHERY.value and
                        u.alliance == ALLIANCE.SELF.value and
                        u.build_progress == 1.0 and
                        len(u.orders) > 0 and
                        u.orders[0].ability_id == ABILITY_ID.MORPH_LAIR.value)
                       for u in units)
    self._self_lair = any(self_lair_u) or any(self_morphing_u)

  def _update_self_overseer(self, obs):
    units = obs.observation.raw_data.units
    self_overseer_u = ((u.alliance == ALLIANCE.SELF.value and
                        u.unit_type in [UNIT_TYPEID.ZERG_OVERSEER.value,
                                       UNIT_TYPEID.ZERG_OVERSEEROVERSIGHTMODE.value])
                       for u in units)
    self._self_overseer = any(self_overseer_u)

  def _update_self_hydraliskden(self, obs):
    units = obs.observation.raw_data.units
    self_hydraliskden_u = ((u.alliance == ALLIANCE.SELF.value and
                            u.unit_type == UNIT_TYPEID.ZERG_HYDRALISKDEN.value)
                           for u in units)
    self._self_hydraliskden = any(self_hydraliskden_u)

  def _update_self_spire(self, obs):
    units = obs.observation.raw_data.units
    self_spire_u = ((u.alliance == ALLIANCE.SELF.value and
                     u.unit_type in [UNIT_TYPEID.ZERG_SPIRE.value,
                                     UNIT_TYPEID.ZERG_GREATERSPIRE.value])
                    for u in units)
    self._self_spire = any(self_spire_u)

  def _update_self_baneling(self, obs):
    if not self._self_baneling:
      # self baneling only count once (that banelingnest is easy to be destoried)
      units = obs.observation.raw_data.units
      baneling_u = ((u.alliance == ALLIANCE.SELF.value and
                     u.unit_type == UNIT_TYPEID.ZERG_BANELINGNEST.value)
                    for u in units)
      self._self_baneling = any(baneling_u)

  def _explore_map_condition(self, obs, minimap):
    """ This function should be only used for KJ map """
    # (1) both map start_pos are visible or fogged, but not full hidden
    # (2) units list do not contain enemy units except overlord, overseer,
    # overseer_oversight, overlord_trans, overlord_concoons, tumors. Note that
    # buildings with display_type = snapshot are in unit list (per jc)
    # (3) there still exist base positions that are not explored, i.e., are full hidden
    units = obs.observation.raw_data.units
    enemy_valid_u = [u for u in units if
                     u.alliance == ALLIANCE.ENEMY.value and
                     u.unit_type not in [UNIT_TYPEID.ZERG_OVERLORD.value,
                                         UNIT_TYPEID.ZERG_OVERSEER.value,
                                         UNIT_TYPEID.ZERG_OVERSEEROVERSIGHTMODE.value,
                                         UNIT_TYPEID.ZERG_OVERLORDTRANSPORT.value,
                                         UNIT_TYPEID.ZERG_OVERLORDCOCOON.value,
                                         UNIT_TYPEID.ZERG_TRANSPORTOVERLORDCOCOON.value,
                                         UNIT_TYPEID.ZERG_CREEPTUMOR.value,
                                         UNIT_TYPEID.ZERG_CREEPTUMORQUEEN.value,
                                         UNIT_TYPEID.ZERG_CREEPTUMORBURROWED.value]]
    # the following attribute fetch follows pb2feature
    visibility0 = np.equal(minimap.visibility_map, 0)  # Hidden
    map_ori_size = (obs.observation.raw_data.map_state.creep.size.x,
                    obs.observation.raw_data.map_state.creep.size.y)
    ori_x, ori_y = map_ori_size
    explored_born_pos = True
    for pos in KJ_BORN_POS:
      pos_x, pos_y = pos
      if visibility0[ori_y - 1 - int(pos_y), int(pos_x)] == 1:
        explored_born_pos = False

    explored_all_base_pos = True
    for pos in KJ_IDEAL_BASE_POS:
      pos_x, pos_y = pos
      if visibility0[ori_y - 1 - int(pos_y), int(pos_x)] == 1:
        explored_all_base_pos = False

    return explored_born_pos and len(enemy_valid_u) == 0 and (not explored_all_base_pos)

  def _explore_map_condition_v2(self, obs, minimap):
    """ This function should be only used for KJ map """
    # (1) both map start_pos are visible or fogged, but not hidden
    # (2) units list do not contain enemy buildings
    # (3) there still exist base positions that are not explored, i.e., are hidden
    units = obs.observation.raw_data.units
    enemy_valid_u = [u for u in units if
                     u.alliance == ALLIANCE.ENEMY.value and
                     u.unit_type in BUILDINGS_SET and
                     u.unit_type not in [UNIT_TYPEID.ZERG_CREEPTUMOR.value,
                                         UNIT_TYPEID.ZERG_CREEPTUMORQUEEN.value,
                                         UNIT_TYPEID.ZERG_CREEPTUMORBURROWED.value]]
    # the following attribute fetch follows pb2feature
    visibility0 = np.equal(minimap.visibility_map, 0)  # Hidden
    map_ori_size = (obs.observation.raw_data.map_state.creep.size.x,
                    obs.observation.raw_data.map_state.creep.size.y)
    ori_x, ori_y = map_ori_size
    explored_born_pos = True
    for pos in KJ_BORN_POS:
      pos_x, pos_y = pos
      if visibility0[ori_y - 1 - int(pos_y), int(pos_x)] == 1:
        explored_born_pos = False

    explored_all_base_pos = True
    for pos in KJ_IDEAL_BASE_POS:
      pos_x, pos_y = pos
      if visibility0[ori_y - 1 - int(pos_y), int(pos_x)] == 1:
        explored_all_base_pos = False

    return explored_born_pos and len(enemy_valid_u) == 0 and (not explored_all_base_pos)

  def _explore_map_condition_v3(self, obs, minimap):
    """ This function should be only used for KJ map """
    # (1) both map start_pos are visible or fogged, but not hidden
    # (2) units list do not contain enemy buildings
    units = obs.observation.raw_data.units
    enemy_valid_u = ((u.alliance == ALLIANCE.ENEMY.value and
                      u.unit_type in BUILDINGS_SET and
                      u.unit_type not in [UNIT_TYPEID.ZERG_CREEPTUMOR.value,
                                          UNIT_TYPEID.ZERG_CREEPTUMORQUEEN.value,
                                          UNIT_TYPEID.ZERG_CREEPTUMORBURROWED.value])
                     for u in units)
    if any(enemy_valid_u):
      return False
    # the following attribute fetch follows pb2feature
    visibility0 = np.equal(minimap.visibility_map, 0)  # Hidden
    map_ori_size = (obs.observation.raw_data.map_state.creep.size.x,
                    obs.observation.raw_data.map_state.creep.size.y)
    ori_x, ori_y = map_ori_size
    explored_born_pos = True
    for pos in KJ_BORN_POS:
      pos_x, pos_y = pos
      if visibility0[ori_y - 1 - int(pos_y), int(pos_x)] == 1:
        explored_born_pos = False
    return explored_born_pos

  def _update_map_base_condition(self, obs, minimap):
    """ This function should be only used for KJ map """
    # the following attribute fetch follows pb2feature
    # visibility0 = np.equal(minimap.visibility_map, 0)  # Hidden
    # visibility1 = np.equal(minimap.visibility_map, 1)  # Fogged
    visibility2 = np.equal(minimap.visibility_map, 2)  # Visible

    map_ori_size = (obs.observation.raw_data.map_state.creep.size.x,
                    obs.observation.raw_data.map_state.creep.size.y)
    ori_x, ori_y = map_ori_size

    for pos in KJ_IDEAL_BASE_POS:
      pos_x, pos_y = pos
      if visibility2[ori_y - 1 - int(pos_y), int(pos_x)] == 1:
        self._base_visit_time_dict[str(pos_x)+','+str(pos_y)] = obs.observation.game_loop

  def convert(self, pb):
    assert self._flip, "4.7.1/4.8.0 are not supported any more!"
    obs, game_info = pb
    images = _get_minimaps(obs)

    self._update_enemy_air(obs)
    self._update_enemy_lurker(obs)
    self._update_enemy_lair(obs)
    self._update_enemy_baneling(obs)
    self._update_self_lair(obs)
    self._update_self_hydraliskden(obs)
    self._update_self_spire(obs)
    self._update_self_overseer(obs)
    self._update_map_base_condition(obs, images)
    self._update_self_baneling(obs)

    ab_mask = self._get_ability_mask(obs)
    len_mask = self._get_unit_len_mask(obs)
    selection_mask = self._get_selection_mask(obs, ab_mask)
    cmd_unit_mask = self._get_cmd_unit_mask(obs, ab_mask)
    cmd_pos_mask = self._get_cmd_pos_mask(obs, ab_mask, images)
    ab_mask &= ((~self._arg_mask[:, 3 - 1]) | (np.sum(selection_mask, axis=1) > 0))
    ab_mask &= ((~self._arg_mask[:, 4 - 1]) | (np.sum(cmd_unit_mask, axis=1) > 0))
    res = ab_mask, len_mask, selection_mask, cmd_unit_mask, cmd_pos_mask
    if self._dict_space:
      return self._check_space(OrderedDict(zip(self.tensor_names, res)))
    else:
      return self._check_space(res)

  @property
  def space(self):
    num_abilities = len(ZERG_ABILITIES)
    sps = [
        spaces.Box(low=0, high=1, shape=(num_abilities,), dtype=self._dtype),
        spaces.Box(low=0, high=1, shape=(self._max_unit_num,), dtype=self._dtype),
        spaces.Box(low=0, high=1, shape=(num_abilities, self._max_unit_num), dtype=self._dtype),
        spaces.Box(low=0, high=1, shape=(num_abilities, self._max_unit_num), dtype=self._dtype),
        spaces.Box(low=0, high=1, shape=(num_abilities,) + self._map_resolution, dtype=self._dtype),
    ]
    if self._dict_space:
      return spaces.Dict(OrderedDict(zip(self.tensor_names, sps)))
    else:
      return spaces.Tuple(sps)

  @property
  def tensor_names(self):
    return self._tensor_names

  """ constant mask: astar func_embed type mask """
  def get_selection_type_func_mask(self):
    return np.stack([ab[-3] for ab in ZERG_ABILITIES], axis=0)

  """ constant mask: astar func_embed type mask """
  def get_tar_u_type_func_mask(self):
    return np.stack([ab[-2] for ab in ZERG_ABILITIES], axis=0)

  """ constant mask """
  def _make_arg_mask(self):
    # A_NOOP_NUM
    # A_SHIFT
    # A_SELECT
    # A_CMD_UNIT
    # A_CMD_POS
    mask = []
    for ab in ZERG_ABILITIES:
      if ab[1] == ABILITY_TYPES.CMD_QUICK:
        mask.append(np.asarray([True, True, True, False, False], dtype=self._dtype))
      elif ab[1] == ABILITY_TYPES.NO_OP:
        mask.append(np.asarray([True, False, False, False, False], dtype=self._dtype))
      elif ab[1] == ABILITY_TYPES.CMD_UNIT:
        mask.append(np.asarray([True, True, True, True, False], dtype=self._dtype))
      elif ab[1] == ABILITY_TYPES.CMD_POS:
        mask.append(np.asarray([True, True, True, False, True], dtype=self._dtype))
      else:
        mask.append(np.asarray([True, False, False, False, False], dtype=self._dtype))
    return np.asarray(mask, dtype=self._dtype)

  def get_arg_mask(self):
    return self._arg_mask

  """ dynamic mask, building limit mask """
  def _get_ability_mask(self, obs):
    ab_mask = np.array([zab[4](obs) for zab in ZERG_ABILITIES], dtype=np.bool)
    ### special treating per rules
    ## inject larva rule
    ab_mask[z_name_map['Effect_InjectLarva_screen']] = \
      ZERG_ABILITIES[z_name_map['Effect_InjectLarva_screen']][4](obs, self._inj_larv_rule)
    ## ban zergling and roach rule
    ab_mask[z_name_map['Train_Zergling_quick']] = \
      ZERG_ABILITIES[z_name_map['Train_Zergling_quick']][4](obs, self._ban_zb_rule, self._zb_food_cap)
    ab_mask[z_name_map['Morph_Baneling_quick']] = \
      ZERG_ABILITIES[z_name_map['Morph_Baneling_quick']][4](obs, self._ban_zb_rule, self._zb_food_cap)
    ab_mask[z_name_map['Train_Roach_quick']] = \
      ZERG_ABILITIES[z_name_map['Train_Roach_quick']][4](obs, self._ban_rr_rule, self._enemy_air,
                                                         self._rr_rood_cap)
    ab_mask[z_name_map['Morph_Ravager_quick']] = \
      ZERG_ABILITIES[z_name_map['Morph_Ravager_quick']][4](obs, self._ban_rr_rule, self._enemy_air,
                                                           self._rr_rood_cap)
    ab_mask[z_name_map['Train_Hydralisk_quick']] = \
      ZERG_ABILITIES[z_name_map['Train_Hydralisk_quick']][4](
        obs, self._ban_hydra_rule, self._enemy_air, self._hydra_food_cap)

    ## baneling_rule
    if self._baneling_rule and (not self._self_baneling) and \
      ZERG_ABILITIES[z_name_map['Build_BanelingNest_screen']][4](obs):
      if self._enemy_baneling:
        ab_mask = np.zeros_like(ab_mask, dtype=np.bool)
        ab_mask[z_name_map['Build_BanelingNest_screen']] = True
    ## morph lair rule
    if self._mof_lair_rule and (not self._self_lair) and \
      ZERG_ABILITIES[z_name_map['Morph_Lair_quick']][4](obs):
      # first make sure that morph_lair is not executed yet and no lair is built
      # and this action is indeed available at this step, then if enemy has already
      # morphed lair or satisfied some logic
      if self._enemy_lair or not_rush_fn(obs):
        ab_mask = np.zeros_like(ab_mask, dtype=np.bool)
        ab_mask[z_name_map['Morph_Lair_quick']] = True
    ## hydraliskden and spire rule
    # if lair exists and enemy has airforce and both hydraliskden and spire do not exist
    if self._hydra_spire_rule and self._self_lair:
      if self._enemy_air and (not self._self_hydraliskden) and (not self._self_spire):
        can_build_hydraliskden = ZERG_ABILITIES[z_name_map['Build_HydraliskDen_screen']][4](obs)
        can_build_spire = ZERG_ABILITIES[z_name_map['Build_Spire_screen']][4](obs)
        if can_build_hydraliskden or can_build_spire:
          ab_mask = np.zeros_like(ab_mask, dtype=np.bool)
          if can_build_hydraliskden:
            ab_mask[z_name_map['Build_HydraliskDen_screen']] = True
          if can_build_spire:
            ab_mask[z_name_map['Build_Spire_screen']] = True
    ## overseer rule
    # if lair exists and enemy has lurker and overseer does not exist
    if self._overseer_rule and self._self_lair:
      if self._enemy_lurker and (not self._self_overseer):
        if ZERG_ABILITIES[z_name_map['Morph_Overseer_quick']][4](obs):
          ab_mask = np.zeros_like(ab_mask, dtype=np.bool)
          ab_mask[z_name_map['Morph_Overseer_quick']] = True
    # action dropout rule
    if self._ab_dropout_list is not None and len(self._ab_dropout_list) > 0:
      for ab_name in self._ab_dropout_list:
        assert isinstance(ab_name, str) and ab_name in z_name_map
        ab_mask[z_name_map[ab_name]] = False
    return ab_mask

  """ general units len mask """
  def _get_unit_len_mask(self, obs):
    l = len(obs.observation.raw_data.units)
    if self._add_cargo_to_units:
      l += np.sum([len(u.passengers) for u in obs.observation.raw_data.units])
    len_mask = np.ones(shape=(self._max_unit_num,), dtype=self._dtype)
    len_mask[l:] = 0
    return len_mask

  """ dynamic mask """
  def _get_selection_mask(self, obs, ab_mask):
    return self._common_unit_mask(obs, ab_mask, func_id=5)

  """ dynamic mask """
  def _get_cmd_unit_mask(self, obs, ab_mask):
    return self._common_unit_mask(obs, ab_mask, func_id=6)

  def _common_unit_mask(self, obs, ab_mask, func_id):
    unit_mask = []
    n = self._max_unit_num - len(obs.observation.raw_data.units)
    if n < 0:
      print("WARN: number of units exceeds the max unit length. "
            "Abandon the rest.")
    zero_mask = np.zeros(shape=(self._max_unit_num,), dtype=np.bool)

    # enemy burrowed roach
    enemy_br = np.zeros(shape=(self._max_unit_num,), dtype=np.bool)
    for i, u in enumerate(obs.observation.raw_data.units):
      if u.unit_type == UNIT_TYPEID.ZERG_ROACHBURROWED.value and \
         u.alliance == ALLIANCE.ENEMY.value and \
         u.display_type == 3 and u.health == 0:  # fully hidden (
        # under which condition all attributes are zeros)
        if i < self._max_unit_num:
          enemy_br[i] = True

    for i, zab in enumerate(ZERG_ABILITIES):
      if not ab_mask[i] or zab[func_id] == zero_unit_mask_fn:
        tmp_mask = zero_mask
      else:
        tmp_mask = zab[func_id](obs.observation.raw_data.units)
        # special treating
        if zab[0] == 'Effect_InjectLarva_screen' and func_id == 6:
          tmp_mask = zab[func_id](obs.observation.raw_data.units, self._inj_larv_rule)
        # deal with > 600 units
        if n < 0:
          tmp_mask = tmp_mask[0:self._max_unit_num]
        else:
          tmp_mask = np.pad(tmp_mask, [0, n], 'constant')
        tmp_mask &= np.logical_not(enemy_br)
      unit_mask.append(tmp_mask)
    return np.asarray(unit_mask, dtype=self._dtype)

  """ dynamic mask """
  def _get_cmd_pos_mask(self, obs, ab_mask, images=None):
    cmd_pos_mask = []
    zero_mask = np.zeros(self._map_resolution, dtype=np.bool)
    one_mask = np.ones(self._map_resolution, dtype=np.bool)
    if images is not None:
      images = _get_minimaps(obs)
    creep_mask = resize_img(
      np.array(creep_pos_mask_fn_new(images), dtype=np.bool),
      img_size=self._map_resolution)
    # expand tumor_mask by one pixel
    tumor_mask = resize_img(
      np.array(tumor_pos_mask_fn_new(images), dtype=np.bool),
      img_size=self._map_resolution, order=1) > 0
    nydus_mask = resize_img(
      np.array(nydus_pos_mask_fn_new(images), dtype=np.bool),
      img_size=self._map_resolution)
    base_mask = resize_img(
      np.array(base_pos_mask_fn_new(images), dtype=np.bool),
      img_size=self._map_resolution)
    # full hidden mask if explore_rule used
    hidden_base_mask = resize_img(
      np.array(hidden_base_mask_fn(obs, images), dtype=np.bool),
      img_size=self._map_resolution, order=1) > 0
    unknown_base_mask = resize_img(
      np.array(unknown_base_mask_fn(obs, images,
                                    self._base_visit_time_dict),
               dtype=np.bool),
      img_size=self._map_resolution, order=1) > 0

    # import imageio
    # imageio.imwrite('creep_mask.jpg', creep_mask.astype(np.float32))
    # imageio.imwrite('tumor_mask.jpg', tumor_mask.astype(np.float32))
    # imageio.imwrite('nydus_mask.jpg', nydus_mask.astype(np.float32))

    for i, zab in enumerate(ZERG_ABILITIES):
      mask_fn = zab[7]
      current_mask = None
      if not ab_mask[i] or mask_fn == zero_pos_mask_fn:
        current_mask = zero_mask
      elif mask_fn == one_pos_mask_fn:
        current_mask = one_mask
      elif mask_fn == creep_pos_mask_fn_new:
        current_mask = creep_mask
      elif mask_fn == tumor_pos_mask_fn_new:
        current_mask = tumor_mask
      elif mask_fn == nydus_pos_mask_fn_new:
        current_mask = nydus_mask
      elif mask_fn == base_pos_mask_fn_new:
        current_mask = base_mask
      assert current_mask is not None
      ## Begin: rule for exploring map
      if self._expl_map_rule:
        if zab[0] == 'Attack_Attack_screen' and \
          self._explore_map_condition_v3(obs, images):
          # current_mask = hidden_base_mask
          if np.sum(unknown_base_mask) > 0:
            current_mask = unknown_base_mask
      ## End
      cmd_pos_mask.append(current_mask)
    return np.asarray(cmd_pos_mask, dtype=self._dtype)


def main(argv):
  pb2mask = PB2MaskConverter()
  print(len([ab[0] for ab in pb2mask._cmd_unit_mask_abs]))


if __name__ == '__main__':
  app.run(main)
