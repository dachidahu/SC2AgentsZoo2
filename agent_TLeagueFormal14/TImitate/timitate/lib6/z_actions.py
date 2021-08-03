from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import enum

import numpy as np
from gym import spaces
from pysc2.lib.features import PlayerRelative as ALLIANCE
from pysc2.lib.typeenums import UNIT_TYPEID, BUFF_ID
from timitate.utils.commands import noop, select_units_by_pos, cmd_screen_raw, cmd_quick_raw, cmd_unit_raw
from timitate.utils.mask_fn import *


# cmd_screen = cmd_screen_ui
cmd_screen = cmd_screen_raw

# cmd_quick = cmd_quick_ui
cmd_quick = cmd_quick_raw

# cmd_unit = cmd_screen
cmd_unit = cmd_unit_raw

# select_units = select_units_by_tags
select_units = select_units_by_pos


class ABILITY_TYPES(enum.Enum):
  # Categorized by argument type
  NO_OP = 1  # discrete
  CMD_QUICK = 2  #
  CMD_UNIT = 3  # pointer
  CMD_POS = 4  # spatial discrete


select_unit_type_list = [UNIT_TYPEID.ZERG_ZERGLING,
                         UNIT_TYPEID.ZERG_ZERGLINGBURROWED,
                         UNIT_TYPEID.ZERG_ROACH,
                         UNIT_TYPEID.ZERG_ROACHBURROWED,
                         UNIT_TYPEID.ZERG_HYDRALISK,
                         UNIT_TYPEID.ZERG_HYDRALISKBURROWED,
                         UNIT_TYPEID.ZERG_INFESTOR,
                         UNIT_TYPEID.ZERG_INFESTORBURROWED,
                         UNIT_TYPEID.ZERG_SWARMHOSTMP,
                         UNIT_TYPEID.ZERG_SWARMHOSTBURROWEDMP,
                         UNIT_TYPEID.ZERG_BANELING,
                         UNIT_TYPEID.ZERG_BANELINGBURROWED,
                         UNIT_TYPEID.ZERG_QUEEN,
                         UNIT_TYPEID.ZERG_QUEENBURROWED,
                         UNIT_TYPEID.ZERG_RAVAGER,
                         UNIT_TYPEID.ZERG_LURKERMP,
                         UNIT_TYPEID.ZERG_LURKERMPBURROWED,
                         UNIT_TYPEID.ZERG_ULTRALISK,
                         UNIT_TYPEID.ZERG_MUTALISK,
                         UNIT_TYPEID.ZERG_CORRUPTOR,
                         UNIT_TYPEID.ZERG_VIPER,
                         UNIT_TYPEID.ZERG_BROODLORD,
                         UNIT_TYPEID.ZERG_OVERLORD,
                         UNIT_TYPEID.ZERG_OVERSEER,
                         UNIT_TYPEID.ZERG_OVERLORDTRANSPORT]

# (name, type, sub_id, id, ab_mask, select_unit_mask, cmd_unit_mask, cmd_pos_mask, select_type_func_mask, tar_u_type_func_mask, raw_action_func)
ZERG_ABILITIES = [
  #TODO: NO_OP
  ("no_op", ABILITY_TYPES.NO_OP, None, None, true_ab_mask_fn, zero_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, zero_type_mask, zero_type_mask, noop),
  # CMD_UNIT
  # mask type: any units
  ("Smart_unit", ABILITY_TYPES.CMD_UNIT, 1, None, true_ab_mask_fn, ally_unit_mask_fn, one_unit_mask_fn, zero_pos_mask_fn, one_type_mask, one_type_mask, cmd_unit),
  ("Rally_Hatchery_Units_on_unit", ABILITY_TYPES.CMD_UNIT, 211, 3673, base_ab_mask_fn, base_unit_mask_fn, one_unit_mask_fn, zero_pos_mask_fn, base_type_mask, one_type_mask, cmd_unit),
  ("Rally_Morphing_Unit_on_unit", ABILITY_TYPES.CMD_UNIT, 199, 3673, egg_ab_mask_fn, egg_unit_mask_fn, one_unit_mask_fn, zero_pos_mask_fn, egg_type_mask, one_type_mask, cmd_unit),
  # mask type: any non-structure units
  ("Effect_Abduct_screen", ABILITY_TYPES.CMD_UNIT, 2067, None, abduct_ab_mask_fn, viper_unit_mask_fn, abduct_unit_mask_fn, zero_pos_mask_fn, viper_type_mask, building_type_mask, cmd_unit),
  # mask type: self hatchery, lair, hive
  ("Effect_InjectLarva_screen", ABILITY_TYPES.CMD_UNIT, 251, None, injectlarva_rule_ab_mask_fn, queen_unit_mask_fn, inj_larva_base_unit_mask_fn, zero_pos_mask_fn, queen_type_mask, base_type_mask, cmd_unit),
  # ("Effect_InjectLarva_screen", ABILITY_TYPES.CMD_UNIT, 251, None, injectlarva_ab_mask_fn, queen_unit_mask_fn, base_unit_mask_fn, zero_pos_mask_fn, queen_type_mask, base_type_mask, cmd_unit),
  # mask type: self units (except the queen itself)
  ("Effect_Transfusion_screen", ABILITY_TYPES.CMD_UNIT, 1664, None, transfusion_ab_mask_fn, queen_unit_mask_fn, ally_unit_mask_fn, zero_pos_mask_fn, queen_type_mask, one_type_mask, cmd_unit),
  # mask type: self structures
  ("Effect_ViperConsume_screen", ABILITY_TYPES.CMD_UNIT, 2073, None, viperconsume_ab_mask_fn, viper_unit_mask_fn, viperconsume_unit_mask_fn, zero_pos_mask_fn, viper_type_mask, viperconsume_type_mask, cmd_unit),
  # mask type: self units
  ("Load_screen", ABILITY_TYPES.CMD_UNIT, 3668, None, load_ab_mask_fn, can_load_unit_mask_fn, ally_unit_mask_fn, zero_pos_mask_fn, can_load_type_mask, one_type_mask, cmd_unit),
  ("Load_NydusNetwork_screen", ABILITY_TYPES.CMD_UNIT, 1437, 3668, nydus_network_ab_mask_fn, nydus_network_unit_mask_fn, ally_unit_mask_fn, zero_pos_mask_fn, nydusnetwork_type_mask, one_type_mask, cmd_unit),
  ("Load_NydusWorm_screen", ABILITY_TYPES.CMD_UNIT, 2370, 3668, nydus_worm_ab_mask_fn, nydus_worm_unit_mask_fn, ally_unit_mask_fn, zero_pos_mask_fn, nydusworm_type_mask, one_type_mask, cmd_unit),
  ("Load_Overlord_screen", ABILITY_TYPES.CMD_UNIT, 1406, 3668, overlord_trans_ab_mask_fn, overlord_trans_unit_mask_fn, ally_unit_mask_fn, zero_pos_mask_fn, overlordtrans_type_mask, one_type_mask, cmd_unit),
  # mask type: enemy units
  ("Attack_Attack_unit", ABILITY_TYPES.CMD_UNIT, 23, 3674, true_ab_mask_fn, ally_unit_mask_fn, attackable_unit_mask_fn, zero_pos_mask_fn, one_type_mask, one_type_mask, cmd_unit),
  # mask type: enemy non-structure units
  ("Effect_NeuralParasite_screen", ABILITY_TYPES.CMD_UNIT, 249, None, neuralparasite_ab_mask_fn, infestor_unit_mask_fn, enemy_non_build_unit_mask_fn, zero_pos_mask_fn, infestor_type_mask, non_build_type_mask, cmd_unit),
  # mask type: enemy air units
  ("Effect_ParasiticBomb_screen", ABILITY_TYPES.CMD_UNIT, 2542, None, parasiticbomb_ab_mask_fn, viper_unit_mask_fn, enemy_air_unit_mask_fn, zero_pos_mask_fn, viper_type_mask, air_type_mask, cmd_unit),
  # mask type: enemy structure
  ("Effect_CausticSpray_screen", ABILITY_TYPES.CMD_UNIT, 2324, None, causticspray_ab_mask_fn, corruptor_unit_mask_fn, enemy_build_unit_mask_fn, zero_pos_mask_fn, corruptor_type_mask, building_type_mask, cmd_unit),
  ("Effect_Contaminate_screen", ABILITY_TYPES.CMD_UNIT, 1825, None, contaminate_ab_mask_fn, overseer_unit_mask_fn, enemy_build_unit_mask_fn, zero_pos_mask_fn, overseer_type_mask, building_type_mask, cmd_unit),
  # mask type: neutral vespene
  ("Build_Extractor_screen", ABILITY_TYPES.CMD_UNIT, 1154, None, build_extractor_ab_mask_fn, drone_unit_mask_fn, neutral_vespene_unit_mask_fn, zero_pos_mask_fn, drone_type_mask, vespene_type_mask, cmd_unit),
  # mask type: neutral mineral
  # ("Harvest_Gather_screen", ABILITY_TYPES.CMD_UNIT, 3666, None, harvest_gather_ab_mask_fn, drone_unit_mask_fn, gatherable_unit_mask_fn, zero_pos_mask_fn, cmd_unit),
  ("Harvest_Gather_Drone_screen", ABILITY_TYPES.CMD_UNIT, 1183, 3666, harvest_gather_ab_mask_fn, drone_unit_mask_fn, gatherable_unit_mask_fn, zero_pos_mask_fn, drone_type_mask, gatherable_type_mask, cmd_unit),
  # ("Rally_Workers_on_unit", ABILITY_TYPES.CMD_UNIT, 3690, None, base_ab_mask_fn, base_unit_mask_fn, gatherable_unit_mask_fn, zero_pos_mask_fn, cmd_unit),
  ("Rally_Hatchery_Workers_on_unit", ABILITY_TYPES.CMD_UNIT, 212, 3690, base_ab_mask_fn, base_unit_mask_fn, gatherable_unit_mask_fn, zero_pos_mask_fn, base_type_mask, gatherable_type_mask, cmd_unit),
  # CMD_POS
  # mask type: all
  ("Attack_Attack_screen", ABILITY_TYPES.CMD_POS, 23, 3674, attack_ab_mask_fn, canattack_unit_mask_fn, zero_unit_mask_fn, one_pos_mask_fn, canattack_type_mask, zero_type_mask, cmd_screen),
  ("Scan_Move_screen", ABILITY_TYPES.CMD_POS, 19, 3674, true_ab_mask_fn, ally_unit_mask_fn, zero_unit_mask_fn, one_pos_mask_fn, one_type_mask, zero_type_mask, cmd_screen),
  ("Effect_BlindingCloud_screen", ABILITY_TYPES.CMD_POS, 2063, None, blindingcloud_ab_mask_fn, viper_unit_mask_fn, zero_unit_mask_fn, one_pos_mask_fn, viper_type_mask, zero_type_mask, cmd_screen),
  ("Effect_CorrosiveBile_screen", ABILITY_TYPES.CMD_POS, 2338, None, corrosivebile_ab_mask_fn, ravager_unit_mask_fn, zero_unit_mask_fn, one_pos_mask_fn, ravager_type_mask, zero_type_mask, cmd_screen),
  ("Effect_FungalGrowth_screen", ABILITY_TYPES.CMD_POS, 74, None, fungalgrowth_ab_mask_fn, infestor_unit_mask_fn, zero_unit_mask_fn, one_pos_mask_fn, infestor_type_mask, zero_type_mask, cmd_screen),
  ("Effect_InfestedTerrans_screen", ABILITY_TYPES.CMD_POS, 247, None, infestedterrans_ab_mask_fn, infestor_unit_mask_fn, zero_unit_mask_fn, one_pos_mask_fn, infestor_type_mask, zero_type_mask, cmd_screen),
  ("Effect_LocustSwoop_screen", ABILITY_TYPES.CMD_POS, 2387, None, locustswoop_ab_mask_fn, locust_unit_mask_fn, zero_unit_mask_fn, one_pos_mask_fn, locust_type_mask, zero_type_mask, cmd_screen),
  ("Effect_SpawnLocusts_screen", ABILITY_TYPES.CMD_POS, 2704, None, spawnlocusts_ab_mask_fn, swarmhost_unit_mask_fn, zero_unit_mask_fn, one_pos_mask_fn, swarmhost_type_mask, zero_type_mask, cmd_screen),
  ("Move_screen", ABILITY_TYPES.CMD_POS, 16, None, true_ab_mask_fn, ally_unit_mask_fn, zero_unit_mask_fn, one_pos_mask_fn, one_type_mask, zero_type_mask, cmd_screen),
  ("Patrol_screen", ABILITY_TYPES.CMD_POS, 17, None, true_ab_mask_fn, ally_unit_mask_fn, zero_unit_mask_fn, one_pos_mask_fn, one_type_mask, zero_type_mask, cmd_screen),
  # ("Rally_Building_screen", ABILITY_TYPES.CMD_POS, 195, 3673, rally_building_ab_mask_fn, building_unit_mask_fn, zero_unit_mask_fn, one_pos_mask_fn, cmd_screen),
  ("Rally_Hatchery_Units_screen", ABILITY_TYPES.CMD_POS, 211, 3673, base_ab_mask_fn, base_unit_mask_fn, zero_unit_mask_fn, one_pos_mask_fn, base_type_mask, zero_type_mask, cmd_screen),
  ("Rally_Morphing_Unit_screen", ABILITY_TYPES.CMD_POS, 199, 3673, egg_ab_mask_fn, egg_unit_mask_fn, zero_unit_mask_fn, one_pos_mask_fn, egg_type_mask, zero_type_mask, cmd_screen),
  ("Rally_Hatchery_Workers_screen", ABILITY_TYPES.CMD_POS, 212, 3690, base_ab_mask_fn, base_unit_mask_fn, zero_unit_mask_fn, one_pos_mask_fn, base_type_mask, zero_type_mask, cmd_screen),
  ("Smart_screen", ABILITY_TYPES.CMD_POS, 1, None, true_ab_mask_fn, ally_unit_mask_fn, zero_unit_mask_fn, one_pos_mask_fn, one_type_mask, zero_type_mask, cmd_screen),
  ("UnloadAllAt_Overlord_screen", ABILITY_TYPES.CMD_POS, 1408, 3669, overlord_trans_ab_mask_fn, overlord_trans_unit_mask_fn, zero_unit_mask_fn, one_pos_mask_fn, overlordtrans_type_mask, zero_type_mask, cmd_screen),
  # mask type: buildable (placement)
  ("Build_Hatchery_screen", ABILITY_TYPES.CMD_POS, 1152, None, build_hatchery_ab_mask_fn, drone_unit_mask_fn, zero_unit_mask_fn, base_pos_mask_fn_new, drone_type_mask, zero_type_mask, cmd_screen),
  # mask type: tumor
  ("Build_CreepTumor_Queen_screen", ABILITY_TYPES.CMD_POS, 1694, 3691, queen_tumor_ab_mask_fn, queen_unit_mask_fn, zero_unit_mask_fn, tumor_pos_mask_fn_new, queen_type_mask, zero_type_mask, cmd_screen),
  ("Build_CreepTumor_Tumor_screen", ABILITY_TYPES.CMD_POS, 1733, 3691, tumorburrowed_ab_mask_fn, tumorburrowed_unit_mask_fn, zero_unit_mask_fn, tumor_pos_mask_fn_new, tumorburrowed_type_mask, zero_type_mask, cmd_screen),
  # mask type: creep
  ("Build_BanelingNest_screen", ABILITY_TYPES.CMD_POS, 1162, None, build_banelingnest_ab_mask_fn, drone_unit_mask_fn, zero_unit_mask_fn, creep_pos_mask_fn_new, drone_type_mask, zero_type_mask, cmd_screen),
  ("Build_EvolutionChamber_screen", ABILITY_TYPES.CMD_POS, 1156, None, build_evolutionchamber_ab_mask_fn, drone_unit_mask_fn, zero_unit_mask_fn, creep_pos_mask_fn_new, drone_type_mask, zero_type_mask, cmd_screen),
  ("Build_HydraliskDen_screen", ABILITY_TYPES.CMD_POS, 1157, None, build_hydraliskden_ab_mask_fn, drone_unit_mask_fn, zero_unit_mask_fn, creep_pos_mask_fn_new, drone_type_mask, zero_type_mask, cmd_screen),
  ("Build_InfestationPit_screen", ABILITY_TYPES.CMD_POS, 1160, None, build_infestationpit_ab_mask_fn, drone_unit_mask_fn, zero_unit_mask_fn, creep_pos_mask_fn_new, drone_type_mask, zero_type_mask, cmd_screen),
  ("Build_LurkerDen_screen", ABILITY_TYPES.CMD_POS, 1163, None, build_lurkerden_ab_mask_fn, drone_unit_mask_fn, zero_unit_mask_fn, creep_pos_mask_fn_new, drone_type_mask, zero_type_mask, cmd_screen),
  ("Build_NydusNetwork_screen", ABILITY_TYPES.CMD_POS, 1161, None, build_nydusnetwork_ab_mask_fn, drone_unit_mask_fn, zero_unit_mask_fn, creep_pos_mask_fn_new, drone_type_mask, zero_type_mask, cmd_screen),
  ("Build_RoachWarren_screen", ABILITY_TYPES.CMD_POS, 1165, None, build_roachwarren_ab_mask_fn, drone_unit_mask_fn, zero_unit_mask_fn, creep_pos_mask_fn_new, drone_type_mask, zero_type_mask, cmd_screen),
  ("Build_SpawningPool_screen", ABILITY_TYPES.CMD_POS, 1155, None, build_spawningpool_ab_mask_fn, drone_unit_mask_fn, zero_unit_mask_fn, creep_pos_mask_fn_new, drone_type_mask, zero_type_mask, cmd_screen),
  ("Build_SpineCrawler_screen", ABILITY_TYPES.CMD_POS, 1166, None, build_spinecrawler_ab_mask_fn, drone_unit_mask_fn, zero_unit_mask_fn, creep_pos_mask_fn_new, drone_type_mask, zero_type_mask, cmd_screen),
  ("Build_Spire_screen", ABILITY_TYPES.CMD_POS, 1158, None, build_spire_ab_mask_fn, drone_unit_mask_fn, zero_unit_mask_fn, creep_pos_mask_fn_new, drone_type_mask, zero_type_mask, cmd_screen),
  ("Build_SporeCrawler_screen", ABILITY_TYPES.CMD_POS, 1167, None, build_sporecrawler_ab_mask_fn, drone_unit_mask_fn, zero_unit_mask_fn, creep_pos_mask_fn_new, drone_type_mask, zero_type_mask, cmd_screen),
  ("Build_UltraliskCavern_screen", ABILITY_TYPES.CMD_POS, 1159, None, build_ultraliskcavern_ab_mask_fn, drone_unit_mask_fn, zero_unit_mask_fn, creep_pos_mask_fn_new, drone_type_mask, zero_type_mask, cmd_screen),
  ("Morph_SpineCrawlerRoot_screen", ABILITY_TYPES.CMD_POS, 1729, 3680, spinecrawlerroot_ab_mask_fn, up_spine_unit_mask_fn, zero_unit_mask_fn, creep_pos_mask_fn_new, upspine_type_mask, zero_type_mask, cmd_screen),
  ("Morph_SporeCrawlerRoot_screen", ABILITY_TYPES.CMD_POS, 1731, 3680, sporecrawlerroot_ab_mask_fn, up_spore_unit_mask_fn, zero_unit_mask_fn, creep_pos_mask_fn_new, upspore_type_mask, zero_type_mask, cmd_screen),
  # mask type: nydus (visible area)
  ("Build_NydusWorm_screen", ABILITY_TYPES.CMD_POS, 1768, None, build_nydusworm_ab_mask_fn, nydus_network_unit_mask_fn, zero_unit_mask_fn, nydus_pos_mask_fn_new, nydusnetwork_type_mask, zero_type_mask, cmd_screen),
  # CMD_QUICK
  # NOTE: If using unload one unit action, target unit can be the unit in cargo, cargo units are append after raw units in pb2feature
  ("UnloadAll_NydasNetwork_quick", ABILITY_TYPES.CMD_QUICK, 1438, 3664, nydus_network_ab_mask_fn, nydus_network_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, nydusnetwork_type_mask, zero_type_mask, cmd_quick),
  ("UnloadAll_NydusWorm_quick", ABILITY_TYPES.CMD_QUICK, 2371, 3664, nydus_worm_ab_mask_fn, nydus_worm_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, nydusworm_type_mask, zero_type_mask, cmd_quick),
  ("Stop_Stop_quick", ABILITY_TYPES.CMD_QUICK, 4, 3665, true_ab_mask_fn, ally_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, one_type_mask, zero_type_mask, cmd_quick),
  ("LoadAll_quick", ABILITY_TYPES.CMD_QUICK, 3663, None, true_ab_mask_fn, ally_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, one_type_mask, zero_type_mask, cmd_quick),
  ("Harvest_Return_Drone_quick", ABILITY_TYPES.CMD_QUICK, 1184, 3667, harvest_gather_ab_mask_fn, drone_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, drone_type_mask, zero_type_mask, cmd_quick),
  ("Effect_SpawnChangeling_quick", ABILITY_TYPES.CMD_QUICK, 181, None, spawnchangeling_ab_mask_fn, overseer_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, overseer_type_mask, zero_type_mask, cmd_quick),
  ("Effect_Explode_quick", ABILITY_TYPES.CMD_QUICK, 42, None, explode_ab_mask_fn, baneling_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, baneling_type_mask, zero_type_mask, cmd_quick),
  ("Behavior_GenerateCreepOff_quick", ABILITY_TYPES.CMD_QUICK, 1693, None, overlord_ab_mask_fn, overlord_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, overlord_type_mask, zero_type_mask, cmd_quick),
  ("Behavior_GenerateCreepOn_quick", ABILITY_TYPES.CMD_QUICK, 1692, None, overlord_ab_mask_fn, overlord_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, overlord_type_mask, zero_type_mask, cmd_quick),
  ("Behavior_HoldFireOff_quick", ABILITY_TYPES.CMD_QUICK, 3689, None, true_ab_mask_fn, ally_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, one_type_mask, zero_type_mask, cmd_quick),
  ("Behavior_HoldFireOff_Lurker_quick", ABILITY_TYPES.CMD_QUICK, 2552, 3689, lurkerburrowed_ab_mask_fn, lurker_burrowed_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, lurkerburrowed_type_mask, zero_type_mask, cmd_quick),
  ("Behavior_HoldFireOn_quick", ABILITY_TYPES.CMD_QUICK, 3688, None, true_ab_mask_fn, ally_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, one_type_mask, zero_type_mask, cmd_quick),
  ("Behavior_HoldFireOn_Lurker_quick", ABILITY_TYPES.CMD_QUICK, 2550, 3688, lurkerburrowed_ab_mask_fn, lurker_burrowed_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, lurkerburrowed_type_mask, zero_type_mask, cmd_quick),
  ("BurrowDown_quick", ABILITY_TYPES.CMD_QUICK, 3661, None, burrowdown_ab_mask_fn, ground_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, ground_type_mask, zero_type_mask, cmd_quick),
  ("BurrowDown_Lurker_quick", ABILITY_TYPES.CMD_QUICK, 2108, 3661, lurker_ab_mask_fn, lurker_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, lurker_type_mask, zero_type_mask, cmd_quick),
  ("BurrowUp_quick", ABILITY_TYPES.CMD_QUICK, 3662, None, burrowup_ab_mask_fn, ground_unit_burrowed_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, ground_burrowed_type_mask, zero_type_mask, cmd_quick),
  ("BurrowUp_Lurker_quick", ABILITY_TYPES.CMD_QUICK, 2110, 3662, lurkerburrowed_ab_mask_fn, lurker_burrowed_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, lurkerburrowed_type_mask, zero_type_mask, cmd_quick),
  ("Cancel_quick", ABILITY_TYPES.CMD_QUICK, 3659, None, cancel_ab_mask_fn, in_progress_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, can_in_progress_type_mask, zero_type_mask, cmd_quick),
  ("Cancel_Last_quick", ABILITY_TYPES.CMD_QUICK, 3671, None, cancel_last_ab_mask_fn, can_cancel_last_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, can_cancel_last_type_mask, zero_type_mask, cmd_quick),
  ("HoldPosition_quick", ABILITY_TYPES.CMD_QUICK, 18, None, true_ab_mask_fn, ally_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, one_type_mask, zero_type_mask, cmd_quick),
  ("Morph_Baneling_quick", ABILITY_TYPES.CMD_QUICK, 80, None, morph_baneling_ab_mask_fn, zergling_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, zergling_type_mask, zero_type_mask, cmd_quick),
  ("Morph_BroodLord_quick", ABILITY_TYPES.CMD_QUICK, 1372, None, morph_broodlord_ab_mask_fn, corruptor_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, corruptor_type_mask, zero_type_mask, cmd_quick),
  ("Morph_GreaterSpire_quick", ABILITY_TYPES.CMD_QUICK, 1220, None, morph_greaterspire_ab_mask_fn, free_spire_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, spire_type_mask, zero_type_mask, cmd_quick),
  ("Morph_Hive_quick", ABILITY_TYPES.CMD_QUICK, 1218, None, morph_hive_ab_mask_fn, free_lair_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, lair_type_mask, zero_type_mask, cmd_quick),
  ("Morph_Lair_quick", ABILITY_TYPES.CMD_QUICK, 1216, None, morph_lair_ab_mask_fn, free_hatchery_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, hatchery_type_mask, zero_type_mask, cmd_quick),
  ("Morph_Lurker_quick", ABILITY_TYPES.CMD_QUICK, 2332, None, morph_lurker_ab_mask_fn, hydralisk_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, hydralisk_type_mask, zero_type_mask, cmd_quick),
  # ("Morph_LurkerDen_quick", ABILITY_TYPES.CMD_QUICK, 2112, None, morph_lurkerden_ab_mask_fn, drone_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, cmd_quick),
  ("Morph_OverlordTransport_quick", ABILITY_TYPES.CMD_QUICK, 2708, None, morph_overlordtransport_ab_mask_fn, overlord_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, overlord_type_mask, zero_type_mask, cmd_quick),
  ("Morph_Overseer_quick", ABILITY_TYPES.CMD_QUICK, 1448, None, morph_overseer_ab_mask_fn, overlord_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, overlord_type_mask, zero_type_mask, cmd_quick),
  ("Morph_OverseerMode_quick", ABILITY_TYPES.CMD_QUICK, 3745, None, overseeroversight_ab_mask_fn, overseeroversight_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, overseeroversight_type_mask, zero_type_mask, cmd_quick),
  ("Morph_OversightMode_quick", ABILITY_TYPES.CMD_QUICK, 3743, None, overseer_ab_mask_fn, overseer_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, overseer_type_mask, zero_type_mask, cmd_quick),
  ("Morph_Ravager_quick", ABILITY_TYPES.CMD_QUICK, 2330, None, morph_ravager_ab_mask_fn, roach_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, roach_type_mask, zero_type_mask, cmd_quick),
  ("Morph_SpineCrawlerUproot_quick", ABILITY_TYPES.CMD_QUICK, 1725, 3681, spinecrawleruproot_ab_mask_fn, spine_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, spine_type_mask, zero_type_mask, cmd_quick),
  ("Morph_SporeCrawlerUproot_quick", ABILITY_TYPES.CMD_QUICK, 1727, 3681, sporecrawleruproot_ab_mask_fn, spore_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, spore_type_mask, zero_type_mask, cmd_quick),
  ("Research_Burrow_quick", ABILITY_TYPES.CMD_QUICK, 1225, None, research_burrow_ab_mask_fn, no_morphing_base_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, base_type_mask, zero_type_mask, cmd_quick),
  ("Research_CentrifugalHooks_quick", ABILITY_TYPES.CMD_QUICK, 1482, None, research_centrifugalhooks_ab_mask_fn, banelingnest_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, banelingnest_type_mask, zero_type_mask, cmd_quick),
  ("Research_ChitinousPlating_quick", ABILITY_TYPES.CMD_QUICK, 265, None, research_chitinousplating_ab_mask_fn, ultraliskcavern_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, ultraliskcavern_type_mask, zero_type_mask, cmd_quick),
  ("Research_GlialRegeneration_quick", ABILITY_TYPES.CMD_QUICK, 216, None, research_glialregeneration_ab_mask_fn, roachwarren_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, roachwarren_type_mask, zero_type_mask, cmd_quick),
  ("Research_MuscularAugments_quick", ABILITY_TYPES.CMD_QUICK, 1283, None, research_muscularaugments_ab_mask_fn, hydraliskden_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, hydraliskden_type_mask, zero_type_mask, cmd_quick),
  ("Research_NeuralParasite_quick", ABILITY_TYPES.CMD_QUICK, 1455, None, research_neuralparasite_ab_mask_fn, infestorpit_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, infestorpit_type_mask, zero_type_mask, cmd_quick),
  ("Research_TunnelingClaws_quick", ABILITY_TYPES.CMD_QUICK, 217, None, research_tunnelingclaws_ab_mask_fn, roachwarren_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, roachwarren_type_mask, zero_type_mask, cmd_quick),
  ("Research_GroovedSpines_quick", ABILITY_TYPES.CMD_QUICK, 1282, None, research_groovedspines_ab_mask_fn, hydraliskden_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, hydraliskden_type_mask, zero_type_mask, cmd_quick),
  ("Research_AdaptiveTalons_quick", ABILITY_TYPES.CMD_QUICK, 3709, None, research_adaptivetalons_ab_mask_fn, lurkerden_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, lurkerden_type_mask, zero_type_mask, cmd_quick),
  ("Research_PathogenGlands_quick", ABILITY_TYPES.CMD_QUICK, 1454, None, research_pathogenglands_ab_mask_fn, infestorpit_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, infestorpit_type_mask, zero_type_mask, cmd_quick),
  ("Research_PneumatizedCarapace_quick", ABILITY_TYPES.CMD_QUICK, 1223, None, research_pneumatizedcarapace_ab_mask_fn, no_morphing_base_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, base_type_mask, zero_type_mask, cmd_quick),
  ("Research_EvolveAnabolicSynthesis2_quick", ABILITY_TYPES.CMD_QUICK, 263, None, research_evolveanabolicsynthesis2_ab_mask_fn, ultraliskcavern_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, ultraliskcavern_type_mask, zero_type_mask, cmd_quick),
  ("Research_ZergFlyerArmor_quick", ABILITY_TYPES.CMD_QUICK, 3702, None, research_zergflyerarmor_ab_mask_fn, research_flyer_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, research_flyer_type_mask, zero_type_mask, cmd_quick),
  ("Research_ZergFlyerAttack_quick", ABILITY_TYPES.CMD_QUICK, 3703, None, research_zergflyerattack_ab_mask_fn, research_flyer_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, research_flyer_type_mask, zero_type_mask, cmd_quick),
  ("Research_ZergGroundArmor_quick", ABILITY_TYPES.CMD_QUICK, 3704, None, research_zerggroundarmor_ab_mask_fn, evolutionchamber_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, evolutionchamber_type_mask, zero_type_mask, cmd_quick),
  ("Research_ZergMeleeWeapons_quick", ABILITY_TYPES.CMD_QUICK, 3705, None, research_zergmeleeweapons_ab_mask_fn, evolutionchamber_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, evolutionchamber_type_mask, zero_type_mask, cmd_quick),
  ("Research_ZergMissileWeapons_quick", ABILITY_TYPES.CMD_QUICK, 3706, None, research_zergmissileweapons_ab_mask_fn, evolutionchamber_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, evolutionchamber_type_mask, zero_type_mask, cmd_quick),
  ("Research_ZerglingAdrenalGlands_quick", ABILITY_TYPES.CMD_QUICK, 1252, None, research_zerglingadrenalglands_ab_mask_fn, spawningpool_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, spawningpool_type_mask, zero_type_mask, cmd_quick),
  ("Research_ZerglingMetabolicBoost_quick", ABILITY_TYPES.CMD_QUICK, 1253, None, research_zerglingmetabolicboost_ab_mask_fn, spawningpool_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, spawningpool_type_mask, zero_type_mask, cmd_quick),
  ("Train_Corruptor_quick", ABILITY_TYPES.CMD_QUICK, 1353, None, train_corruptor_ab_mask_fn, larva_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, larva_type_mask, zero_type_mask, cmd_quick),
  ("Train_Drone_quick", ABILITY_TYPES.CMD_QUICK, 1342, None, train_drone_ab_mask_fn, larva_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, larva_type_mask, zero_type_mask, cmd_quick),
  ("Train_Hydralisk_quick", ABILITY_TYPES.CMD_QUICK, 1345, None, train_hydralisk_ab_mask_fn, larva_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, larva_type_mask, zero_type_mask, cmd_quick),
  ("Train_Infestor_quick", ABILITY_TYPES.CMD_QUICK, 1352, None, train_infestor_ab_mask_fn, larva_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, larva_type_mask, zero_type_mask, cmd_quick),
  ("Train_Mutalisk_quick", ABILITY_TYPES.CMD_QUICK, 1346, None, train_mutalisk_ab_mask_fn, larva_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, larva_type_mask, zero_type_mask, cmd_quick),
  ("Train_Overlord_quick", ABILITY_TYPES.CMD_QUICK, 1344, None, train_overlord_ab_mask_fn, larva_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, larva_type_mask, zero_type_mask, cmd_quick),
  ("Train_Queen_quick", ABILITY_TYPES.CMD_QUICK, 1632, None, train_queen_ab_mask_fn, no_morphing_base_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, base_type_mask, zero_type_mask, cmd_quick),
  ("Train_Roach_quick", ABILITY_TYPES.CMD_QUICK, 1351, None, train_roach_ab_mask_fn, larva_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, larva_type_mask, zero_type_mask, cmd_quick),
  ("Train_SwarmHost_quick", ABILITY_TYPES.CMD_QUICK, 1356, None, train_swarmhost_ab_mask_fn, larva_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, larva_type_mask, zero_type_mask, cmd_quick),
  ("Train_Ultralisk_quick", ABILITY_TYPES.CMD_QUICK, 1348, None, train_ultralisk_ab_mask_fn, larva_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, larva_type_mask, zero_type_mask, cmd_quick),
  ("Train_Viper_quick", ABILITY_TYPES.CMD_QUICK, 1354, None, train_viper_ab_mask_fn, larva_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, larva_type_mask, zero_type_mask, cmd_quick),
  ("Train_Zergling_quick", ABILITY_TYPES.CMD_QUICK, 1343, None, train_zergling_ab_mask_fn, larva_unit_mask_fn, zero_unit_mask_fn, zero_pos_mask_fn, larva_type_mask, zero_type_mask, cmd_quick),
]

z_quick_ab_map = dict([(a[2], i) for i, a in enumerate(ZERG_ABILITIES)
                       if a[1] == ABILITY_TYPES.CMD_QUICK])
z_unit_ab_map = dict([(a[2], i) for i, a in enumerate(ZERG_ABILITIES)
                      if a[1] == ABILITY_TYPES.CMD_UNIT])
z_pos_ab_map = dict([(a[2], i) for i, a in enumerate(ZERG_ABILITIES)
                     if a[1] == ABILITY_TYPES.CMD_POS])
z_ab_map = {}
for d in [z_unit_ab_map, z_pos_ab_map, z_quick_ab_map]:
  for i, j in d.items():
    z_ab_map.setdefault(i,[]).append(j)

z_name_map = dict([(a[0], i) for i, a in enumerate(ZERG_ABILITIES)])

# unique ability_ids
z_ability_ids = list(np.unique([a[2] for a in ZERG_ABILITIES if a[2] is not None]))

# unique ability_id to ability_id index
z_ability2index = dict([(b, i) for i, b in enumerate(z_ability_ids)])

# unique buff_id to buff index
z_buff2index = dict([(b.value, i) for i, b in enumerate(BUFF_ID)])

# action index to ability_id index, None to len(z_ability_ids) + 1
z_action2ability = dict([(i, len(z_ability_ids) + 1) if a[2] is None else (i, z_ability2index[a[2]])
                         for i, a in enumerate(ZERG_ABILITIES)])

z_sub2gen_map = {
    2048: 23, # note: 23 is not general id
    3674: 23,
    1374: 3661,
    1378: 3661,
    1382: 3661,
    1444: 3661,
    1394: 3661,
    1433: 3661,
    2340: 3661,
    1386: 3661,
    2014: 3661,
    1512: 3661,
    1390: 3661,
    1376: 3662,
    1380: 3662,
    1384: 3662,
    1446: 3662,
    1396: 3662,
    1435: 3662,
    2342: 3662,
    1388: 3662,
    2016: 3662,
    1514: 3662,
    1392: 3662,
    314: 3659,
    1763: 3659,
    1373: 3659,
    1221: 3659,
    1219: 3659,
    1217: 3659,
    2333: 3659,
    2113: 3659,
    2709: 3659,
    1449: 3659,
    2331: 3659,
    1730: 3659,
    1732: 3659,
    304: 3671,
    306: 3671,
    312: 3671,
    308: 3671,
    1831: 3671,
    1833: 3671,
    1315: 3702,
    1316: 3702,
    1317: 3702,
    1312: 3703,
    1313: 3703,
    1314: 3703,
    1189: 3704,
    1190: 3704,
    1191: 3704,
    1186: 3705,
    1187: 3705,
    1188: 3705,
    1192: 3706,
    1193: 3706,
    1194: 3706,
}


class ActionSpec(object):
  """ action space:
    # ab:              Discrete(196)
    # noop_num:        Discrete(10)
    # shift:           Discrete(2)
    # select:          MultiDiscrete(MAX_UNITS_NUM)
    # cmd_unit:        Discrete(MAX_UNITS_NUM)
    # cmd_pos:         Discrete(200 * 176)
  """
  def __init__(self, max_unit_num=600, max_noop_num=10, map_resolution=(128, 128)):
    self._max_unit_num = max_unit_num
    self._max_noop_num = max_noop_num
    self._resolution_c, self._resolution_r = map_resolution
    self._tensor_names = ['A_AB',
                          'A_NOOP_NUM',
                          'A_SHIFT',
                          'A_SELECT',
                          'A_CMD_UNIT',
                          'A_CMD_POS']

  @property
  def space(self):
    sps = [
      spaces.Discrete(len(ZERG_ABILITIES)),
      spaces.Discrete(self._max_noop_num),
      spaces.Discrete(2),
      spaces.MultiDiscrete([self._max_unit_num+1]*64),  # one for terminal token
      spaces.Discrete(self._max_unit_num),
      spaces.Discrete(self._resolution_c * self._resolution_r),
    ]
    for sp in sps:
      sp.dtype = np.int32
    return sps

  @property
  def tensor_names(self):
    return self._tensor_names


if __name__=='__main__':
    for ab in ZERG_ABILITIES:
        assert len(ab) == 11

    from timitate.utils.const import SAMPLING_WEIGHT_LIB6
    def _get_ability_weight(ab_id):
        if ZERG_ABILITIES[ab_id][0] in SAMPLING_WEIGHT_LIB6:
          w = SAMPLING_WEIGHT_LIB6[ZERG_ABILITIES[ab_id][0]]
        else:
          if ZERG_ABILITIES[ab_id][0].startswith('Research'):
            w = 5.0
          elif ZERG_ABILITIES[ab_id][0].startswith('Effect'):
            w = 5.0
          else:
            w = 1.0
        return w

    for i in range(len(ZERG_ABILITIES)):
        print("{}: {}".format(ZERG_ABILITIES[i][0], _get_ability_weight(i)))

    astar_select_func_emebd_mask = np.stack([ab[-3] for ab in ZERG_ABILITIES], axis=0)
    astar_tar_u_func_emebd_mask = np.stack([ab[-2] for ab in ZERG_ABILITIES], axis=0)
    print(astar_select_func_emebd_mask.shape)
    print(astar_select_func_emebd_mask)
    print(astar_tar_u_func_emebd_mask.shape)
    print(astar_tar_u_func_emebd_mask)
