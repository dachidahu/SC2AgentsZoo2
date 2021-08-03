import math
import numpy as np
from timitate.utils.utils import norm_img, bitmap2array, _get_minimaps
from pysc2.lib.features import PlayerRelative as ALLIANCE
from pysc2.lib.typeenums import UNIT_TYPEID, BUFF_ID, ABILITY_ID, UPGRADE_ID
from timitate.utils.const import BUILDINGS_SET, BASES_SET, UPGRADE_ID, \
   AIR_UNITS_SET, NEUTRAL_VESPENE_SET, NEUTRAL_MINERAL_SET, VESPENE_CAP_SET, \
   NEUTRAL_ATTACKABLE_SET, EGGS_SET, GROUND_UNITS_SET, GROUND_UNITS_BURROWED_SET, \
   BUILDINGS_RADIUS, ABILITY_RADIUS, KJ_IDEAL_BASE_POS
from timitate.utils.const import ALL_UNIT_TYPES, RESEARCH_ABILITY_IDS, \
   RESEARCH_BUILDINGS_SET, MORPH_ABILITY_IDS, ATTACK_SELF_BUILDINGS_SET, \
   MAP_PLAYABLE_AREA_DICT


""" some rule-based mask func """
def not_rush_fn(obs):
  """ determine my strategy is not a pure rush """
  # if more than two hatchery: can specify MA
  units = obs.observation.raw_data.units
  self_bases = [u for u in units if u.alliance == ALLIANCE.SELF.value
                and u.unit_type in BASES_SET]
  # if build roachwarren: can specify MA
  self_rw = [u for u in units if u.alliance == ALLIANCE.SELF.value
             and u.unit_type == UNIT_TYPEID.ZERG_ROACHWARREN.value
             and u.build_progress == 1.0]
  # if there are more than 2 spinecrawler: can specify ml and fl;
  # dz do not gather gas, so it is fine
  self_spine = [u for u in units if u.alliance == ALLIANCE.SELF.value
                and u.unit_type in [UNIT_TYPEID.ZERG_SPINECRAWLER.value,
                                    UNIT_TYPEID.ZERG_SPINECRAWLERUPROOTED.value]]
  return len(self_bases) >= 3 or \
         (len(self_rw) > 0 and ban_zr_fn(obs, enemy_air=True, food_cap=10)) or \
         len(self_spine) >= 2


def ban_zr_fn(obs, enemy_air=False, food_cap=50):
  units = obs.observation.raw_data.units
  self_zr = [u for u in units if u.alliance == ALLIANCE.SELF.value
             and u.unit_type in [UNIT_TYPEID.ZERG_ZERGLING.value,
                                 UNIT_TYPEID.ZERG_ZERGLINGBURROWED,
                                 UNIT_TYPEID.ZERG_BANELING.value,
                                 UNIT_TYPEID.ZERG_BANELINGBURROWED.value,
                                 UNIT_TYPEID.ZERG_ROACH.value,
                                 UNIT_TYPEID.ZERG_ROACHBURROWED.value,
                                 UNIT_TYPEID.ZERG_RAVAGER.value,
                                 UNIT_TYPEID.ZERG_RAVAGERBURROWED.value,
                                 UNIT_TYPEID.ZERG_BANELINGCOCOON.value,
                                 UNIT_TYPEID.ZERG_RAVAGERCOCOON.value]]
  zr_food = 0
  for u in self_zr:
    if u.unit_type in [UNIT_TYPEID.ZERG_ZERGLING.value,
                       UNIT_TYPEID.ZERG_ZERGLINGBURROWED.value,
                       UNIT_TYPEID.ZERG_BANELING.value,
                       UNIT_TYPEID.ZERG_BANELINGBURROWED.value,
                       UNIT_TYPEID.ZERG_BANELINGCOCOON.value]:
      zr_food += 0.5
    if u.unit_type in [UNIT_TYPEID.ZERG_ROACH.value,
                       UNIT_TYPEID.ZERG_ROACHBURROWED.value]:
      zr_food += 2
    if u.unit_type in [UNIT_TYPEID.ZERG_RAVAGER.value,
                       UNIT_TYPEID.ZERG_RAVAGERBURROWED.value,
                       UNIT_TYPEID.ZERG_RAVAGERCOCOON.value]:
      zr_food += 3
  # if zr_food > 50 and enemy has airforce (in this episode not this frame)
  # and no hydralisk yet, then return ban_zr = True
  return zr_food > food_cap and enemy_air and len(
      [u for u in units if u.alliance == ALLIANCE.SELF.value
       and u.unit_type in [UNIT_TYPEID.ZERG_HYDRALISKDEN.value,
                           UNIT_TYPEID.ZERG_SPIRE.value,
                           UNIT_TYPEID.ZERG_GREATERSPIRE.value]]) == 0


def ban_zb_fn(obs, zb_food_cap=10):
  units = obs.observation.raw_data.units
  self_zb = [u for u in units if u.alliance == ALLIANCE.SELF.value
             and u.unit_type in [UNIT_TYPEID.ZERG_ZERGLING.value,
                                 UNIT_TYPEID.ZERG_ZERGLINGBURROWED,
                                 UNIT_TYPEID.ZERG_BANELING.value,
                                 UNIT_TYPEID.ZERG_BANELINGBURROWED.value,
                                 UNIT_TYPEID.ZERG_BANELINGCOCOON.value]]
  zb_food = len(self_zb) * 0.5
  # if zr_food > zb_food_cap, then return ban_zb = True
  return zb_food > zb_food_cap


def ban_rr_fn(obs, enemy_air=False, rr_food_cap=40):
  units = obs.observation.raw_data.units
  self_rr = [u for u in units if u.alliance == ALLIANCE.SELF.value
             and u.unit_type in [UNIT_TYPEID.ZERG_ROACH.value,
                                 UNIT_TYPEID.ZERG_ROACHBURROWED.value,
                                 UNIT_TYPEID.ZERG_RAVAGER.value,
                                 UNIT_TYPEID.ZERG_RAVAGERBURROWED.value,
                                 UNIT_TYPEID.ZERG_RAVAGERCOCOON.value]]
  self_lair = [u for u in units if u.alliance == ALLIANCE.SELF.value
               and u.unit_type in [UNIT_TYPEID.ZERG_LAIR.value,
                                   UNIT_TYPEID.ZERG_HIVE.value]]
  rr_food = 0
  for u in self_rr:
    if u.unit_type in [UNIT_TYPEID.ZERG_ROACH.value,
                       UNIT_TYPEID.ZERG_ROACHBURROWED.value]:
      rr_food += 2
    if u.unit_type in [UNIT_TYPEID.ZERG_RAVAGER.value,
                       UNIT_TYPEID.ZERG_RAVAGERBURROWED.value,
                       UNIT_TYPEID.ZERG_RAVAGERCOCOON.value]:
      rr_food += 3
  # if rr_food > rr_food_cap and enemy has airforce (in this episode not
  # this frame) and has already morphed lair and no anti-air building yet,
  # then return ban_rr = True
  return rr_food > rr_food_cap and enemy_air and len(self_lair) > 0 and len(
      [u for u in units if u.alliance == ALLIANCE.SELF.value
       and u.unit_type in [UNIT_TYPEID.ZERG_HYDRALISKDEN.value,
                           UNIT_TYPEID.ZERG_SPIRE.value,
                           UNIT_TYPEID.ZERG_GREATERSPIRE.value]]) == 0


def ban_hydra_fn(obs, enemy_air=False, hydra_food_cap=10):
  units = obs.observation.raw_data.units
  self_hydra = [u for u in units if u.alliance == ALLIANCE.SELF.value
                and u.unit_type in [UNIT_TYPEID.ZERG_HYDRALISK.value,
                                    UNIT_TYPEID.ZERG_HYDRALISKBURROWED.value]]
  hydra_food = 2 * len(self_hydra)
  # if not really seen enemy's air (mutalisk), do not train many hydralisks
  return hydra_food > hydra_food_cap and (not enemy_air)


""" ability mask func """
def basic_ab_filter_fn(obs, tp, mineral=0, vespene=0,
                       energy=0, food=0, alliance=ALLIANCE.SELF.value,
                       pre_build=None, pre_tech=None, req_free=False,
                       unique_ab_id=None, tech_id=None):
  """ tp indicates executor types: once there exists at least one in tp, mask might be true
  req_free indicates executor should be free
  """
  units = obs.observation.raw_data.units
  if not isinstance(tp, list) and not isinstance(tp, tuple) and not isinstance(tp, set):
    tps = [tp]
  else:
    tps = tp

  req_func = (lambda u: len(u.orders) == 0) if req_free else (lambda u: True)
  res = any([u.unit_type in tps
             and u.energy >= energy and req_func(u)
             and u.alliance == alliance for u in units]) & \
        (obs.observation.player_common.minerals >= mineral) & \
        (obs.observation.player_common.vespene >= vespene) & \
        (obs.observation.player_common.food_cap - obs.observation.player_common.food_used
         >= (food if food > 0 else -200))
  if pre_tech is not None:
    if not isinstance(pre_tech, list) and not isinstance(pre_tech, tuple) and not isinstance(pre_tech, set):
      pre_tech = [pre_tech]
    else:
      pass
    upgraded_techs = obs.observation.raw_data.player.upgrade_ids
    pre_tech_cond = True
    for tech in pre_tech:
      pre_tech_cond &= (tech in upgraded_techs)
    res &= pre_tech_cond
  if pre_build is not None:
    if not isinstance(pre_build, list) and not isinstance(pre_build, tuple) and not isinstance(pre_build, set):
      pre_build = [pre_build]
    else:
      pass
    # must be competed building types
    self_active_unit_types = [u.unit_type for u in units if u.alliance == ALLIANCE.SELF.value
                              and u.build_progress == 1.0]
    pre_build_cond = True
    for build in pre_build:
      # TODO: confirm only spire and lair have the following condition?
      if build == UNIT_TYPEID.ZERG_HATCHERY.value:
        pre_build_cond &= ((build in self_active_unit_types) or
                           (UNIT_TYPEID.ZERG_LAIR.value in self_active_unit_types) or
                           (UNIT_TYPEID.ZERG_HIVE.value in self_active_unit_types))
      elif build == UNIT_TYPEID.ZERG_LAIR.value:
        pre_build_cond &= ((build in self_active_unit_types) or
                           (UNIT_TYPEID.ZERG_HIVE.value in self_active_unit_types))
      elif build == UNIT_TYPEID.ZERG_SPIRE.value:
        pre_build_cond &= ((build in self_active_unit_types) or
                           (UNIT_TYPEID.ZERG_GREATERSPIRE.value in self_active_unit_types))
      else:
        pre_build_cond &= (build in self_active_unit_types)
    res &= pre_build_cond
  if tech_id is not None:
    # check research ab whether already in upgraded techs
    upgraded_techs = obs.observation.raw_data.player.upgrade_ids
    res &= (tech_id not in upgraded_techs)
  # mostly used for research ability
  if unique_ab_id is not None:
    # check if the ab has already been issued
    exec_u = [u for u in units if u.unit_type in tps and u.alliance == alliance]
    for u in exec_u:
      res &= (unique_ab_id not in [o.ability_id for o in u.orders])
  return res


def true_ab_mask_fn(obs):
  return True


def attack_ab_mask_fn(obs):
  return any([(u.unit_type not in BUILDINGS_SET.union([UNIT_TYPEID.ZERG_LARVA.value]) or
               u.unit_type in [UNIT_TYPEID.ZERG_SPINECRAWLER.value,
                               UNIT_TYPEID.ZERG_SPORECRAWLER.value]) and
              u.alliance == ALLIANCE.SELF.value
              for u in obs.observation.raw_data.units])


def cancel_ab_mask_fn(obs):
  return any([((1 > u.build_progress > 0) or
               (len(u.orders) > 0 and (1 > u.orders[0].progress > 0 or
                                       u.orders[0].ability_id in MORPH_ABILITY_IDS))) and
              u.alliance == ALLIANCE.SELF.value
              for u in obs.observation.raw_data.units])


# def cancel_last_ab_mask_fn(obs):
#   return any([len(u.orders) > 0 and
#               u.orders[-1].ability_id in RESEARCH_ABILITY_IDS+[1632] and
#               u.alliance == ALLIANCE.SELF.value
#               for u in obs.observation.raw_data.units])
def cancel_last_ab_mask_fn(obs):
  return cancel_ab_mask_fn(obs)


def base_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=BASES_SET)


def egg_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=EGGS_SET)


def abduct_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_VIPER.value, energy=75)


def injectlarva_rule_ab_mask_fn(obs, activate=False):
  res = basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_QUEEN.value, energy=25)
  if not activate:
    return res
  """
  471 - 484: buff_duration_remain and buff_duration_max not available
  486 - 4100: buff_duration_remain and buff_duration_max available
  """
  res &= any([u.unit_type in BASES_SET and
              (len(u.buff_ids) == 0 or
               u.buff_ids[0] != BUFF_ID.QUEENSPAWNLARVATIMER.value or
               u.buff_duration_remain/(u.buff_duration_max+1e-10) < 0.1) and
              u.alliance == ALLIANCE.SELF.value for u in obs.observation.raw_data.units])
  return res


def injectlarva_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_QUEEN.value, energy=25)


def transfusion_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_QUEEN.value, energy=50)


def viperconsume_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_VIPER.value)


def load_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=[
    UNIT_TYPEID.ZERG_OVERLORDTRANSPORT.value,
    UNIT_TYPEID.ZERG_NYDUSNETWORK.value,
    UNIT_TYPEID.ZERG_NYDUSCANAL.value])


def nydus_network_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_NYDUSNETWORK.value)


def nydus_worm_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_NYDUSCANAL.value)


def overlord_trans_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_OVERLORDTRANSPORT.value)


def neuralparasite_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_INFESTOR.value, energy=100)


def parasiticbomb_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_VIPER.value, energy=125)


def causticspray_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_CORRUPTOR.value)


def contaminate_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_OVERSEER.value, energy=125)


def build_extractor_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_DRONE.value, mineral=25)


def harvest_gather_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_DRONE.value)


def blindingcloud_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_VIPER.value, energy=100)


def corrosivebile_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_RAVAGER.value)


def fungalgrowth_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_INFESTOR.value, energy=75)


def infestedterrans_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_INFESTOR.value, energy=25)


def locustswoop_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_LOCUSTMP.value)


def spawnlocusts_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_SWARMHOSTMP.value)


def rally_building_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=BUILDINGS_SET)


def overlord_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_OVERLORD.value)


def build_hatchery_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_DRONE.value, mineral=300)


def queen_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_QUEEN.value)


def queen_tumor_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_QUEEN.value, energy=25)


def tumorburrowed_ab_mask_fn(obs):
  """ Notice: only CREEPTUMORBURROWED can build tumor; see typeenums;
  ZERG_CREEPTUMOR and ZERG_CREEPTUMORQUEEN can only do CANCEL
  """
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_CREEPTUMORBURROWED.value)


def build_banelingnest_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_DRONE.value, mineral=100, vespene=50,
                            pre_build=UNIT_TYPEID.ZERG_SPAWNINGPOOL.value)


def build_evolutionchamber_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_DRONE.value, mineral=75)


def build_hydraliskden_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_DRONE.value, mineral=100, vespene=100,
                            pre_build=UNIT_TYPEID.ZERG_LAIR.value)


def build_infestationpit_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_DRONE.value, mineral=100, vespene=100,
                            pre_build=UNIT_TYPEID.ZERG_LAIR.value)


def build_lurkerden_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_DRONE.value, mineral=100, vespene=150,
                            pre_build=UNIT_TYPEID.ZERG_HYDRALISKDEN.value)


def build_nydusnetwork_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_DRONE.value, mineral=150, vespene=150,
                            pre_build=UNIT_TYPEID.ZERG_LAIR.value)


def build_nydusworm_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_NYDUSNETWORK.value, mineral=50, vespene=50)


def build_roachwarren_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_DRONE.value, mineral=150,
                            pre_build=UNIT_TYPEID.ZERG_SPAWNINGPOOL.value)


def build_spawningpool_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_DRONE.value, mineral=200,
                            pre_build=UNIT_TYPEID.ZERG_HATCHERY.value)


def build_spinecrawler_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_DRONE.value, mineral=100,
                            pre_build=UNIT_TYPEID.ZERG_SPAWNINGPOOL.value)


def build_spire_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_DRONE.value, mineral=200, vespene=200,
                            pre_build=UNIT_TYPEID.ZERG_LAIR.value)


def build_sporecrawler_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_DRONE.value, mineral=75,
                            pre_build=UNIT_TYPEID.ZERG_SPAWNINGPOOL.value)


def build_ultraliskcavern_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_DRONE.value, mineral=150, vespene=200,
                            pre_build=UNIT_TYPEID.ZERG_HIVE.value)


def spinecrawlerroot_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_SPINECRAWLERUPROOTED.value)


def sporecrawlerroot_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_SPORECRAWLERUPROOTED.value)


def spinecrawleruproot_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_SPINECRAWLER.value)


def sporecrawleruproot_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_SPORECRAWLER.value)


def spawnchangeling_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_OVERSEER.value, energy=50)


def explode_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=[UNIT_TYPEID.ZERG_BANELING.value,
                                     UNIT_TYPEID.ZERG_BANELINGBURROWED.value])


def burrowdown_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=GROUND_UNITS_SET, pre_tech=UPGRADE_ID.BURROW.value)


def burrowup_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=GROUND_UNITS_BURROWED_SET)


def lurker_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_LURKERMP.value)


def lurkerburrowed_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_LURKERMPBURROWED.value)


def morph_broodlord_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_CORRUPTOR.value, mineral=150, vespene=150, food=2,
                            pre_build=UNIT_TYPEID.ZERG_GREATERSPIRE.value)


def morph_greaterspire_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_SPIRE.value, mineral=100, vespene=150,
                            pre_build=UNIT_TYPEID.ZERG_HIVE.value, req_free=True)


def morph_hive_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_LAIR.value, mineral=200, vespene=150,
                            pre_build=UNIT_TYPEID.ZERG_INFESTATIONPIT.value, req_free=True)


def morph_lair_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_HATCHERY.value, mineral=150, vespene=100,
                            pre_build=UNIT_TYPEID.ZERG_SPAWNINGPOOL.value, req_free=True)


def morph_lurker_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_HYDRALISK.value, mineral=50, vespene=100, food=1,
                            pre_build=UNIT_TYPEID.ZERG_LURKERDENMP.value)


def morph_lurkerden_ab_mask_fn(obs):
  return build_lurkerden_ab_mask_fn(obs)


def morph_overlordtransport_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_OVERLORD.value, mineral=25, vespene=25,
                            pre_build=UNIT_TYPEID.ZERG_LAIR.value)


def morph_overseer_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_OVERLORD.value, mineral=50, vespene=50,
                            pre_build=UNIT_TYPEID.ZERG_LAIR.value)


def overseer_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_OVERSEER.value)


def overseeroversight_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_OVERSEEROVERSIGHTMODE.value)


def morph_ravager_ab_mask_fn(obs, ban=False, enemy_air=False, rr_food_cap=40):
  if ban and ban_rr_fn(obs, enemy_air, rr_food_cap):
    return False
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_ROACH.value, mineral=25, vespene=75, food=1,
                            pre_build=UNIT_TYPEID.ZERG_ROACHWARREN.value)


def research_burrow_ab_mask_fn(obs):
  res = basic_ab_filter_fn(obs, tp=BASES_SET, mineral=100, vespene=100,
                           unique_ab_id=ABILITY_ID.RESEARCH_BURROW.value,
                           tech_id=UPGRADE_ID.BURROW.value)
  res &= any([u.unit_type in BASES_SET and
              u.alliance == ALLIANCE.SELF.value and
              u.build_progress == 1.0 and
              (len(u.orders) == 0 or u.orders[0].ability_id not in
               [ABILITY_ID.MORPH_LAIR.value, ABILITY_ID.MORPH_HIVE.value])
              for u in obs.observation.raw_data.units])
  return res


def research_centrifugalhooks_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_BANELINGNEST.value, mineral=150, vespene=150,
                            pre_build=[UNIT_TYPEID.ZERG_LAIR.value, UNIT_TYPEID.ZERG_BANELINGNEST.value],
                            unique_ab_id=ABILITY_ID.RESEARCH_CENTRIFUGALHOOKS.value,
                            tech_id=UPGRADE_ID.CENTRIFICALHOOKS.value)


def research_chitinousplating_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_ULTRALISKCAVERN.value, mineral=150, vespene=150,
                            pre_build=UNIT_TYPEID.ZERG_ULTRALISKCAVERN.value,
                            unique_ab_id=ABILITY_ID.RESEARCH_CHITINOUSPLATING.value,
                            tech_id=UPGRADE_ID.CHITINOUSPLATING.value)


def research_glialregeneration_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_ROACHWARREN.value, mineral=100, vespene=100,
                            pre_build=[UNIT_TYPEID.ZERG_LAIR.value, UNIT_TYPEID.ZERG_ROACHWARREN.value],
                            unique_ab_id=ABILITY_ID.RESEARCH_GLIALREGENERATION.value,
                            tech_id=UPGRADE_ID.GLIALRECONSTITUTION.value)


def research_muscularaugments_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_HYDRALISKDEN.value, mineral=100, vespene=100,
                            pre_build=[UNIT_TYPEID.ZERG_LAIR.value, UNIT_TYPEID.ZERG_HYDRALISKDEN.value],
                            unique_ab_id=ABILITY_ID.RESEARCH_MUSCULARAUGMENTS.value,
                            tech_id=UPGRADE_ID.EVOLVEMUSCULARAUGMENTS.value)


def research_neuralparasite_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_INFESTATIONPIT.value, mineral=150, vespene=150,
                            pre_build=UNIT_TYPEID.ZERG_INFESTATIONPIT.value,
                            unique_ab_id=ABILITY_ID.RESEARCH_NEURALPARASITE.value,
                            tech_id=UPGRADE_ID.NEURALPARASITE.value)


def research_tunnelingclaws_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_ROACHWARREN.value, mineral=150, vespene=150,
                            pre_build=[UNIT_TYPEID.ZERG_LAIR.value, UNIT_TYPEID.ZERG_ROACHWARREN.value],
                            unique_ab_id=ABILITY_ID.RESEARCH_TUNNELINGCLAWS.value,
                            tech_id=UPGRADE_ID.TUNNELINGCLAWS.value)


def research_groovedspines_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_HYDRALISKDEN.value, mineral=100, vespene=100,
                            pre_build=UNIT_TYPEID.ZERG_HYDRALISKDEN.value,
                            unique_ab_id=ABILITY_ID.RESEARCH_GROOVEDSPINES.value,
                            tech_id=UPGRADE_ID.EVOLVEGROOVEDSPINES.value)


def research_adaptivetalons_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_LURKERDENMP.value, mineral=150, vespene=150,
                            pre_build=[UNIT_TYPEID.ZERG_HIVE.value, UNIT_TYPEID.ZERG_LURKERDENMP.value],
                            unique_ab_id=ABILITY_ID.RESEARCH_ADAPTIVETALONS.value,
                            tech_id=UPGRADE_ID.ADAPTIVETALONS.value)


def research_pathogenglands_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_INFESTATIONPIT.value, mineral=150, vespene=150,
                            pre_build=UNIT_TYPEID.ZERG_INFESTATIONPIT.value,
                            unique_ab_id=ABILITY_ID.RESEARCH_PATHOGENGLANDS.value,
                            tech_id=UPGRADE_ID.INFESTORENERGYUPGRADE.value)


def research_pneumatizedcarapace_ab_mask_fn(obs):
  res = basic_ab_filter_fn(obs, tp=BASES_SET, mineral=100, vespene=100,
                           unique_ab_id=ABILITY_ID.RESEARCH_PNEUMATIZEDCARAPACE.value,
                           tech_id=UPGRADE_ID.OVERLORDSPEED.value)
  res &= any([u.unit_type in BASES_SET and
              u.alliance == ALLIANCE.SELF.value and
              u.build_progress == 1.0 and
              (len(u.orders) == 0 or u.orders[0].ability_id not in
               [ABILITY_ID.MORPH_LAIR.value, ABILITY_ID.MORPH_HIVE.value])
              for u in obs.observation.raw_data.units])
  return res


def research_evolveanabolicsynthesis2_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_ULTRALISKCAVERN.value, mineral=150, vespene=150,
                            pre_build=UNIT_TYPEID.ZERG_ULTRALISKCAVERN.value,
                            unique_ab_id=ABILITY_ID.RESEARCH_EVOLVEANABOLICSYNTHESIS2.value,
                            tech_id=UPGRADE_ID.EVOLVEANABOLICSYNTHESIS.value)


def research_zergflyerarmor_ab_mask_fn(obs):
  upgraded_techs = obs.observation.raw_data.player.upgrade_ids
  if UPGRADE_ID.ZERGFLYERARMORSLEVEL1.value not in upgraded_techs:
    return basic_ab_filter_fn(obs, tp=[UNIT_TYPEID.ZERG_SPIRE.value,
                                       UNIT_TYPEID.ZERG_GREATERSPIRE.value],
                              mineral=150, vespene=150,
                              pre_build=UNIT_TYPEID.ZERG_SPIRE.value,
                              unique_ab_id=ABILITY_ID.RESEARCH_ZERGFLYERARMORLEVEL1.value,
                              tech_id=UPGRADE_ID.ZERGFLYERARMORSLEVEL1.value)
  elif UPGRADE_ID.ZERGFLYERARMORSLEVEL2.value not in upgraded_techs:
    return basic_ab_filter_fn(obs, tp=[UNIT_TYPEID.ZERG_SPIRE.value,
                                       UNIT_TYPEID.ZERG_GREATERSPIRE.value],
                              mineral=225, vespene=225,
                              pre_build=[UNIT_TYPEID.ZERG_LAIR.value, UNIT_TYPEID.ZERG_SPIRE.value],
                              unique_ab_id=ABILITY_ID.RESEARCH_ZERGFLYERARMORLEVEL2.value,
                              tech_id=UPGRADE_ID.ZERGFLYERARMORSLEVEL2.value)
  elif UPGRADE_ID.ZERGFLYERARMORSLEVEL3.value not in upgraded_techs:
    return basic_ab_filter_fn(obs, tp=[UNIT_TYPEID.ZERG_SPIRE.value,
                                       UNIT_TYPEID.ZERG_GREATERSPIRE.value],
                              mineral=300, vespene=300,
                              pre_build=[UNIT_TYPEID.ZERG_HIVE.value, UNIT_TYPEID.ZERG_SPIRE.value],
                              unique_ab_id=ABILITY_ID.RESEARCH_ZERGFLYERARMORLEVEL3.value,
                              tech_id=UPGRADE_ID.ZERGFLYERARMORSLEVEL3.value)
  else:
    return False


def research_zergflyerattack_ab_mask_fn(obs):
  upgraded_techs = obs.observation.raw_data.player.upgrade_ids
  if UPGRADE_ID.ZERGFLYERWEAPONSLEVEL1.value not in upgraded_techs:
    return basic_ab_filter_fn(obs, tp=[UNIT_TYPEID.ZERG_SPIRE.value,
                                       UNIT_TYPEID.ZERG_GREATERSPIRE.value],
                              mineral=100, vespene=100,
                              pre_build=UNIT_TYPEID.ZERG_SPIRE.value,
                              unique_ab_id=ABILITY_ID.RESEARCH_ZERGFLYERATTACKLEVEL1.value,
                              tech_id=UPGRADE_ID.ZERGFLYERWEAPONSLEVEL1.value)
  elif UPGRADE_ID.ZERGFLYERWEAPONSLEVEL2.value not in upgraded_techs:
    return basic_ab_filter_fn(obs, tp=[UNIT_TYPEID.ZERG_SPIRE.value,
                                       UNIT_TYPEID.ZERG_GREATERSPIRE.value],
                              mineral=175, vespene=175,
                              pre_build=[UNIT_TYPEID.ZERG_LAIR.value, UNIT_TYPEID.ZERG_SPIRE.value],
                              unique_ab_id=ABILITY_ID.RESEARCH_ZERGFLYERATTACKLEVEL2.value,
                              tech_id=UPGRADE_ID.ZERGFLYERWEAPONSLEVEL2.value)
  elif UPGRADE_ID.ZERGFLYERWEAPONSLEVEL3.value not in upgraded_techs:
    return basic_ab_filter_fn(obs, tp=[UNIT_TYPEID.ZERG_SPIRE.value,
                                       UNIT_TYPEID.ZERG_GREATERSPIRE.value],
                              mineral=250, vespene=250,
                              pre_build=[UNIT_TYPEID.ZERG_HIVE.value, UNIT_TYPEID.ZERG_SPIRE.value],
                              unique_ab_id=ABILITY_ID.RESEARCH_ZERGFLYERATTACKLEVEL3.value,
                              tech_id=UPGRADE_ID.ZERGFLYERWEAPONSLEVEL3.value)
  else:
    return False


def research_zerggroundarmor_ab_mask_fn(obs):
  upgraded_techs = obs.observation.raw_data.player.upgrade_ids
  if UPGRADE_ID.ZERGGROUNDARMORSLEVEL1.value not in upgraded_techs:
    return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_EVOLUTIONCHAMBER.value,
                              mineral=150, vespene=150,
                              pre_build=UNIT_TYPEID.ZERG_EVOLUTIONCHAMBER.value,
                              unique_ab_id=ABILITY_ID.RESEARCH_ZERGGROUNDARMORLEVEL1.value,
                              tech_id=UPGRADE_ID.ZERGGROUNDARMORSLEVEL1.value)
  elif UPGRADE_ID.ZERGGROUNDARMORSLEVEL2.value not in upgraded_techs:
    return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_EVOLUTIONCHAMBER.value,
                              mineral=225, vespene=225,
                              pre_build=[UNIT_TYPEID.ZERG_LAIR.value, UNIT_TYPEID.ZERG_EVOLUTIONCHAMBER.value],
                              unique_ab_id=ABILITY_ID.RESEARCH_ZERGGROUNDARMORLEVEL2.value,
                              tech_id=UPGRADE_ID.ZERGGROUNDARMORSLEVEL2.value)
  elif UPGRADE_ID.ZERGGROUNDARMORSLEVEL3.value not in upgraded_techs:
    return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_EVOLUTIONCHAMBER.value,
                              mineral=300, vespene=300,
                              pre_build=[UNIT_TYPEID.ZERG_HIVE.value, UNIT_TYPEID.ZERG_EVOLUTIONCHAMBER.value],
                              unique_ab_id=ABILITY_ID.RESEARCH_ZERGGROUNDARMORLEVEL3.value,
                              tech_id=UPGRADE_ID.ZERGGROUNDARMORSLEVEL3.value)
  else:
    return False


def research_zergmeleeweapons_ab_mask_fn(obs):
  upgraded_techs = obs.observation.raw_data.player.upgrade_ids
  if UPGRADE_ID.ZERGMELEEWEAPONSLEVEL1.value not in upgraded_techs:
    return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_EVOLUTIONCHAMBER.value,
                              mineral=100, vespene=100,
                              pre_build=UNIT_TYPEID.ZERG_EVOLUTIONCHAMBER.value,
                              unique_ab_id=ABILITY_ID.RESEARCH_ZERGMELEEWEAPONSLEVEL1.value,
                              tech_id=UPGRADE_ID.ZERGMELEEWEAPONSLEVEL1.value)
  elif UPGRADE_ID.ZERGMELEEWEAPONSLEVEL2.value not in upgraded_techs:
    return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_EVOLUTIONCHAMBER.value,
                              mineral=150, vespene=150,
                              pre_build=[UNIT_TYPEID.ZERG_LAIR.value, UNIT_TYPEID.ZERG_EVOLUTIONCHAMBER.value],
                              unique_ab_id=ABILITY_ID.RESEARCH_ZERGMELEEWEAPONSLEVEL2.value,
                              tech_id=UPGRADE_ID.ZERGMELEEWEAPONSLEVEL2.value)
  elif UPGRADE_ID.ZERGMELEEWEAPONSLEVEL3.value not in upgraded_techs:
    return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_EVOLUTIONCHAMBER.value,
                              mineral=200, vespene=200,
                              pre_build=[UNIT_TYPEID.ZERG_HIVE.value, UNIT_TYPEID.ZERG_EVOLUTIONCHAMBER.value],
                              unique_ab_id=ABILITY_ID.RESEARCH_ZERGMELEEWEAPONSLEVEL3.value,
                              tech_id=UPGRADE_ID.ZERGMELEEWEAPONSLEVEL3.value)
  else:
    return False


def research_zergmissileweapons_ab_mask_fn(obs):
  upgraded_techs = obs.observation.raw_data.player.upgrade_ids
  if UPGRADE_ID.ZERGMISSILEWEAPONSLEVEL1.value not in upgraded_techs:
    return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_EVOLUTIONCHAMBER.value,
                              mineral=100, vespene=100,
                              pre_build=UNIT_TYPEID.ZERG_EVOLUTIONCHAMBER.value,
                              unique_ab_id=ABILITY_ID.RESEARCH_ZERGMISSILEWEAPONSLEVEL1.value,
                              tech_id=UPGRADE_ID.ZERGMISSILEWEAPONSLEVEL1.value)
  elif UPGRADE_ID.ZERGMISSILEWEAPONSLEVEL2.value not in upgraded_techs:
    return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_EVOLUTIONCHAMBER.value,
                              mineral=150, vespene=150,
                              pre_build=[UNIT_TYPEID.ZERG_LAIR.value, UNIT_TYPEID.ZERG_EVOLUTIONCHAMBER.value],
                              unique_ab_id=ABILITY_ID.RESEARCH_ZERGMISSILEWEAPONSLEVEL2.value,
                              tech_id=UPGRADE_ID.ZERGMISSILEWEAPONSLEVEL2.value)
  elif UPGRADE_ID.ZERGMISSILEWEAPONSLEVEL3.value not in upgraded_techs:
    return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_EVOLUTIONCHAMBER.value,
                              mineral=200, vespene=200,
                              pre_build=[UNIT_TYPEID.ZERG_HIVE.value, UNIT_TYPEID.ZERG_EVOLUTIONCHAMBER.value],
                              unique_ab_id=ABILITY_ID.RESEARCH_ZERGMISSILEWEAPONSLEVEL3.value,
                              tech_id=UPGRADE_ID.ZERGMISSILEWEAPONSLEVEL3.value)
  else:
    return False


def research_zerglingadrenalglands_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_SPAWNINGPOOL.value, mineral=200, vespene=200,
                            pre_build=[UNIT_TYPEID.ZERG_HIVE.value, UNIT_TYPEID.ZERG_SPAWNINGPOOL.value],
                            unique_ab_id=ABILITY_ID.RESEARCH_ZERGLINGADRENALGLANDS.value,
                            tech_id=UPGRADE_ID.ZERGLINGATTACKSPEED.value)


def research_zerglingmetabolicboost_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_SPAWNINGPOOL.value, mineral=100, vespene=100,
                            pre_build=UNIT_TYPEID.ZERG_SPAWNINGPOOL.value,
                            unique_ab_id=ABILITY_ID.RESEARCH_ZERGLINGMETABOLICBOOST.value,
                            tech_id=UPGRADE_ID.ZERGLINGMOVEMENTSPEED.value)


def morph_baneling_ab_mask_fn(obs, ban=False, zb_food_cap=10):
  if ban and ban_zb_fn(obs, zb_food_cap):
    return False
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_ZERGLING.value, mineral=25, vespene=25,
                            pre_build=UNIT_TYPEID.ZERG_BANELINGNEST.value)


def train_corruptor_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_LARVA.value, mineral=150, vespene=100, food=2,
                            pre_build=UNIT_TYPEID.ZERG_SPIRE.value)


def train_drone_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_LARVA.value, mineral=50, food=1)


def train_hydralisk_ab_mask_fn(obs, ban=False, enemy_air=False, hydra_food_cap=10):
  if ban and ban_hydra_fn(obs, enemy_air, hydra_food_cap):
    return False
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_LARVA.value, mineral=100, vespene=50, food=2,
                            pre_build=UNIT_TYPEID.ZERG_HYDRALISKDEN.value)


def train_infestor_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_LARVA.value, mineral=100, vespene=150, food=2,
                            pre_build=UNIT_TYPEID.ZERG_INFESTATIONPIT.value)


def train_mutalisk_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_LARVA.value, mineral=100, vespene=100, food=2,
                            pre_build=UNIT_TYPEID.ZERG_SPIRE.value)


def train_overlord_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_LARVA.value, mineral=100)


def train_queen_ab_mask_fn(obs):
  res = basic_ab_filter_fn(obs, tp=BASES_SET, mineral=150,  # queen can be queued, even for the first
                           pre_build=UNIT_TYPEID.ZERG_SPAWNINGPOOL.value)
  res &= any([u.unit_type in BASES_SET and
              u.alliance == ALLIANCE.SELF.value and
              u.build_progress == 1.0 and
              (len(u.orders) == 0 or u.orders[0].ability_id not in
               [ABILITY_ID.MORPH_LAIR.value, ABILITY_ID.MORPH_HIVE.value])
              for u in obs.observation.raw_data.units])
  return res


def train_roach_ab_mask_fn(obs, ban=False, enemy_air=False, rr_food_cap=40):
  if ban and ban_rr_fn(obs, enemy_air, rr_food_cap):
    return False
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_LARVA.value, mineral=75, vespene=25, food=2,
                            pre_build=UNIT_TYPEID.ZERG_ROACHWARREN.value)


def train_swarmhost_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_LARVA.value, mineral=100, vespene=75, food=3,
                            pre_build=UNIT_TYPEID.ZERG_INFESTATIONPIT.value)


def train_ultralisk_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_LARVA.value, mineral=300, vespene=200, food=6,
                            pre_build=UNIT_TYPEID.ZERG_ULTRALISKCAVERN.value)


def train_viper_ab_mask_fn(obs):
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_LARVA.value, mineral=100, vespene=200, food=3,
                            pre_build=[UNIT_TYPEID.ZERG_SPIRE.value, UNIT_TYPEID.ZERG_HIVE.value])


def train_zergling_ab_mask_fn(obs, ban=False, zb_food_cap=10):
  if ban and ban_zb_fn(obs, zb_food_cap):
    return False
  return basic_ab_filter_fn(obs, tp=UNIT_TYPEID.ZERG_LARVA.value, mineral=50, food=1,
                            pre_build=UNIT_TYPEID.ZERG_SPAWNINGPOOL.value)


""" position mask func """
def base_pos_mask_fn(obs, game_info, flip):
  placement_grid = norm_img(bitmap2array(game_info.start_raw.placement_grid))
  pathing_grid = norm_img(bitmap2array(game_info.start_raw.pathing_grid))
  # TODO: can give more rules for base position
  # 0=Hidden, 1=Fogged, 2=Visible, 3=FullHidden
  # visibility = bitmap2array(obs.observation.raw_data.map_state.visibility)
  # visibility = np.equal(visibility, 1) + np.equal(visibility, 2)
  # mask = placement_grid * visibility
  if not flip:
    mask = placement_grid * (1.0 - pathing_grid)
  else:
    mask = placement_grid * pathing_grid
  mask = np.array(mask, dtype=np.bool)
  if flip:
    return mask[::-1]
  else:
    return mask


def creep_pos_mask_fn(obs, game_info, flip):
  placement_grid = norm_img(bitmap2array(game_info.start_raw.placement_grid))
  pathing_grid = norm_img(bitmap2array(game_info.start_raw.pathing_grid))
  creep = norm_img(bitmap2array(obs.observation.raw_data.map_state.creep))
  # 0=Hidden, 1=Fogged, 2=Visible, 3=FullHidden
  # visibility = bitmap2array(obs.observation.raw_data.map_state.visibility)
  # visibility = np.equal(visibility, 2)
  if not flip:
    mask = placement_grid * (1.0 - pathing_grid) * creep
  else:
    mask = placement_grid * pathing_grid * creep
  mask = np.array(mask, dtype=np.bool)
  if flip:
    return mask[::-1]
  else:
    return mask


def tumor_pos_mask_fn(obs, game_info, flip):
  pathing_grid = norm_img(bitmap2array(game_info.start_raw.pathing_grid))
  creep = norm_img(bitmap2array(obs.observation.raw_data.map_state.creep))
  # 0=Hidden, 1=Fogged, 2=Visible, 3=FullHidden
  # visibility = bitmap2array(obs.observation.raw_data.map_state.visibility)
  # visibility = np.equal(visibility, 2)
  if not flip:
    mask = (1.0 - pathing_grid) * creep
  else:
    mask = pathing_grid * creep
  mask = np.array(mask, dtype=np.bool)
  if flip:
    return mask[::-1]
  else:
    return mask


def nydus_pos_mask_fn(obs, game_info, flip):
  placement_grid = norm_img(bitmap2array(game_info.start_raw.placement_grid))
  pathing_grid = norm_img(bitmap2array(game_info.start_raw.pathing_grid))
  # 0=Hidden, 1=Fogged, 2=Visible, 3=FullHidden
  visibility = bitmap2array(obs.observation.raw_data.map_state.visibility)
  visibility = np.equal(visibility, 2)
  if not flip:
    mask = placement_grid * (1.0 - pathing_grid) * visibility
  else:
    mask = placement_grid * pathing_grid * visibility
  mask = np.array(mask, dtype=np.bool)
  if flip:
    return mask[::-1]
  else:
    return mask


def base_pos_mask_fn_new(minimaps):
  return minimaps.buildable * minimaps.pathable


def creep_pos_mask_fn_new(minimaps):
  return minimaps.buildable * minimaps.pathable * minimaps.creep


def tumor_pos_mask_fn_new(minimaps):
  return minimaps.pathable * minimaps.creep


def nydus_pos_mask_fn_new(minimaps):
  return minimaps.buildable * minimaps.pathable * (minimaps.visibility_map == 2)

def hidden_pos_mask_fn(minimaps, map_name='KairosJunction'):
  hidden_pos_mask = np.equal(np.array(minimaps.visibility_map), 0)  # hidden mask
  pos0, pos1 = MAP_PLAYABLE_AREA_DICT[map_name]
  pos0_x, pos0_y = pos0
  pos1_x, pos1_y = pos1
  hidden_pos_mask[:, 0:pos0_x] = 0
  hidden_pos_mask[:, pos1_x:] = 0
  hidden_pos_mask[-pos0_y:, :] = 0
  hidden_pos_mask[:-pos1_y, :] = 0
  return hidden_pos_mask


def hidden_base_mask_fn(obs, minimaps, map_name='KairosJunction'):
  hidden_pos_mask = np.equal(np.array(minimaps.visibility_map), 0)  # hidden mask
  hidden_base_mask = np.zeros_like(np.array(hidden_pos_mask), dtype=np.bool)
  map_ori_size = (obs.observation.raw_data.map_state.creep.size.x,
                  obs.observation.raw_data.map_state.creep.size.y)
  ori_x, ori_y = map_ori_size
  for pos in KJ_IDEAL_BASE_POS:
    pos_x, pos_y = pos
    if hidden_pos_mask[ori_y - 1 - int(pos_y), int(pos_x)] == 1:
      hidden_base_mask[ori_y - 1 - int(pos_y), int(pos_x)] = True
  return hidden_base_mask


def unknown_base_mask_fn(obs, minimaps, visit_time: dict,
                         map_name='KairosJunction'):
  hidden_pos_mask = np.equal(np.array(minimaps.visibility_map), 0)  # hidden mask
  tar_base_mask = np.zeros_like(np.array(hidden_pos_mask), dtype=np.bool)
  map_ori_size = (obs.observation.raw_data.map_state.creep.size.x,
                  obs.observation.raw_data.map_state.creep.size.y)
  ori_x, ori_y = map_ori_size
  last_visit_duration_list = []
  for pos in KJ_IDEAL_BASE_POS:
    pos_x, pos_y = pos
    if str(pos_x)+','+str(pos_y) in visit_time:
      last_visit_duration_list.append(
          obs.observation.game_loop -
          visit_time[str(pos_x)+','+str(pos_y)])
    else:
      last_visit_duration_list.append(obs.observation.game_loop)
  if len(last_visit_duration_list) > 0 and \
     max(last_visit_duration_list) > 22.4*60*2:  # a base more than 2 minutes unseen
    idx = last_visit_duration_list.index(max(last_visit_duration_list))
    tar_pos_x, tar_pos_y = KJ_IDEAL_BASE_POS[idx]
    tar_base_mask[ori_y - 1 - int(tar_pos_y), int(tar_pos_x)] = True
  return tar_base_mask


def zero_pos_mask_fn(obs, game_info):
  placement_grid = norm_img(bitmap2array(game_info.start_raw.placement_grid))
  mask = np.zeros_like(placement_grid, dtype=np.bool)
  return mask


def one_pos_mask_fn(obs, game_info):
  placement_grid = norm_img(bitmap2array(game_info.start_raw.placement_grid))
  mask = np.ones_like(placement_grid, dtype=np.bool)
  return mask


""" unit mask func """
def zero_unit_mask_fn(x):
  return np.zeros(shape=(len(x),), dtype=np.bool)
zero_type_mask = np.zeros_like(ALL_UNIT_TYPES, dtype=np.bool)


def one_unit_mask_fn(x):
  return np.ones(shape=(len(x),), dtype=np.bool)
one_type_mask = np.ones_like(ALL_UNIT_TYPES, dtype=np.bool)


# single type
def larva_unit_mask_fn(x):
  return np.asarray([u.unit_type == UNIT_TYPEID.ZERG_LARVA.value and u.alliance == ALLIANCE.SELF.value for u in x], dtype=np.bool)
larva_type_mask = np.zeros_like(ALL_UNIT_TYPES, dtype=np.bool)
larva_type_mask[ALL_UNIT_TYPES.index(UNIT_TYPEID.ZERG_LARVA.value)] = True


def drone_unit_mask_fn(x):
  return np.asarray([u.unit_type == UNIT_TYPEID.ZERG_DRONE.value and u.alliance == ALLIANCE.SELF.value for u in x], dtype=np.bool)
drone_type_mask = np.zeros_like(ALL_UNIT_TYPES, dtype=np.bool)
drone_type_mask[ALL_UNIT_TYPES.index(UNIT_TYPEID.ZERG_DRONE.value)] = True


def queen_unit_mask_fn(x):
  return np.asarray([u.unit_type == UNIT_TYPEID.ZERG_QUEEN.value and u.alliance == ALLIANCE.SELF.value for u in x], dtype=np.bool)
queen_type_mask = np.zeros_like(ALL_UNIT_TYPES, dtype=np.bool)
queen_type_mask[ALL_UNIT_TYPES.index(UNIT_TYPEID.ZERG_QUEEN.value)] = True


def viper_unit_mask_fn(x):
  return np.asarray([u.unit_type == UNIT_TYPEID.ZERG_VIPER.value and u.alliance == ALLIANCE.SELF.value for u in x], dtype=np.bool)
viper_type_mask = np.zeros_like(ALL_UNIT_TYPES, dtype=np.bool)
viper_type_mask[ALL_UNIT_TYPES.index(UNIT_TYPEID.ZERG_VIPER.value)] = True


def infestor_unit_mask_fn(x):
  return np.asarray([u.unit_type == UNIT_TYPEID.ZERG_INFESTOR.value and u.alliance == ALLIANCE.SELF.value for u in x], dtype=np.bool)
infestor_type_mask = np.zeros_like(ALL_UNIT_TYPES, dtype=np.bool)
infestor_type_mask[ALL_UNIT_TYPES.index(UNIT_TYPEID.ZERG_INFESTOR.value)] = True


def ravager_unit_mask_fn(x):
  return np.asarray([u.unit_type == UNIT_TYPEID.ZERG_RAVAGER.value and u.alliance == ALLIANCE.SELF.value for u in x], dtype=np.bool)
ravager_type_mask = np.zeros_like(ALL_UNIT_TYPES, dtype=np.bool)
ravager_type_mask[ALL_UNIT_TYPES.index(UNIT_TYPEID.ZERG_RAVAGER.value)] = True


def corruptor_unit_mask_fn(x):
  return np.asarray([u.unit_type == UNIT_TYPEID.ZERG_CORRUPTOR.value and u.alliance == ALLIANCE.SELF.value for u in x], dtype=np.bool)
corruptor_type_mask = np.zeros_like(ALL_UNIT_TYPES, dtype=np.bool)
corruptor_type_mask[ALL_UNIT_TYPES.index(UNIT_TYPEID.ZERG_CORRUPTOR.value)] = True


def overseer_unit_mask_fn(x):
  return np.asarray([u.unit_type == UNIT_TYPEID.ZERG_OVERSEER.value and u.alliance == ALLIANCE.SELF.value for u in x], dtype=np.bool)
overseer_type_mask = np.zeros_like(ALL_UNIT_TYPES, dtype=np.bool)
overseer_type_mask[ALL_UNIT_TYPES.index(UNIT_TYPEID.ZERG_OVERSEER.value)] = True


def overseeroversight_unit_mask_fn(x):
  return np.asarray([u.unit_type == UNIT_TYPEID.ZERG_OVERSEEROVERSIGHTMODE.value and u.alliance == ALLIANCE.SELF.value for u in x], dtype=np.bool)
overseeroversight_type_mask = np.zeros_like(ALL_UNIT_TYPES, dtype=np.bool)
overseeroversight_type_mask[ALL_UNIT_TYPES.index(UNIT_TYPEID.ZERG_OVERSEEROVERSIGHTMODE.value)] = True


def locust_unit_mask_fn(x):
  return np.asarray([u.unit_type == UNIT_TYPEID.ZERG_LOCUSTMP.value and u.alliance == ALLIANCE.SELF.value for u in x], dtype=np.bool)
locust_type_mask = np.zeros_like(ALL_UNIT_TYPES, dtype=np.bool)
locust_type_mask[ALL_UNIT_TYPES.index(UNIT_TYPEID.ZERG_LOCUSTMP.value)] = True


def swarmhost_unit_mask_fn(x):
  return np.asarray([u.unit_type == UNIT_TYPEID.ZERG_SWARMHOSTMP.value and u.alliance == ALLIANCE.SELF.value for u in x], dtype=np.bool)
swarmhost_type_mask = np.zeros_like(ALL_UNIT_TYPES, dtype=np.bool)
swarmhost_type_mask[ALL_UNIT_TYPES.index(UNIT_TYPEID.ZERG_SWARMHOSTMP.value)] = True


def nydus_network_unit_mask_fn(x):
  return np.asarray([u.unit_type == UNIT_TYPEID.ZERG_NYDUSNETWORK.value and u.alliance == ALLIANCE.SELF.value for u in x], dtype=np.bool)
nydusnetwork_type_mask = np.zeros_like(ALL_UNIT_TYPES, dtype=np.bool)
nydusnetwork_type_mask[ALL_UNIT_TYPES.index(UNIT_TYPEID.ZERG_NYDUSNETWORK.value)] = True


def nydus_worm_unit_mask_fn(x):
  return np.asarray([u.unit_type == UNIT_TYPEID.ZERG_NYDUSCANAL.value and u.alliance == ALLIANCE.SELF.value for u in x], dtype=np.bool)
nydusworm_type_mask = np.zeros_like(ALL_UNIT_TYPES, dtype=np.bool)
nydusworm_type_mask[ALL_UNIT_TYPES.index(UNIT_TYPEID.ZERG_NYDUSCANAL.value)] = True


def overlord_trans_unit_mask_fn(x):
  return np.asarray([u.unit_type == UNIT_TYPEID.ZERG_OVERLORDTRANSPORT.value and u.alliance == ALLIANCE.SELF.value for u in x], dtype=np.bool)
overlordtrans_type_mask = np.zeros_like(ALL_UNIT_TYPES, dtype=np.bool)
overlordtrans_type_mask[ALL_UNIT_TYPES.index(UNIT_TYPEID.ZERG_OVERLORDTRANSPORT.value)] = True


def overlord_unit_mask_fn(x):
  return np.asarray([u.unit_type == UNIT_TYPEID.ZERG_OVERLORD.value and u.alliance == ALLIANCE.SELF.value for u in x], dtype=np.bool)
overlord_type_mask = np.zeros_like(ALL_UNIT_TYPES, dtype=np.bool)
overlord_type_mask[ALL_UNIT_TYPES.index(UNIT_TYPEID.ZERG_OVERLORD.value)] = True


def lurker_unit_mask_fn(x):
  return np.asarray([u.unit_type == UNIT_TYPEID.ZERG_LURKERMP.value and u.alliance == ALLIANCE.SELF.value for u in x], dtype=np.bool)
lurker_type_mask = np.zeros_like(ALL_UNIT_TYPES, dtype=np.bool)
lurker_type_mask[ALL_UNIT_TYPES.index(UNIT_TYPEID.ZERG_LURKERMP.value)] = True


def lurker_burrowed_unit_mask_fn(x):
  return np.asarray([u.unit_type == UNIT_TYPEID.ZERG_LURKERMPBURROWED.value and u.alliance == ALLIANCE.SELF.value for u in x], dtype=np.bool)
lurkerburrowed_type_mask = np.zeros_like(ALL_UNIT_TYPES, dtype=np.bool)
lurkerburrowed_type_mask[ALL_UNIT_TYPES.index(UNIT_TYPEID.ZERG_LURKERMPBURROWED.value)] = True


def hydralisk_unit_mask_fn(x):
  return np.asarray([u.unit_type == UNIT_TYPEID.ZERG_HYDRALISK.value and u.alliance == ALLIANCE.SELF.value for u in x], dtype=np.bool)
hydralisk_type_mask = np.zeros_like(ALL_UNIT_TYPES, dtype=np.bool)
hydralisk_type_mask[ALL_UNIT_TYPES.index(UNIT_TYPEID.ZERG_HYDRALISK.value)] = True


def roach_unit_mask_fn(x):
  return np.asarray([u.unit_type == UNIT_TYPEID.ZERG_ROACH.value and u.alliance == ALLIANCE.SELF.value for u in x], dtype=np.bool)
roach_type_mask = np.zeros_like(ALL_UNIT_TYPES, dtype=np.bool)
roach_type_mask[ALL_UNIT_TYPES.index(UNIT_TYPEID.ZERG_ROACH.value)] = True


def zergling_unit_mask_fn(x):
  return np.asarray([u.unit_type == UNIT_TYPEID.ZERG_ZERGLING.value and u.alliance == ALLIANCE.SELF.value for u in x], dtype=np.bool)
zergling_type_mask = np.zeros_like(ALL_UNIT_TYPES, dtype=np.bool)
zergling_type_mask[ALL_UNIT_TYPES.index(UNIT_TYPEID.ZERG_ZERGLING.value)] = True


def spire_unit_mask_fn(x):
  return np.asarray([u.unit_type == UNIT_TYPEID.ZERG_SPIRE.value and u.alliance == ALLIANCE.SELF.value for u in x], dtype=np.bool)
spire_type_mask = np.zeros_like(ALL_UNIT_TYPES, dtype=np.bool)
spire_type_mask[ALL_UNIT_TYPES.index(UNIT_TYPEID.ZERG_SPIRE.value)] = True


def free_spire_unit_mask_fn(x):
  return np.asarray([u.unit_type == UNIT_TYPEID.ZERG_SPIRE.value and len(u.orders) == 0
                     and u.alliance == ALLIANCE.SELF.value for u in x], dtype=np.bool)


def hatchery_unit_mask_fn(x):
  return np.asarray([u.unit_type == UNIT_TYPEID.ZERG_HATCHERY.value and u.alliance == ALLIANCE.SELF.value for u in x], dtype=np.bool)
hatchery_type_mask = np.zeros_like(ALL_UNIT_TYPES, dtype=np.bool)
hatchery_type_mask[ALL_UNIT_TYPES.index(UNIT_TYPEID.ZERG_HATCHERY.value)] = True


def free_hatchery_unit_mask_fn(x):
  return np.asarray([u.unit_type == UNIT_TYPEID.ZERG_HATCHERY.value and len(u.orders) == 0
                     and u.alliance == ALLIANCE.SELF.value for u in x], dtype=np.bool)


def lair_unit_mask_fn(x):
  return np.asarray([u.unit_type == UNIT_TYPEID.ZERG_LAIR.value and u.alliance == ALLIANCE.SELF.value for u in x], dtype=np.bool)
lair_type_mask = np.zeros_like(ALL_UNIT_TYPES, dtype=np.bool)
lair_type_mask[ALL_UNIT_TYPES.index(UNIT_TYPEID.ZERG_LAIR.value)] = True



def free_lair_unit_mask_fn(x):
  return np.asarray([u.unit_type == UNIT_TYPEID.ZERG_LAIR.value and len(u.orders) == 0
                     and u.alliance == ALLIANCE.SELF.value for u in x], dtype=np.bool)


def hive_unit_mask_fn(x):
  return np.asarray([u.unit_type == UNIT_TYPEID.ZERG_HIVE.value and u.alliance == ALLIANCE.SELF.value for u in x], dtype=np.bool)
hive_type_mask = np.zeros_like(ALL_UNIT_TYPES, dtype=np.bool)
hive_type_mask[ALL_UNIT_TYPES.index(UNIT_TYPEID.ZERG_HIVE.value)] = True


def up_spine_unit_mask_fn(x):
  return np.asarray([u.unit_type == UNIT_TYPEID.ZERG_SPINECRAWLERUPROOTED.value and u.alliance == ALLIANCE.SELF.value for u in x], dtype=np.bool)
upspine_type_mask = np.zeros_like(ALL_UNIT_TYPES, dtype=np.bool)
upspine_type_mask[ALL_UNIT_TYPES.index(UNIT_TYPEID.ZERG_SPINECRAWLERUPROOTED.value)] = True


def up_spore_unit_mask_fn(x):
  return np.asarray([u.unit_type == UNIT_TYPEID.ZERG_SPORECRAWLERUPROOTED.value and u.alliance == ALLIANCE.SELF.value for u in x], dtype=np.bool)
upspore_type_mask = np.zeros_like(ALL_UNIT_TYPES, dtype=np.bool)
upspore_type_mask[ALL_UNIT_TYPES.index(UNIT_TYPEID.ZERG_SPORECRAWLERUPROOTED.value)] = True


def spine_unit_mask_fn(x):
  return np.asarray([u.unit_type == UNIT_TYPEID.ZERG_SPINECRAWLER.value and u.alliance == ALLIANCE.SELF.value for u in x], dtype=np.bool)
spine_type_mask = np.zeros_like(ALL_UNIT_TYPES, dtype=np.bool)
spine_type_mask[ALL_UNIT_TYPES.index(UNIT_TYPEID.ZERG_SPINECRAWLER.value)] = True


def spore_unit_mask_fn(x):
  return np.asarray([u.unit_type == UNIT_TYPEID.ZERG_SPORECRAWLER.value and u.alliance == ALLIANCE.SELF.value for u in x], dtype=np.bool)
spore_type_mask = np.zeros_like(ALL_UNIT_TYPES, dtype=np.bool)
spore_type_mask[ALL_UNIT_TYPES.index(UNIT_TYPEID.ZERG_SPORECRAWLER.value)] = True


def baneling_unit_mask_fn(x):
  return np.asarray([u.unit_type == UNIT_TYPEID.ZERG_BANELING.value and u.alliance == ALLIANCE.SELF.value for u in x], dtype=np.bool)
baneling_type_mask = np.zeros_like(ALL_UNIT_TYPES, dtype=np.bool)
baneling_type_mask[ALL_UNIT_TYPES.index(UNIT_TYPEID.ZERG_BANELING.value)] = True


def banelingnest_unit_mask_fn(x):
  return np.asarray([u.unit_type == UNIT_TYPEID.ZERG_BANELINGNEST.value and
                     u.build_progress == 1.0 and
                     u.alliance == ALLIANCE.SELF.value for u in x], dtype=np.bool)
banelingnest_type_mask = np.zeros_like(ALL_UNIT_TYPES, dtype=np.bool)
banelingnest_type_mask[ALL_UNIT_TYPES.index(UNIT_TYPEID.ZERG_BANELINGNEST.value)] = True


def spawningpool_unit_mask_fn(x):
  return np.asarray([u.unit_type == UNIT_TYPEID.ZERG_SPAWNINGPOOL.value and
                     u.build_progress == 1.0 and
                     u.alliance == ALLIANCE.SELF.value for u in x], dtype=np.bool)
spawningpool_type_mask = np.zeros_like(ALL_UNIT_TYPES, dtype=np.bool)
spawningpool_type_mask[ALL_UNIT_TYPES.index(UNIT_TYPEID.ZERG_SPAWNINGPOOL.value)] = True


def roachwarren_unit_mask_fn(x):
  return np.asarray([u.unit_type == UNIT_TYPEID.ZERG_ROACHWARREN.value and
                     u.build_progress == 1.0 and
                     u.alliance == ALLIANCE.SELF.value for u in x], dtype=np.bool)
roachwarren_type_mask = np.zeros_like(ALL_UNIT_TYPES, dtype=np.bool)
roachwarren_type_mask[ALL_UNIT_TYPES.index(UNIT_TYPEID.ZERG_ROACHWARREN.value)] = True


def hydraliskden_unit_mask_fn(x):
  return np.asarray([u.unit_type == UNIT_TYPEID.ZERG_HYDRALISKDEN.value and
                     u.build_progress == 1.0 and
                     u.alliance == ALLIANCE.SELF.value for u in x], dtype=np.bool)
hydraliskden_type_mask = np.zeros_like(ALL_UNIT_TYPES, dtype=np.bool)
hydraliskden_type_mask[ALL_UNIT_TYPES.index(UNIT_TYPEID.ZERG_HYDRALISKDEN.value)] = True


def infestorpit_unit_mask_fn(x):
  return np.asarray([u.unit_type == UNIT_TYPEID.ZERG_INFESTATIONPIT.value and
                     u.build_progress == 1.0 and
                     u.alliance == ALLIANCE.SELF.value for u in x], dtype=np.bool)
infestorpit_type_mask = np.zeros_like(ALL_UNIT_TYPES, dtype=np.bool)
infestorpit_type_mask[ALL_UNIT_TYPES.index(UNIT_TYPEID.ZERG_INFESTATIONPIT.value)] = True


def ultraliskcavern_unit_mask_fn(x):
  return np.asarray([u.unit_type == UNIT_TYPEID.ZERG_ULTRALISKCAVERN.value and
                     u.build_progress == 1.0 and
                     u.alliance == ALLIANCE.SELF.value for u in x], dtype=np.bool)
ultraliskcavern_type_mask = np.zeros_like(ALL_UNIT_TYPES, dtype=np.bool)
ultraliskcavern_type_mask[ALL_UNIT_TYPES.index(UNIT_TYPEID.ZERG_ULTRALISKCAVERN.value)] = True


def greatspire_unit_mask_fn(x):
  return np.asarray([u.unit_type == UNIT_TYPEID.ZERG_GREATERSPIRE.value and u.alliance == ALLIANCE.SELF.value for u in x], dtype=np.bool)
greatspire_type_mask = np.zeros_like(ALL_UNIT_TYPES, dtype=np.bool)
greatspire_type_mask[ALL_UNIT_TYPES.index(UNIT_TYPEID.ZERG_GREATERSPIRE.value)] = True


def lurkerden_unit_mask_fn(x):
  return np.asarray([u.unit_type == UNIT_TYPEID.ZERG_LURKERDENMP.value and
                     u.build_progress == 1.0 and
                     u.alliance == ALLIANCE.SELF.value for u in x], dtype=np.bool)
lurkerden_type_mask = np.zeros_like(ALL_UNIT_TYPES, dtype=np.bool)
lurkerden_type_mask[ALL_UNIT_TYPES.index(UNIT_TYPEID.ZERG_LURKERDENMP.value)] = True


def evolutionchamber_unit_mask_fn(x):
  return np.asarray([u.unit_type == UNIT_TYPEID.ZERG_EVOLUTIONCHAMBER.value and
                     u.build_progress == 1.0 and
                     u.alliance == ALLIANCE.SELF.value for u in x], dtype=np.bool)
evolutionchamber_type_mask = np.zeros_like(ALL_UNIT_TYPES, dtype=np.bool)
evolutionchamber_type_mask[ALL_UNIT_TYPES.index(UNIT_TYPEID.ZERG_EVOLUTIONCHAMBER.value)] = True


def tumorburrowed_unit_mask_fn(x):
  return np.asarray([u.unit_type == UNIT_TYPEID.ZERG_CREEPTUMORBURROWED.value and u.alliance == ALLIANCE.SELF.value for u in x], dtype=np.bool)
tumorburrowed_type_mask = np.zeros_like(ALL_UNIT_TYPES, dtype=np.bool)
tumorburrowed_type_mask[ALL_UNIT_TYPES.index(UNIT_TYPEID.ZERG_CREEPTUMORBURROWED.value)] = True


# sets
def ground_unit_mask_fn(x):
  return np.asarray([u.unit_type in GROUND_UNITS_SET and u.alliance == ALLIANCE.SELF.value for u in x], dtype=np.bool)
ground_type_mask = np.zeros_like(ALL_UNIT_TYPES, dtype=np.bool)
for tp in GROUND_UNITS_SET:
  ground_type_mask[ALL_UNIT_TYPES.index(tp)] = True



def ground_unit_burrowed_mask_fn(x):
  return np.asarray([u.unit_type in GROUND_UNITS_BURROWED_SET and u.alliance == ALLIANCE.SELF.value for u in x], dtype=np.bool)
ground_burrowed_type_mask = np.zeros_like(ALL_UNIT_TYPES, dtype=np.bool)
for tp in GROUND_UNITS_BURROWED_SET:
  ground_burrowed_type_mask[ALL_UNIT_TYPES.index(tp)] = True


def base_unit_mask_fn(x):
  return np.asarray([u.unit_type in BASES_SET and u.alliance == ALLIANCE.SELF.value for u in x], dtype=np.bool)
base_type_mask = np.zeros_like(ALL_UNIT_TYPES, dtype=np.bool)
for tp in BASES_SET:
  base_type_mask[ALL_UNIT_TYPES.index(tp)] = True


def inj_larva_base_unit_mask_fn(x, inj_larv_rule=False):
  if not inj_larv_rule:
    return base_unit_mask_fn(x)
  else:
    return np.asarray([u.unit_type in BASES_SET and
                       (len(u.buff_ids) == 0 or
                        u.buff_ids[0] != BUFF_ID.QUEENSPAWNLARVATIMER.value or
                        u.buff_duration_remain/(u.buff_duration_max+1e-10) < 0.1) and
                       u.alliance == ALLIANCE.SELF.value for u in x], dtype=np.bool)


def no_morphing_base_unit_mask_fn(x):
  return np.asarray([u.unit_type in BASES_SET and
                     u.alliance == ALLIANCE.SELF.value and
                     u.build_progress == 1.0 and
                     (len(u.orders) == 0 or u.orders[0].ability_id not in
                      [ABILITY_ID.MORPH_LAIR.value, ABILITY_ID.MORPH_HIVE.value])  # MORPH_LAIR, MORPH_HIVE
                     for u in x], dtype=np.bool)


def building_unit_mask_fn(x):
  return np.asarray([u.unit_type in BUILDINGS_SET and u.alliance == ALLIANCE.SELF.value for u in x], dtype=np.bool)
building_type_mask = np.zeros_like(ALL_UNIT_TYPES, dtype=np.bool)
for tp in BUILDINGS_SET:
  building_type_mask[ALL_UNIT_TYPES.index(tp)] = True


def viperconsume_unit_mask_fn(x):
  return np.asarray([u.unit_type in BUILDINGS_SET and
                     u.unit_type not in [UNIT_TYPEID.ZERG_CREEPTUMORBURROWED.value,
                                         UNIT_TYPEID.ZERG_CREEPTUMOR.value,
                                         UNIT_TYPEID.ZERG_CREEPTUMORQUEEN.value] and
                     u.alliance == ALLIANCE.SELF.value for u in x], dtype=np.bool)
viperconsume_type_mask = np.zeros_like(ALL_UNIT_TYPES, dtype=np.bool)
for tp in ALL_UNIT_TYPES:
  if tp in BUILDINGS_SET and tp not in [UNIT_TYPEID.ZERG_CREEPTUMORBURROWED.value,
                                        UNIT_TYPEID.ZERG_CREEPTUMOR.value,
                                        UNIT_TYPEID.ZERG_CREEPTUMORQUEEN.value]:
    viperconsume_type_mask[ALL_UNIT_TYPES.index(tp)] = True


def egg_unit_mask_fn(x):
  return np.asarray([u.unit_type in EGGS_SET and u.alliance == ALLIANCE.SELF.value for u in x], dtype=np.bool)
egg_type_mask = np.zeros_like(ALL_UNIT_TYPES, dtype=np.bool)
for tp in EGGS_SET:
  egg_type_mask[ALL_UNIT_TYPES.index(tp)] = True


def ally_unit_mask_fn(x):
  return np.asarray([u.alliance == ALLIANCE.SELF.value for u in x], dtype=np.bool)


def in_progress_unit_mask_fn(x):
  return np.asarray([((1 > u.build_progress > 0) or
                      (len(u.orders) > 0 and (1 > u.orders[0].progress > 0 or
                                              u.orders[0].ability_id in MORPH_ABILITY_IDS))) and
                     u.alliance == ALLIANCE.SELF.value for u in x], dtype=np.bool)
can_in_progress_type_mask = np.zeros_like(ALL_UNIT_TYPES, dtype=np.bool)
for tp in BUILDINGS_SET.union(EGGS_SET):
  can_in_progress_type_mask[ALL_UNIT_TYPES.index(tp)] = True


# def can_cancel_last_unit_mask_fn(x):
#   return np.asarray([len(u.orders) > 0 and
#                      u.orders[-1].ability_id in RESEARCH_ABILITY_IDS+[1632] and
#                      u.alliance == ALLIANCE.SELF.value for u in x], dtype=np.bool)
# can_cancel_last_type_mask = np.zeros_like(ALL_UNIT_TYPES, dtype=np.bool)
# for tp in RESEARCH_BUILDINGS_SET:
#   can_cancel_last_type_mask[ALL_UNIT_TYPES.index(tp)] = True
def can_cancel_last_unit_mask_fn(x):
  return in_progress_unit_mask_fn(x)
can_cancel_last_type_mask = can_in_progress_type_mask


def canattack_unit_mask_fn(x):
  return np.asarray([(u.unit_type not in BUILDINGS_SET.union([UNIT_TYPEID.ZERG_LARVA.value]) or
                      u.unit_type in [UNIT_TYPEID.ZERG_SPINECRAWLER.value,
                                      UNIT_TYPEID.ZERG_SPORECRAWLER.value]) and
                     u.alliance == ALLIANCE.SELF.value for u in x], dtype=np.bool)
canattack_type_mask = np.zeros_like(ALL_UNIT_TYPES, dtype=np.bool)
for tp in ALL_UNIT_TYPES:
  if (tp not in BUILDINGS_SET.union([UNIT_TYPEID.ZERG_LARVA.value])) or \
     (tp in [UNIT_TYPEID.ZERG_SPINECRAWLER.value,
             UNIT_TYPEID.ZERG_SPORECRAWLER.value]):
    canattack_type_mask[ALL_UNIT_TYPES.index(tp)] = True


def enemy_non_build_unit_mask_fn(x):
  return np.asarray([u.unit_type not in BUILDINGS_SET and u.alliance == ALLIANCE.ENEMY.value for u in x], dtype=np.bool)
non_build_type_mask = np.zeros_like(ALL_UNIT_TYPES, dtype=np.bool)
for tp in ALL_UNIT_TYPES:
  if tp not in BUILDINGS_SET:
    non_build_type_mask[ALL_UNIT_TYPES.index(tp)] = True


def enemy_air_unit_mask_fn(x):
  return np.asarray([u.unit_type in AIR_UNITS_SET and u.alliance == ALLIANCE.ENEMY.value for u in x], dtype=np.bool)
air_type_mask = np.zeros_like(ALL_UNIT_TYPES, dtype=np.bool)
for tp in AIR_UNITS_SET:
    air_type_mask[ALL_UNIT_TYPES.index(tp)] = True


def enemy_build_unit_mask_fn(x):
  return np.asarray([u.unit_type in BUILDINGS_SET and u.alliance == ALLIANCE.ENEMY.value for u in x], dtype=np.bool)


def neutral_vespene_unit_mask_fn(x):
  return np.asarray([u.unit_type in NEUTRAL_VESPENE_SET for u in x], dtype=np.bool)
vespene_type_mask = np.zeros_like(ALL_UNIT_TYPES, dtype=np.bool)
for tp in NEUTRAL_VESPENE_SET:
    vespene_type_mask[ALL_UNIT_TYPES.index(tp)] = True


def research_flyer_unit_mask_fn(x):
  return np.asarray([u.unit_type in [
    UNIT_TYPEID.ZERG_SPIRE.value,
    UNIT_TYPEID.ZERG_GREATERSPIRE.value] and u.build_progress == 1.0 for u in x], dtype=np.bool)
research_flyer_type_mask = np.zeros_like(ALL_UNIT_TYPES, dtype=np.bool)
for tp in [UNIT_TYPEID.ZERG_SPIRE.value, UNIT_TYPEID.ZERG_GREATERSPIRE.value]:
  research_flyer_type_mask[ALL_UNIT_TYPES.index(tp)] = True


# functional
def abduct_unit_mask_fn(x):
  return np.asarray([u.unit_type not in BUILDINGS_SET
                     and u.alliance != ALLIANCE.NEUTRAL.value for u in x], dtype=np.bool)


def can_load_unit_mask_fn(x):
  return np.asarray([u.unit_type in [
    UNIT_TYPEID.ZERG_OVERLORDTRANSPORT.value,
    UNIT_TYPEID.ZERG_NYDUSNETWORK.value,
    UNIT_TYPEID.ZERG_NYDUSCANAL.value] and u.alliance == ALLIANCE.SELF.value for u in x], dtype=np.bool)
can_load_type_mask = np.zeros_like(ALL_UNIT_TYPES, dtype=np.bool)
for tp in [UNIT_TYPEID.ZERG_OVERLORDTRANSPORT.value,
           UNIT_TYPEID.ZERG_NYDUSNETWORK.value,
           UNIT_TYPEID.ZERG_NYDUSCANAL.value]:
  can_load_type_mask[ALL_UNIT_TYPES.index(tp)] = True


def attackable_unit_mask_fn(x):
  return np.asarray([u.alliance == ALLIANCE.ENEMY.value or
                     u.unit_type in NEUTRAL_ATTACKABLE_SET or
                     (u.alliance == ALLIANCE.SELF.value and u.unit_type in ATTACK_SELF_BUILDINGS_SET)
                     for u in x], dtype=np.bool)


def gatherable_unit_mask_fn(x):
  return np.asarray([u.unit_type in NEUTRAL_MINERAL_SET.union(VESPENE_CAP_SET) for u in x], dtype=np.bool)
gatherable_type_mask = np.zeros_like(ALL_UNIT_TYPES, dtype=np.bool)
for tp in NEUTRAL_MINERAL_SET.union(VESPENE_CAP_SET):
  gatherable_type_mask[ALL_UNIT_TYPES.index(tp)] = True


def find_nearest_buildable_pos(ability_id, x, y, obs, game_info,
                               pos_mask_fn, search_radius=2):
  if ability_id not in ABILITY_RADIUS:
    return x, y
  search_radius = int(search_radius)
  if pos_mask_fn in [creep_pos_mask_fn, nydus_pos_mask_fn,
                     base_pos_mask_fn, tumor_pos_mask_fn]:
    pos_mask = pos_mask_fn(obs, game_info, flip=True)
  elif pos_mask_fn in [creep_pos_mask_fn_new, nydus_pos_mask_fn_new,
                       base_pos_mask_fn_new, tumor_pos_mask_fn_new]:
    images = _get_minimaps(obs)
    pos_mask = np.array(pos_mask_fn(images))
  size_y, size_x = pos_mask.shape
  ability_radius = ABILITY_RADIUS[ability_id]
  if int(ability_radius) == ability_radius:  # unit build on grid
    x, y = np.round(x), np.round(y)
  else:
    x, y = np.floor(x), np.floor(y)
  min_x = int(max((x - search_radius - np.floor(ability_radius)), np.floor(ability_radius)))
  min_y = int(max((y - search_radius - np.floor(ability_radius)), np.floor(ability_radius)))
  max_x = int(min((x + search_radius + np.floor(ability_radius)), size_x - 1 - np.floor(ability_radius)))
  max_y = int(min((y + search_radius + np.floor(ability_radius)), size_y - 1 - np.floor(ability_radius)))
  pool = True
  for i in range(-math.floor(ability_radius), math.ceil(ability_radius)):
    for j in range(-math.floor(ability_radius), math.ceil(ability_radius)):
      pool &= pos_mask[(size_y-1-max_y-j):(size_y-min_y-j), (min_x+i):(max_x+1+i)]
  candidates = list(zip(*np.nonzero(pool)))
  if len(candidates) == 0:
    print(f'Ability {ability_id} Cannot find any legal position near {(x, y)}!')
  else:
    dist = [np.abs(min_x + i - x) + np.abs(max_y - j - y) for j, i in candidates]
    j, i = candidates[np.argmin(dist)]
    x = min_x + i
    y = max_y - j
  if int(ability_radius) == ability_radius:
    return x, y
  else:
    return x + 0.5, y + 0.5
