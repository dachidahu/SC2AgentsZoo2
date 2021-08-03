from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from collections import namedtuple, OrderedDict
from pysc2.lib import UNIT_TYPEID, UPGRADE_ID, ABILITY_ID


# for AbyssalReef only
#IDEAL_BASE_POS = [[38.5, 122.5], [40.5, 44.5], [42.5, 93.5], [161.5, 21.5],
#                  [129.5, 26.5], [70.5, 117.5], [70.5, 94.5], [129.5, 49.5],
#                  [157.5, 50.5], [159.5, 99.5], [141.5, 65.5], [71.5, 16.5],
#                  [99.5, 115.5], [100.5, 28.5], [128.5, 127.5], [58.5, 78.5]]
# for KJ map only
OLD_KJ_IDEAL_BASE_POS = [[122.5, 50.5], [58.5, 28.5], [28.5, 27.5], [124.5, 80.5],
                         [29.5, 117.5], [93.5, 139.5], [87.5, 35.5], [123.5, 140.5],
                         [27.5, 87.5], [64.5, 132.5], [55.5, 94.5], [125.5, 109.5],
                         [120.5, 27.5], [31.5, 140.5], [96.5, 73.5], [26.5, 58.5]]

KJ_BORN_POS = [[31.5, 140.5], [120.5, 27.5]]

IDEAL_BASE_POS_DICT = OrderedDict([
    ('Blueshift', [[141.5, 112.5], [34.5, 63.5], [35.5, 91.5], [35.5, 35.5], [140.5, 84.5], [111.5, 127.5], [89.5, 34.5], [76.5, 118.5], [140.5, 34.5], [99.5, 57.5], [140.5, 140.5], [64.5, 48.5], [86.5, 141.5], [35.5, 141.5]]),
    ('Stasis', [[20.5, 86.5], [50.5, 64.5], [148.5, 32.5], [19.5, 62.5], [54.5, 105.5], [148.5, 62.5], [19.5, 32.5], [27.5, 123.5], [147.5, 86.5], [117.5, 64.5], [113.5, 105.5], [140.5, 123.5], [83.5, 30.5]]),
    ('KairosJunction', [[96.5, 73.5], [28.5, 27.5], [55.5, 94.5], [26.5, 58.5], [125.5, 109.5], [58.5, 28.5], [93.5, 139.5], [27.5, 87.5], [123.5, 140.5], [124.5, 80.5], [122.5, 50.5], [120.5, 27.5], [31.5, 140.5], [29.5, 117.5], [64.5, 132.5], [87.5, 35.5]]),
    ('Automaton', [[127.5, 114.5], [35.5, 34.5], [54.5, 151.5], [98.5, 26.5], [150.5, 74.5], [56.5, 65.5], [33.5, 105.5], [29.5, 65.5], [85.5, 153.5], [154.5, 114.5], [148.5, 145.5], [103.5, 113.5], [120.5, 153.5], [63.5, 26.5], [129.5, 28.5], [80.5, 66.5]]),
    ('PortAleksander', [[145.5, 24.5], [147.5, 105.5], [28.5, 42.5], [59.5, 74.5], [25.5, 70.5], [30.5, 123.5], [150.5, 77.5], [85.5, 124.5], [90.5, 23.5], [64.5, 106.5], [50.5, 18.5], [116.5, 73.5], [125.5, 129.5], [146.5, 52.5], [29.5, 95.5], [111.5, 41.5]]),
    ('ParaSite', [[38.5, 116.5], [119.5, 28.5], [56.5, 143.5], [90.5, 47.5], [122.5, 120.5], [142.5, 25.5], [144.5, 86.5], [84.5, 147.5], [137.5, 55.5], [38.5, 27.5], [31.5, 85.5], [53.5, 51.5], [85.5, 124.5], [137.5, 144.5], [91.5, 24.5], [33.5, 146.5]]),
    ('CeruleanFall', [[114.5, 79.5], [53.5, 80.5], [87.5, 26.5], [108.5, 45.5], [25.5, 99.5], [131.5, 27.5], [59.5, 114.5], [138.5, 132.5], [111.5, 134.5], [36.5, 132.5], [29.5, 27.5], [141.5, 91.5], [56.5, 25.5], [53.5, 51.5], [142.5, 60.5], [80.5, 133.5], [26.5, 68.5], [114.5, 108.5]]),
    ('YearZero', [[172.5, 141.5], [38.5, 112.5], [79.5, 61.5], [179.5, 112.5], [177.5, 82.5], [70.5, 119.5], [133.5, 36.5], [48.5, 47.5], [138.5, 61.5], [147.5, 119.5], [40.5, 82.5], [84.5, 36.5], [45.5, 141.5], [169.5, 47.5]]),
    ('TurboCruise84', [[96.5, 123.5], [38.5, 44.5], [152.5, 67.5], [70.5, 83.5], [153.5, 111.5], [39.5, 88.5], [135.5, 90.5], [121.5, 72.5], [56.5, 65.5], [95.5, 32.5], [137.5, 29.5], [61.5, 35.5], [130.5, 120.5], [54.5, 126.5]]),
    ('Thunderbird', [[134.5, 68.5], [80.5, 55.5], [111.5, 100.5], [67.5, 126.5], [38.5, 133.5], [93.5, 25.5], [57.5, 87.5], [154.5, 93.5], [153.5, 22.5], [151.5, 52.5], [98.5, 130.5], [131.5, 136.5], [37.5, 62.5], [40.5, 103.5], [124.5, 29.5], [60.5, 19.5]]),
    ('Acropolis', [[47.5, 28.5], [102.5, 33.5], [32.5, 85.5], [128.5, 143.5], [142.5, 33.5], [117.5, 60.5], [107.5, 129.5], [144.5, 58.5], [29.5, 53.5], [68.5, 42.5], [143.5, 86.5], [33.5, 138.5], [146.5, 118.5], [73.5, 138.5], [58.5, 111.5], [31.5, 113.5]]),
    ('KingsCove', [[31.5, 135.5], [67.5, 29.5], [61.5, 111.5], [142.5, 84.5], [33.5, 75.5], [114.5, 23.5], [108.5, 130.5], [114.5, 48.5], [83.5, 135.5], [29.5, 106.5], [144.5, 24.5], [40.5, 35.5], [92.5, 24.5], [135.5, 124.5], [87.5, 52.5], [88.5, 107.5], [146.5, 53.5], [61.5, 136.5]]),
    ('CyberForest', [[132.5, 77.5], [83.5, 24.5], [35.5, 61.5], [132.5, 102.5], [37.5, 139.5], [131.5, 50.5], [51.5, 24.5], [36.5, 113.5], [104.5, 46.5], [63.5, 117.5], [116.5, 139.5], [84.5, 139.5], [35.5, 86.5], [130.5, 24.5]]),
    ('NewRepugnancy', [[32.5, 50.5], [151.5, 85.5], [84.5, 113.5], [114.5, 79.5], [63.5, 34.5], [153.5, 59.5], [69.5, 56.5], [32.5, 26.5], [125.5, 30.5], [120.5, 101.5], [151.5, 109.5], [30.5, 76.5], [99.5, 22.5], [58.5, 105.5], [31.5, 102.5], [152.5, 33.5]]),
])


KJ_IDEAL_BASE_POS = IDEAL_BASE_POS_DICT['KairosJunction']


MapReflectPoint = OrderedDict([
    ('Blueshift', [88., 88.]),
    ('Stasis', [84., None]),
    ('KairosJunction', [76., 84.]),
    ('Automaton', [92., 90.]),
    ('PortAleksander', [88., 74.]),
    ('ParaSite', [88., 86.]),
    ('CeruleanFall', [84., 80.]),
    ('YearZero', [109., None]),
    ('TurboCruise84', [96., 78.]),
    ('Thunderbird', [96., 78.]),
    ('Acropolis', [88., 86.]),
    ('KingsCove', [88., 80.]),
    ('CyberForest', [84., 82.]),
    ('NewRepugnancy', [92., 68.]),
])


MAP_ORI_SIZE_DICT = {
    'Blueshift': [176.0, 184.0],
    'Stasis': [168.0, 144.0],
    'KairosJunction': [152.0, 168.0],
    'Automaton': [184.0, 192.0],
    'PortAleksander': [176.0, 160.0],
    'ParaSite': [176.0, 184.0],
    'CeruleanFall': [168.0, 160.0],
    'YearZero': [216, 192],
    'TurboCruise84': [192, 176],
    'Thunderbird': [192, 168],
    'Acropolis': [176, 184],
    'KingsCove': [176, 176],
    'CyberForest': [168, 184],
    'NewRepugnancy': [184, 144],
}


MAP_PLAYABLE_AREA_DICT = {
    'Acropolis': [[18, 18], [158, 154]],
    'Automaton': [[18, 16], [166, 164]],
    'Blueshift': [[20, 20], [156, 156]],
    'CeruleanFall': [[10, 12], [158, 148]],
    'CyberForest': [[20, 8], [148, 156]],
    'KairosJunction': [[16, 14], [136, 154]],
    'KingsCove': [[12, 6], [164, 154]],
    'NewRepugnancy': [[16, 8], [168, 128]],
    'ParaSite': [[18, 10], [158, 162]],
    'PortAleksander': [[10, 4], [166, 144]],
    'Stasis': [[8, 8], [160, 136]],
    'Thunderbird': [[26, 8], [166, 148]],
    'TurboCruise84': [[26, 20], [166, 136]],
    'YearZero': [[26, 26], [192, 154]],
}

def relative_pos(p1, p0):
    return [None if p1[0] is None else p1[0]-p0[0],
            None if p1[1] is None else p1[1]-p0[1]]

MAP_PLAYABLE_SIZE_DICT = dict([(map_name, relative_pos(p1, p0))
                               for map_name, (p0, p1) in MAP_PLAYABLE_AREA_DICT.items()])


IDEAL_BASE_POS_CROP_DICT = OrderedDict(
    [(name, [relative_pos(pos, MAP_PLAYABLE_AREA_DICT[name][0])
             for pos in pos_list]) for name, pos_list in IDEAL_BASE_POS_DICT.items()]
)


KJ_IDEAL_BASE_POS_CROP = IDEAL_BASE_POS_CROP_DICT['KairosJunction']

MapReflectPoint_CROP = OrderedDict(
    [(name, relative_pos(pos, MAP_PLAYABLE_AREA_DICT[name][0]))
      for name, pos in MapReflectPoint.items()]
)


AB_ID_OVERSAMPLE_CNT_DICT = {
    1165: 2,  # BUILD_ROACHWARREN  cnt: 9607
    1158: 6,  # BUILD_SPIRE  cnt: 3520
    1159: 42,  # BUILD_ULTRALISKCAVERN  cnt: 527
    1160: 7,  # BUILD_INFESTATIONPIT  cnt: 2731
    1157: 5,  # BUILD_HYDRALISKDEN  cnt: 4373
    2112: 12,  # MORPH_LURKERDEN  cnt: 1967
    1216: 2,  # MORPH_LAIR  cnt: 11591
    1218: 12,  # MORPH_HIVE  cnt: 1950
}


SAMPLING_WEIGHT = {
    'no_op': 0.25,
    'Smart_screen': 0.5,
    'Morph_Lair_quick': 2.0,
    'Morph_Lurker_quick': 3.0,
    'Build_Hatchery_screen': 2.0,
    'Build_SpawningPool_screen': 5.0,
    'Build_RoachWarren_screen': 15.0,
    'Effect_Transfusion_screen': 5.0,
    'Rally_Hatchery_Units_screen': 5.0,
    'BurrowDown_Lurker_quick': 5.0,
    'Build_HydraliskDen_screen': 20.0,
    'Rally_Hatchery_Workers_on_unit': 5.0,
    'Build_Spire_screen': 20.0,
    'UnloadAll_NydusWorm_quick': 5.0,
    'BurrowUp_Lurker_quick': 4.0,
    'Build_InfestationPit_screen': 20.0,
    'select_all_idle_worker': 5.0,
    'Effect_Explode_quick': 5.0,
    'Build_LurkerDen_screen': 20.0,
    'Research_Burrow_quick': 5.0,
    'BurrowDown_quick': 5.0,
    'Morph_Hive_quick': 12.0,
    'BurrowUp_quick': 5.0,
    'Effect_ViperConsume_screen': 5.0,
    'Build_NydusWorm_screen': 20.0,
    'Build_NydusNetwork_screen': 20.0,
    'UnloadAll_NydasNetwork_quick': 5.0,
    'Morph_OverlordTransport_quick': 5.0,
    'Build_UltraliskCavern_screen': 80.0,
    'Morph_GreaterSpire_quick': 40.0,
    'Effect_ParasiticBomb_screen': 10.0,
}


SAMPLING_WEIGHT_LIB6 = {
    'no_op': 0.25,
    "Smart_screen": 0.2,
    "Effect_InjectLarva_screen": 1.0,
    "Effect_Transfusion_screen": 1.0,
    "Effect_CorrosiveBile_screen": 1.0,
    "UnloadAllAt_Overlord_screen": 10.0,
    "Build_BanelingNest_screen": 1.5,
    "Build_HydraliskDen_screen": 4.2,
    "Build_InfestationPit_screen": 7.6,
    "Build_LurkerDen_screen": 9.0,
    "Build_NydusNetwork_screen": 10.0,
    "Build_RoachWarren_screen": 1.5,
    "Build_Spire_screen": 5.2,
    "Build_UltraliskCavern_screen": 10.0,
    "Morph_SpineCrawlerRoot_screen": 1.6,
    "Morph_SporeCrawlerRoot_screen": 3.0,
    "Build_NydusWorm_screen": 6.4,
    "UnloadAll_NydasNetwork_quick": 7.0,
    "UnloadAll_NydusWorm_quick": 1.5,
    "BurrowDown_quick": 2.0,
    "BurrowDown_Lurker_quick": 1.5,
    "BurrowUp_quick": 2.0,
    "BurrowUp_Lurker_quick": 1.5,
    "Morph_BroodLord_quick": 9.9,
    "Morph_GreaterSpire_quick": 10.0,
    "Morph_Hive_quick": 10.0,
    "Morph_Lair_quick": 1.5,
    "Morph_Lurker_quick": 1.5,
    "Morph_OverlordTransport_quick": 5.0,
    "Morph_OverseerMode_quick": 5.0,
    "Morph_OversightMode_quick": 5.0,
    "Morph_SpineCrawlerUproot_quick": 1.6,
    "Morph_SporeCrawlerUproot_quick": 3.0,
    "Research_Burrow_quick": 5.0,
    "Research_ZerglingMetabolicBoost_quick": 1.0,
    "Train_Corruptor_quick": 3.3,
    "Train_Infestor_quick": 5.0,
    "Train_SwarmHost_quick": 5.0,
    "Train_Ultralisk_quick": 10.0,
    "Train_Viper_quick": 5.0,
    "Effect_SpawnChangeling_quick": 2.0,
    "Effect_Explode_quick": 2.0,
    "Effect_ViperConsume_screen": 3.8,
}


BUILDINGS_ON_CREEP = [
    'SPAWNINGPOOL',
    'BANELINGNEST',
    'ROACHWARREN',
    'CREEPTUMOR_QUEEN',
    'CREEPTUMOR_TUMOR',
    'EVOLUTIONCHAMBER',
    'HYDRALISKDEN',
    'INFESTATIONPIT',
    'NYDUSNETWORK',
    'NYDUSWORM',
    'SPIRE',
    'SPINECRAWLER',
    'SPORECRAWLER',
    'ULTRALISKCAVERN',
]

COMBAT_UNITS_FOR_SMART = [
    UNIT_TYPEID.ZERG_INFESTORTERRAN.value,
    UNIT_TYPEID.ZERG_CHANGELING.value,
    UNIT_TYPEID.ZERG_CHANGELINGZEALOT.value,
    UNIT_TYPEID.ZERG_CHANGELINGMARINESHIELD.value,
    UNIT_TYPEID.ZERG_CHANGELINGMARINE.value,
    UNIT_TYPEID.ZERG_CHANGELINGZERGLINGWINGS.value,
    UNIT_TYPEID.ZERG_CHANGELINGZERGLING.value,
    UNIT_TYPEID.ZERG_ZERGLING.value,
    UNIT_TYPEID.ZERG_ZERGLINGBURROWED.value,
    UNIT_TYPEID.ZERG_BANELING.value,
    UNIT_TYPEID.ZERG_BANELINGBURROWED.value,
    UNIT_TYPEID.ZERG_ROACH.value,
    UNIT_TYPEID.ZERG_ROACHBURROWED.value,
    UNIT_TYPEID.ZERG_HYDRALISK.value,
    UNIT_TYPEID.ZERG_HYDRALISKBURROWED.value,
    UNIT_TYPEID.ZERG_INFESTOR.value,
    UNIT_TYPEID.ZERG_INFESTORBURROWED.value,
    UNIT_TYPEID.ZERG_LOCUSTMP.value,
    UNIT_TYPEID.ZERG_LOCUSTMPFLYING.value,
    UNIT_TYPEID.ZERG_ULTRALISK.value,
    # UNIT_TYPEID.ZERG_QUEEN.value,
    # UNIT_TYPEID.ZERG_QUEENBURROWED.value,
    UNIT_TYPEID.ZERG_RAVAGER.value,
    UNIT_TYPEID.ZERG_LURKERMP.value,
    UNIT_TYPEID.ZERG_LURKERMPBURROWED.value,
    UNIT_TYPEID.ZERG_OVERSEER.value,
    UNIT_TYPEID.ZERG_MUTALISK.value,
    UNIT_TYPEID.ZERG_CORRUPTOR.value,
    UNIT_TYPEID.ZERG_BROODLORD.value,
    UNIT_TYPEID.ZERG_VIPER.value,
    UNIT_TYPEID.ZERG_BROODLING.value,
    # UNIT_TYPEID.ZERG_SPINECRAWLERUPROOTED.value,
    # UNIT_TYPEID.ZERG_SPORECRAWLERUPROOTED.value,
    # UNIT_TYPEID.ZERG_SWARMHOSTBURROWEDMP.value,
    # UNIT_TYPEID.ZERG_SWARMHOSTMP.value,
]


COMBAT_UNITS_SET_FOR_SMART = set(COMBAT_UNITS_FOR_SMART)


BUILDINGS = [
    UNIT_TYPEID.ZERG_HATCHERY.value,
    UNIT_TYPEID.ZERG_SPINECRAWLER.value,
    UNIT_TYPEID.ZERG_SPINECRAWLERUPROOTED.value,
    UNIT_TYPEID.ZERG_SPORECRAWLER.value,
    UNIT_TYPEID.ZERG_SPORECRAWLERUPROOTED.value,
    UNIT_TYPEID.ZERG_EXTRACTOR.value,
    UNIT_TYPEID.ZERG_SPAWNINGPOOL.value,
    UNIT_TYPEID.ZERG_EVOLUTIONCHAMBER.value,
    UNIT_TYPEID.ZERG_ROACHWARREN.value,
    UNIT_TYPEID.ZERG_BANELINGNEST.value,
    UNIT_TYPEID.ZERG_CREEPTUMORBURROWED.value,
    UNIT_TYPEID.ZERG_CREEPTUMOR.value,
    UNIT_TYPEID.ZERG_CREEPTUMORQUEEN.value,
    UNIT_TYPEID.ZERG_LAIR.value,
    UNIT_TYPEID.ZERG_HYDRALISKDEN.value,
    UNIT_TYPEID.ZERG_LURKERDENMP.value,
    UNIT_TYPEID.ZERG_SPIRE.value,
    UNIT_TYPEID.ZERG_NYDUSNETWORK.value,
    UNIT_TYPEID.ZERG_NYDUSCANAL.value,
    UNIT_TYPEID.ZERG_INFESTATIONPIT.value,
    UNIT_TYPEID.ZERG_HIVE.value,
    UNIT_TYPEID.ZERG_GREATERSPIRE.value,
    UNIT_TYPEID.ZERG_ULTRALISKCAVERN.value,
]
BUILDINGS_SET = set(BUILDINGS)


ATTACK_SELF_BUILDINGS = [
    UNIT_TYPEID.ZERG_EVOLUTIONCHAMBER.value,
    UNIT_TYPEID.ZERG_ROACHWARREN.value,
    UNIT_TYPEID.ZERG_BANELINGNEST.value,
]
ATTACK_SELF_BUILDINGS_SET = set(ATTACK_SELF_BUILDINGS)


RESEARCH_BUILDINGS = [
    UNIT_TYPEID.ZERG_HATCHERY.value,
    UNIT_TYPEID.ZERG_SPAWNINGPOOL.value,
    UNIT_TYPEID.ZERG_EVOLUTIONCHAMBER.value,
    UNIT_TYPEID.ZERG_ROACHWARREN.value,
    UNIT_TYPEID.ZERG_BANELINGNEST.value,
    UNIT_TYPEID.ZERG_LAIR.value,
    UNIT_TYPEID.ZERG_HYDRALISKDEN.value,
    UNIT_TYPEID.ZERG_LURKERDENMP.value,
    UNIT_TYPEID.ZERG_SPIRE.value,
    UNIT_TYPEID.ZERG_INFESTATIONPIT.value,
    UNIT_TYPEID.ZERG_HIVE.value,
    UNIT_TYPEID.ZERG_GREATERSPIRE.value,
    UNIT_TYPEID.ZERG_ULTRALISKCAVERN.value,
]
RESEARCH_BUILDINGS_SET = set(RESEARCH_BUILDINGS)


EGGS = [
    UNIT_TYPEID.ZERG_BANELINGCOCOON.value,
    UNIT_TYPEID.ZERG_BROODLORDCOCOON.value,
    UNIT_TYPEID.ZERG_OVERLORDCOCOON.value,
    UNIT_TYPEID.ZERG_RAVAGERCOCOON.value,
    UNIT_TYPEID.ZERG_TRANSPORTOVERLORDCOCOON.value,
    UNIT_TYPEID.ZERG_EGG.value,
    UNIT_TYPEID.ZERG_INFESTEDTERRANSEGG.value,
    UNIT_TYPEID.ZERG_LURKERMPEGG.value,
]
EGGS_SET = set(EGGS)


BASES = [
    UNIT_TYPEID.ZERG_HATCHERY.value,
    UNIT_TYPEID.ZERG_LAIR.value,
    UNIT_TYPEID.ZERG_HIVE.value,
]
BASES_SET = set(BASES)


UNITS = [
    UNIT_TYPEID.ZERG_LARVA.value,
    UNIT_TYPEID.ZERG_DRONE.value,
    UNIT_TYPEID.ZERG_DRONEBURROWED.value,
    UNIT_TYPEID.ZERG_QUEEN.value,
    UNIT_TYPEID.ZERG_QUEENBURROWED.value,
    UNIT_TYPEID.ZERG_ZERGLING.value,
    UNIT_TYPEID.ZERG_ZERGLINGBURROWED.value,
    UNIT_TYPEID.ZERG_BANELING.value,
    UNIT_TYPEID.ZERG_BANELINGBURROWED.value,
    UNIT_TYPEID.ZERG_ROACH.value,
    UNIT_TYPEID.ZERG_ROACHBURROWED.value,
    UNIT_TYPEID.ZERG_RAVAGER.value,
    UNIT_TYPEID.ZERG_RAVAGERBURROWED.value,
    UNIT_TYPEID.ZERG_HYDRALISK.value,
    UNIT_TYPEID.ZERG_HYDRALISKBURROWED.value,
    UNIT_TYPEID.ZERG_LURKERMP.value,
    UNIT_TYPEID.ZERG_LURKERMPBURROWED.value,
    UNIT_TYPEID.ZERG_INFESTOR.value,
    UNIT_TYPEID.ZERG_INFESTORBURROWED.value,
    UNIT_TYPEID.ZERG_SWARMHOSTMP.value,
    UNIT_TYPEID.ZERG_SWARMHOSTBURROWEDMP.value,
    UNIT_TYPEID.ZERG_ULTRALISK.value,
    UNIT_TYPEID.ZERG_ULTRALISKBURROWED.value,
    UNIT_TYPEID.ZERG_OVERLORD.value,
    UNIT_TYPEID.ZERG_OVERSEER.value,
    UNIT_TYPEID.ZERG_MUTALISK.value,
    UNIT_TYPEID.ZERG_CORRUPTOR.value,
    UNIT_TYPEID.ZERG_BROODLORD.value,
    UNIT_TYPEID.ZERG_VIPER.value,
    UNIT_TYPEID.ZERG_BANELINGCOCOON.value,
    UNIT_TYPEID.ZERG_BROODLORDCOCOON.value,
    UNIT_TYPEID.ZERG_OVERLORDCOCOON.value,
    UNIT_TYPEID.ZERG_RAVAGERCOCOON.value,
    UNIT_TYPEID.ZERG_LURKERMPEGG.value,
]
UNITS_SET = set(UNITS)


GROUND_UNITS = [
    UNIT_TYPEID.ZERG_DRONE.value,
    UNIT_TYPEID.ZERG_QUEEN.value,
    UNIT_TYPEID.ZERG_ZERGLING.value,
    UNIT_TYPEID.ZERG_BANELING.value,
    UNIT_TYPEID.ZERG_ROACH.value,
    UNIT_TYPEID.ZERG_RAVAGER.value,
    UNIT_TYPEID.ZERG_HYDRALISK.value,
    UNIT_TYPEID.ZERG_LURKERMP.value,
    UNIT_TYPEID.ZERG_INFESTOR.value,
    UNIT_TYPEID.ZERG_SWARMHOSTMP.value,
    UNIT_TYPEID.ZERG_ULTRALISK.value,
]
GROUND_UNITS_SET = set(GROUND_UNITS)


GROUND_UNITS_BURROWED = [
    UNIT_TYPEID.ZERG_DRONEBURROWED.value,
    UNIT_TYPEID.ZERG_QUEENBURROWED.value,
    UNIT_TYPEID.ZERG_ZERGLINGBURROWED.value,
    UNIT_TYPEID.ZERG_BANELINGBURROWED.value,
    UNIT_TYPEID.ZERG_ROACHBURROWED.value,
    UNIT_TYPEID.ZERG_RAVAGERBURROWED.value,
    UNIT_TYPEID.ZERG_HYDRALISKBURROWED.value,
    UNIT_TYPEID.ZERG_LURKERMPBURROWED.value,
    UNIT_TYPEID.ZERG_INFESTORBURROWED.value,
    UNIT_TYPEID.ZERG_SWARMHOSTBURROWEDMP.value,
    UNIT_TYPEID.ZERG_ULTRALISKBURROWED.value,
]
GROUND_UNITS_BURROWED_SET = set(GROUND_UNITS_BURROWED)


AIR_UNITS = [
    UNIT_TYPEID.ZERG_OVERLORD.value,
    UNIT_TYPEID.ZERG_OVERLORDCOCOON.value,
    UNIT_TYPEID.ZERG_OVERLORDTRANSPORT.value,
    UNIT_TYPEID.ZERG_TRANSPORTOVERLORDCOCOON.value,
    UNIT_TYPEID.ZERG_OVERSEER.value,
    UNIT_TYPEID.ZERG_MUTALISK.value,
    UNIT_TYPEID.ZERG_CORRUPTOR.value,
    UNIT_TYPEID.ZERG_VIPER.value,
    UNIT_TYPEID.ZERG_BROODLORD.value,
    UNIT_TYPEID.ZERG_BROODLORDCOCOON.value,
]
AIR_UNITS_SET = set(AIR_UNITS)


NEUTRAL_VESPENE = [
    UNIT_TYPEID.NEUTRAL_VESPENEGEYSER.value,
    UNIT_TYPEID.NEUTRAL_PURIFIERVESPENEGEYSER.value,
    UNIT_TYPEID.NEUTRAL_RICHVESPENEGEYSER.value,
    UNIT_TYPEID.NEUTRAL_PROTOSSVESPENEGEYSER.value,
    UNIT_TYPEID.NEUTRAL_SHAKURASVESPENEGEYSER.value,
    UNIT_TYPEID.NEUTRAL_SPACEPLATFORMGEYSER.value,
]
NEUTRAL_VESPENE_SET = set(NEUTRAL_VESPENE)


NEUTRAL_MINERAL = [
    UNIT_TYPEID.NEUTRAL_MINERALFIELD.value,
    UNIT_TYPEID.NEUTRAL_MINERALFIELD750.value,
    UNIT_TYPEID.NEUTRAL_BATTLESTATIONMINERALFIELD.value,
    UNIT_TYPEID.NEUTRAL_BATTLESTATIONMINERALFIELD750.value,
    UNIT_TYPEID.NEUTRAL_LABMINERALFIELD.value,
    UNIT_TYPEID.NEUTRAL_LABMINERALFIELD750.value,
    UNIT_TYPEID.NEUTRAL_PURIFIERMINERALFIELD.value,
    UNIT_TYPEID.NEUTRAL_PURIFIERMINERALFIELD750.value,
    UNIT_TYPEID.NEUTRAL_PURIFIERRICHMINERALFIELD.value,
    UNIT_TYPEID.NEUTRAL_PURIFIERRICHMINERALFIELD750.value,
    UNIT_TYPEID.NEUTRAL_RICHMINERALFIELD.value,
    UNIT_TYPEID.NEUTRAL_RICHMINERALFIELD750.value,
]
NEUTRAL_MINERAL_SET = set(NEUTRAL_MINERAL)


VESPENE_CAP = [
    UNIT_TYPEID.ZERG_EXTRACTOR.value,
]
VESPENE_CAP_SET = set(VESPENE_CAP)


BUILDINGS_MULTIPLIER = {
    UNIT_TYPEID.ZERG_HATCHERY.value:1,
    UNIT_TYPEID.ZERG_EXTRACTOR.value:0.5,
    UNIT_TYPEID.ZERG_SPAWNINGPOOL.value:1,
    UNIT_TYPEID.ZERG_EVOLUTIONCHAMBER.value:0.5,
    UNIT_TYPEID.ZERG_SPINECRAWLER.value:0.1,
    UNIT_TYPEID.ZERG_SPINECRAWLERUPROOTED.value:0.1,
    UNIT_TYPEID.ZERG_SPORECRAWLER.value:0.1,
    UNIT_TYPEID.ZERG_SPORECRAWLERUPROOTED.value:0.1,
    UNIT_TYPEID.ZERG_ROACHWARREN.value:1,
    UNIT_TYPEID.ZERG_BANELINGNEST.value:1,
    UNIT_TYPEID.ZERG_LAIR.value:1,
    UNIT_TYPEID.ZERG_HYDRALISKDEN.value:1,
    UNIT_TYPEID.ZERG_LURKERDENMP.value:1,
    UNIT_TYPEID.ZERG_INFESTATIONPIT.value:1,
    UNIT_TYPEID.ZERG_SPIRE.value:1,
    UNIT_TYPEID.ZERG_NYDUSNETWORK.value:1,
    UNIT_TYPEID.ZERG_NYDUSCANAL.value:1,
    UNIT_TYPEID.ZERG_HIVE.value:1,
    UNIT_TYPEID.ZERG_ULTRALISKCAVERN.value:1,
    UNIT_TYPEID.ZERG_GREATERSPIRE.value:1,
    UNIT_TYPEID.ZERG_CREEPTUMOR.value:0.1,
}


UNITS_MULTIPLIER = {
    UNIT_TYPEID.ZERG_LARVA.value:1,
    UNIT_TYPEID.ZERG_DRONE.value:1,
    UNIT_TYPEID.ZERG_DRONEBURROWED.value:1,
    UNIT_TYPEID.ZERG_QUEEN.value:2,
    UNIT_TYPEID.ZERG_QUEENBURROWED.value:2,
    UNIT_TYPEID.ZERG_ZERGLING.value:0.5,
    UNIT_TYPEID.ZERG_ZERGLINGBURROWED.value:0.5,
    UNIT_TYPEID.ZERG_BANELING.value:0.5,
    UNIT_TYPEID.ZERG_BANELINGBURROWED.value:0.5,
    UNIT_TYPEID.ZERG_ROACH.value:2,
    UNIT_TYPEID.ZERG_ROACHBURROWED.value:2,
    UNIT_TYPEID.ZERG_RAVAGER.value:3,
    UNIT_TYPEID.ZERG_HYDRALISK.value:2,
    UNIT_TYPEID.ZERG_HYDRALISKBURROWED.value:2,
    UNIT_TYPEID.ZERG_LURKERMP.value:4,
    UNIT_TYPEID.ZERG_LURKERMPBURROWED.value:4,
    UNIT_TYPEID.ZERG_INFESTOR.value:2,
    UNIT_TYPEID.ZERG_INFESTORBURROWED.value:2,
    UNIT_TYPEID.ZERG_SWARMHOSTMP.value:3,
    UNIT_TYPEID.ZERG_ULTRALISK.value:6,
    UNIT_TYPEID.ZERG_OVERLORD.value:0.04,
    UNIT_TYPEID.ZERG_OVERSEER.value:1,
    UNIT_TYPEID.ZERG_MUTALISK.value:2,
    UNIT_TYPEID.ZERG_CORRUPTOR.value:2,
    UNIT_TYPEID.ZERG_BROODLORD.value:4,
    UNIT_TYPEID.ZERG_VIPER.value:3,
    UNIT_TYPEID.ZERG_BANELINGCOCOON.value:0.5,
    UNIT_TYPEID.ZERG_BROODLORDCOCOON.value:4,
    UNIT_TYPEID.ZERG_OVERLORDCOCOON.value:1,
    UNIT_TYPEID.ZERG_RAVAGERCOCOON.value:3,
    UNIT_TYPEID.ZERG_LURKERMPEGG.value:4,
}


AttackAttr = namedtuple('AttackAttr', ('can_attack_ground', 'can_attack_air'))


ATTACK_FORCE = {
    UNIT_TYPEID.ZERG_LARVA.value: AttackAttr(False, False),
    UNIT_TYPEID.ZERG_DRONE.value: AttackAttr(True, False),
    UNIT_TYPEID.ZERG_ZERGLING.value: AttackAttr(True, False),
    UNIT_TYPEID.ZERG_BANELING.value: AttackAttr(True, False),
    UNIT_TYPEID.ZERG_ROACH.value: AttackAttr(True, False),
    UNIT_TYPEID.ZERG_ROACHBURROWED.value: AttackAttr(True, False),
    UNIT_TYPEID.ZERG_RAVAGER.value: AttackAttr(True, False),
    UNIT_TYPEID.ZERG_HYDRALISK.value: AttackAttr(True, True),
    UNIT_TYPEID.ZERG_LURKERMP.value: AttackAttr(True, False),
    UNIT_TYPEID.ZERG_LURKERMPBURROWED.value: AttackAttr(True, False),
    UNIT_TYPEID.ZERG_VIPER.value: AttackAttr(False, False),
    UNIT_TYPEID.ZERG_MUTALISK.value: AttackAttr(True, True),
    UNIT_TYPEID.ZERG_CORRUPTOR.value: AttackAttr(False, True),
    UNIT_TYPEID.ZERG_BROODLORD.value: AttackAttr(True, False),
    UNIT_TYPEID.ZERG_SWARMHOSTMP.value: AttackAttr(False, False),
    UNIT_TYPEID.ZERG_LOCUSTMP.value: AttackAttr(True, False),
    UNIT_TYPEID.ZERG_INFESTOR.value: AttackAttr(False, False),
    UNIT_TYPEID.ZERG_ULTRALISK.value: AttackAttr(True, False),
    UNIT_TYPEID.ZERG_BROODLING.value: AttackAttr(True, False),
    UNIT_TYPEID.ZERG_OVERLORD.value: AttackAttr(False, False),
    UNIT_TYPEID.ZERG_OVERSEER.value: AttackAttr(False, False),
    UNIT_TYPEID.ZERG_QUEEN.value: AttackAttr(True, True),
    UNIT_TYPEID.ZERG_CHANGELING.value: AttackAttr(False, False),
    UNIT_TYPEID.ZERG_SPINECRAWLER.value: AttackAttr(True, False),
    UNIT_TYPEID.ZERG_SPORECRAWLER.value: AttackAttr(False, True),
    UNIT_TYPEID.ZERG_NYDUSCANAL.value: AttackAttr(False, False)
}


ALL_NEUTRAL = [
    UNIT_TYPEID.NEUTRAL_BATTLESTATIONMINERALFIELD.value,
    UNIT_TYPEID.NEUTRAL_BATTLESTATIONMINERALFIELD750.value,
    UNIT_TYPEID.NEUTRAL_COLLAPSIBLEROCKTOWERDEBRIS.value,
    UNIT_TYPEID.NEUTRAL_COLLAPSIBLEROCKTOWERDIAGONAL.value,
    UNIT_TYPEID.NEUTRAL_COLLAPSIBLEROCKTOWERPUSHUNIT.value,
    UNIT_TYPEID.NEUTRAL_COLLAPSIBLETERRANTOWERDEBRIS.value,
    UNIT_TYPEID.NEUTRAL_COLLAPSIBLETERRANTOWERDIAGONAL.value,
    UNIT_TYPEID.NEUTRAL_COLLAPSIBLETERRANTOWERPUSHUNIT.value,
    UNIT_TYPEID.NEUTRAL_COLLAPSIBLETERRANTOWERPUSHUNITRAMPLEFT.value,
    UNIT_TYPEID.NEUTRAL_COLLAPSIBLETERRANTOWERPUSHUNITRAMPRIGHT.value,
    UNIT_TYPEID.NEUTRAL_COLLAPSIBLETERRANTOWERRAMPLEFT.value,
    UNIT_TYPEID.NEUTRAL_COLLAPSIBLETERRANTOWERRAMPRIGHT.value,
    UNIT_TYPEID.NEUTRAL_DEBRISRAMPLEFT.value,
    UNIT_TYPEID.NEUTRAL_DEBRISRAMPRIGHT.value,
    UNIT_TYPEID.NEUTRAL_DESTRUCTIBLEDEBRIS6X6.value,
    UNIT_TYPEID.NEUTRAL_DESTRUCTIBLEDEBRISRAMPDIAGONALHUGEBLUR.value,
    UNIT_TYPEID.NEUTRAL_DESTRUCTIBLEDEBRISRAMPDIAGONALHUGEULBR.value,
    UNIT_TYPEID.NEUTRAL_DESTRUCTIBLEROCK6X6.value,
    UNIT_TYPEID.NEUTRAL_DESTRUCTIBLEROCKEX1DIAGONALHUGEBLUR.value,
    UNIT_TYPEID.NEUTRAL_FORCEFIELD.value,
    UNIT_TYPEID.NEUTRAL_KARAKFEMALE.value,
    UNIT_TYPEID.NEUTRAL_LABMINERALFIELD.value,
    UNIT_TYPEID.NEUTRAL_LABMINERALFIELD750.value,
    UNIT_TYPEID.NEUTRAL_MINERALFIELD.value,
    UNIT_TYPEID.NEUTRAL_MINERALFIELD750.value,
    UNIT_TYPEID.NEUTRAL_PROTOSSVESPENEGEYSER.value,
    UNIT_TYPEID.NEUTRAL_PURIFIERMINERALFIELD.value,
    UNIT_TYPEID.NEUTRAL_PURIFIERMINERALFIELD750.value,
    UNIT_TYPEID.NEUTRAL_PURIFIERRICHMINERALFIELD.value,
    UNIT_TYPEID.NEUTRAL_PURIFIERRICHMINERALFIELD750.value,
    UNIT_TYPEID.NEUTRAL_PURIFIERVESPENEGEYSER.value,
    UNIT_TYPEID.NEUTRAL_RICHMINERALFIELD.value,
    UNIT_TYPEID.NEUTRAL_RICHMINERALFIELD750.value,
    UNIT_TYPEID.NEUTRAL_RICHVESPENEGEYSER.value,
    UNIT_TYPEID.NEUTRAL_SCANTIPEDE.value,
    UNIT_TYPEID.NEUTRAL_SHAKURASVESPENEGEYSER.value,
    UNIT_TYPEID.NEUTRAL_SPACEPLATFORMGEYSER.value,
    UNIT_TYPEID.NEUTRAL_UNBUILDABLEBRICKSDESTRUCTIBLE.value,
    UNIT_TYPEID.NEUTRAL_UNBUILDABLEPLATESDESTRUCTIBLE.value,
    UNIT_TYPEID.NEUTRAL_UTILITYBOT.value,
    UNIT_TYPEID.NEUTRAL_VESPENEGEYSER.value,
    UNIT_TYPEID.NEUTRAL_XELNAGATOWER.value,
]
ALL_NEUTRAL_SET = set(ALL_NEUTRAL)


NEUTRAL_ATTACKABLE_SET = ALL_NEUTRAL_SET.difference(NEUTRAL_MINERAL_SET.union(NEUTRAL_VESPENE_SET))


z_train_tar_map = {
  "Train_Baneling_quick": UNIT_TYPEID.ZERG_BANELING.value,
  "Train_Corruptor_quick": UNIT_TYPEID.ZERG_CORRUPTOR.value,
  "Train_Drone_quick": UNIT_TYPEID.ZERG_DRONE.value,
  "Train_Hydralisk_quick": UNIT_TYPEID.ZERG_HYDRALISK.value,
  "Train_Infestor_quick": UNIT_TYPEID.ZERG_INFESTOR.value,
  "Train_Mutalisk_quick": UNIT_TYPEID.ZERG_MUTALISK.value,
  "Train_Overlord_quick": UNIT_TYPEID.ZERG_OVERLORD.value,
  "Train_Queen_quick": UNIT_TYPEID.ZERG_QUEEN.value,
  "Train_Roach_quick": UNIT_TYPEID.ZERG_ROACH.value,
  "Train_SwarmHost_quick": UNIT_TYPEID.ZERG_SWARMHOSTMP.value,
  "Train_Ultralisk_quick": UNIT_TYPEID.ZERG_ULTRALISK.value,
  "Train_Viper_quick": UNIT_TYPEID.ZERG_VIPER.value,
  "Train_Zergling_quick": UNIT_TYPEID.ZERG_ZERGLING.value,
}


z_train_tar_map_v6 = {
  "Train_Corruptor_quick": UNIT_TYPEID.ZERG_CORRUPTOR.value,
  "Train_Drone_quick": UNIT_TYPEID.ZERG_DRONE.value,
  "Train_Hydralisk_quick": UNIT_TYPEID.ZERG_HYDRALISK.value,
  "Train_Infestor_quick": UNIT_TYPEID.ZERG_INFESTOR.value,
  "Train_Mutalisk_quick": UNIT_TYPEID.ZERG_MUTALISK.value,
  "Train_Overlord_quick": UNIT_TYPEID.ZERG_OVERLORD.value,
  "Train_Queen_quick": UNIT_TYPEID.ZERG_QUEEN.value,
  "Train_Roach_quick": UNIT_TYPEID.ZERG_ROACH.value,
  "Train_SwarmHost_quick": UNIT_TYPEID.ZERG_SWARMHOSTMP.value,
  "Train_Ultralisk_quick": UNIT_TYPEID.ZERG_ULTRALISK.value,
  "Train_Viper_quick": UNIT_TYPEID.ZERG_VIPER.value,
  "Train_Zergling_quick": UNIT_TYPEID.ZERG_ZERGLING.value,
}


z_morph_tar_map = {
  "Train_Baneling_quick": (UNIT_TYPEID.ZERG_ZERGLING.value,
                           UNIT_TYPEID.ZERG_BANELINGCOCOON.value,
                           UNIT_TYPEID.ZERG_BANELING.value),
  "Morph_BroodLord_quick": (UNIT_TYPEID.ZERG_CORRUPTOR.value,
                            UNIT_TYPEID.ZERG_BROODLORDCOCOON.value,
                            UNIT_TYPEID.ZERG_BROODLORD.value),
  "Morph_Lurker_quick": (UNIT_TYPEID.ZERG_HYDRALISK.value,
                         UNIT_TYPEID.ZERG_LURKERMPEGG.value,
                         UNIT_TYPEID.ZERG_LURKERMP.value),
  "Morph_OverlordTransport_quick": (UNIT_TYPEID.ZERG_OVERLORD.value,
                                    UNIT_TYPEID.ZERG_TRANSPORTOVERLORDCOCOON.value,
                                    UNIT_TYPEID.ZERG_OVERLORDTRANSPORT.value),
  "Morph_Overseer_quick": (UNIT_TYPEID.ZERG_OVERLORD.value,
                           UNIT_TYPEID.ZERG_OVERLORDCOCOON.value,
                           UNIT_TYPEID.ZERG_OVERSEER.value),
  "Morph_Ravager_quick": (UNIT_TYPEID.ZERG_ROACH.value,
                          UNIT_TYPEID.ZERG_RAVAGERCOCOON.value,
                          UNIT_TYPEID.ZERG_RAVAGER.value),
}


z_morph_tar_map_v6 = {
  "Morph_Baneling_quick": (UNIT_TYPEID.ZERG_ZERGLING.value,
                           UNIT_TYPEID.ZERG_BANELINGCOCOON.value,
                           UNIT_TYPEID.ZERG_BANELING.value),
  "Morph_BroodLord_quick": (UNIT_TYPEID.ZERG_CORRUPTOR.value,
                            UNIT_TYPEID.ZERG_BROODLORDCOCOON.value,
                            UNIT_TYPEID.ZERG_BROODLORD.value),
  "Morph_Lurker_quick": (UNIT_TYPEID.ZERG_HYDRALISK.value,
                         UNIT_TYPEID.ZERG_LURKERMPEGG.value,
                         UNIT_TYPEID.ZERG_LURKERMP.value),
  "Morph_OverlordTransport_quick": (UNIT_TYPEID.ZERG_OVERLORD.value,
                                    UNIT_TYPEID.ZERG_TRANSPORTOVERLORDCOCOON.value,
                                    UNIT_TYPEID.ZERG_OVERLORDTRANSPORT.value),
  "Morph_Overseer_quick": (UNIT_TYPEID.ZERG_OVERLORD.value,
                           UNIT_TYPEID.ZERG_OVERLORDCOCOON.value,
                           UNIT_TYPEID.ZERG_OVERSEER.value),
  "Morph_Ravager_quick": (UNIT_TYPEID.ZERG_ROACH.value,
                          UNIT_TYPEID.ZERG_RAVAGERCOCOON.value,
                          UNIT_TYPEID.ZERG_RAVAGER.value),
}


z_skill_tar_map = {
  "Effect_Abduct_screen": (UNIT_TYPEID.ZERG_VIPER.value, None),
  "Effect_InjectLarva_screen": (UNIT_TYPEID.ZERG_QUEEN.value, None),
  "Effect_Transfusion_screen": (UNIT_TYPEID.ZERG_QUEEN.value, None),
  "Effect_ViperConsume_screen": (UNIT_TYPEID.ZERG_VIPER.value, None),
  "Effect_NeuralParasite_screen": (UNIT_TYPEID.ZERG_INFESTOR.value, UPGRADE_ID.NEURALPARASITE.value),
  "Effect_ParasiticBomb_screen": (UNIT_TYPEID.ZERG_VIPER.value, None),
  "Effect_CausticSpray_screen": (UNIT_TYPEID.ZERG_CORRUPTOR.value, None),
  "Effect_Contaminate_screen": (UNIT_TYPEID.ZERG_OVERSEER.value, None),
  "Effect_BlindingCloud_screen": (UNIT_TYPEID.ZERG_VIPER.value, None),
  "Effect_CorrosiveBile_screen": (UNIT_TYPEID.ZERG_RAVAGER.value, None),
  "Effect_FungalGrowth_screen": (UNIT_TYPEID.ZERG_INFESTOR.value, None),
  "Effect_InfestedTerrans_screen": (UNIT_TYPEID.ZERG_INFESTOR.value, None),
  "Effect_LocustSwoop_screen": (UNIT_TYPEID.ZERG_SWARMHOSTMP.value, None),
  "Effect_SpawnLocusts_screen": (UNIT_TYPEID.ZERG_SWARMHOSTMP.value, None),
  "Effect_SpawnChangeling_quick": (UNIT_TYPEID.ZERG_OVERSEER.value, None),
  "Effect_Explode_quick": (UNIT_TYPEID.ZERG_BANELING.value, None),
  "BurrowDown_Lurker_quick": (UNIT_TYPEID.ZERG_LURKERMP.value, None),
  "BurrowUp_Lurker_quick": (UNIT_TYPEID.ZERG_LURKERMPBURROWED.value, None),
  "UnloadAllAt_Overlord_screen": (UNIT_TYPEID.ZERG_OVERLORDTRANSPORT.value, None),
  "Behavior_GenerateCreepOff_quick": (UNIT_TYPEID.ZERG_OVERLORD.value, None),
  "Behavior_GenerateCreepOn_quick": (UNIT_TYPEID.ZERG_OVERLORD.value, None),
  "Behavior_HoldFireOff_Lurker_quick": (UNIT_TYPEID.ZERG_LURKERMPBURROWED.value, None),
  "Behavior_HoldFireOn_Lurker_quick": (UNIT_TYPEID.ZERG_LURKERMPBURROWED.value, None),
}


executor_pre_order = [
    # larva
    UNIT_TYPEID.ZERG_LARVA.value,
    UNIT_TYPEID.ZERG_EGG.value,
    # army units
    UNIT_TYPEID.ZERG_QUEEN.value,
    UNIT_TYPEID.ZERG_QUEENBURROWED.value,
    UNIT_TYPEID.ZERG_ULTRALISK.value,
    UNIT_TYPEID.ZERG_ULTRALISKBURROWED.value,
    UNIT_TYPEID.ZERG_BROODLORD.value,
    UNIT_TYPEID.ZERG_BROODLORDCOCOON.value,
    UNIT_TYPEID.ZERG_VIPER.value,
    UNIT_TYPEID.ZERG_CORRUPTOR.value,
    UNIT_TYPEID.ZERG_SWARMHOSTMP.value,
    UNIT_TYPEID.ZERG_SWARMHOSTBURROWEDMP.value,
    UNIT_TYPEID.ZERG_INFESTOR.value,
    UNIT_TYPEID.ZERG_INFESTORBURROWED.value,
    UNIT_TYPEID.ZERG_LURKERMP.value,
    UNIT_TYPEID.ZERG_LURKERMPBURROWED.value,
    UNIT_TYPEID.ZERG_LURKERMPEGG.value,
    UNIT_TYPEID.ZERG_MUTALISK.value,
    UNIT_TYPEID.ZERG_HYDRALISK.value,
    UNIT_TYPEID.ZERG_HYDRALISKBURROWED.value,
    UNIT_TYPEID.ZERG_RAVAGER.value,
    UNIT_TYPEID.ZERG_RAVAGERBURROWED.value,
    UNIT_TYPEID.ZERG_RAVAGERCOCOON.value,
    UNIT_TYPEID.ZERG_ROACH.value,
    UNIT_TYPEID.ZERG_ROACHBURROWED.value,
    UNIT_TYPEID.ZERG_BANELING.value,
    UNIT_TYPEID.ZERG_BANELINGBURROWED.value,
    UNIT_TYPEID.ZERG_BANELINGCOCOON.value,
    UNIT_TYPEID.ZERG_ZERGLING.value,
    UNIT_TYPEID.ZERG_ZERGLINGBURROWED.value,
    # drone
    UNIT_TYPEID.ZERG_DRONE.value,
    UNIT_TYPEID.ZERG_DRONEBURROWED.value,
    # buildings
    UNIT_TYPEID.ZERG_OVERSEER.value,
    UNIT_TYPEID.ZERG_OVERSEEROVERSIGHTMODE.value,
    UNIT_TYPEID.ZERG_OVERLORD.value,
    UNIT_TYPEID.ZERG_OVERLORDTRANSPORT.value,
    UNIT_TYPEID.ZERG_OVERLORDCOCOON.value,
    UNIT_TYPEID.ZERG_TRANSPORTOVERLORDCOCOON.value,
    UNIT_TYPEID.ZERG_INFESTORTERRAN.value,
    UNIT_TYPEID.ZERG_INFESTEDTERRANSEGG.value,
    UNIT_TYPEID.ZERG_LOCUSTMP.value,
    UNIT_TYPEID.ZERG_LOCUSTMPFLYING.value,
    UNIT_TYPEID.ZERG_BROODLING.value,
    UNIT_TYPEID.ZERG_CHANGELING.value,
    UNIT_TYPEID.ZERG_CHANGELINGMARINE.value,
    UNIT_TYPEID.ZERG_CHANGELINGMARINESHIELD.value,
    UNIT_TYPEID.ZERG_CHANGELINGZEALOT.value,
    UNIT_TYPEID.ZERG_CHANGELINGZERGLING.value,
    UNIT_TYPEID.ZERG_CHANGELINGZERGLINGWINGS.value,
    UNIT_TYPEID.ZERG_CREEPTUMORBURROWED.value,
    UNIT_TYPEID.ZERG_CREEPTUMOR.value,
    UNIT_TYPEID.ZERG_CREEPTUMORQUEEN.value,
    UNIT_TYPEID.ZERG_HATCHERY.value,
    UNIT_TYPEID.ZERG_LAIR.value,
    UNIT_TYPEID.ZERG_HIVE.value,
    UNIT_TYPEID.ZERG_NYDUSNETWORK.value,
    UNIT_TYPEID.ZERG_NYDUSCANAL.value,
    UNIT_TYPEID.ZERG_ULTRALISKCAVERN.value,
    UNIT_TYPEID.ZERG_GREATERSPIRE.value,
    UNIT_TYPEID.ZERG_SPIRE.value,
    UNIT_TYPEID.ZERG_INFESTATIONPIT.value,
    UNIT_TYPEID.ZERG_LURKERDENMP.value,
    UNIT_TYPEID.ZERG_HYDRALISKDEN.value,
    UNIT_TYPEID.ZERG_ROACHWARREN.value,
    UNIT_TYPEID.ZERG_EVOLUTIONCHAMBER.value,
    UNIT_TYPEID.ZERG_BANELINGNEST.value,
    UNIT_TYPEID.ZERG_SPINECRAWLER.value,
    UNIT_TYPEID.ZERG_SPINECRAWLERUPROOTED.value,
    UNIT_TYPEID.ZERG_SPORECRAWLER.value,
    UNIT_TYPEID.ZERG_SPORECRAWLERUPROOTED.value,
    UNIT_TYPEID.ZERG_SPAWNINGPOOL.value,
    UNIT_TYPEID.ZERG_EXTRACTOR.value,
]


ALL_UNIT_TYPES = executor_pre_order + ALL_NEUTRAL
ALL_UNIT_TYPES_SET = set(ALL_UNIT_TYPES)


RESEARCH_ABILITY_IDS = [1225, 1482, 265, 216, 1283, 1455, 217, 1282, 3709, 1454,
                        1223, 263, 3702, 3703, 3704, 3705, 3706, 1252, 1253]

MORPH_ABILITY_IDS = [1729, 1731, 80, 1372, 1220, 1218, 1216, 2332, 2708, 1448,
                     3745, 3743, 2330, 1725, 3681, 1727]


# Radius for units, used for post rule for building
BUILDINGS_RADIUS = {
    UNIT_TYPEID.ZERG_HATCHERY.value: 2.5,
    UNIT_TYPEID.ZERG_SPINECRAWLER.value: 1.0,
    UNIT_TYPEID.ZERG_SPORECRAWLER.value: 1.0,
    UNIT_TYPEID.ZERG_EXTRACTOR.value: 1.5,
    UNIT_TYPEID.ZERG_SPAWNINGPOOL.value: 1.5,
    UNIT_TYPEID.ZERG_EVOLUTIONCHAMBER.value: 1.5,
    UNIT_TYPEID.ZERG_ROACHWARREN.value: 1.5,
    UNIT_TYPEID.ZERG_BANELINGNEST.value: 1.5,
    UNIT_TYPEID.ZERG_CREEPTUMORBURROWED.value: 0.5,
    UNIT_TYPEID.ZERG_CREEPTUMOR.value: 0.5,
    UNIT_TYPEID.ZERG_CREEPTUMORQUEEN.value: 0.5,
    UNIT_TYPEID.ZERG_LAIR.value: 2.5,
    UNIT_TYPEID.ZERG_HYDRALISKDEN.value: 1.5,
    UNIT_TYPEID.ZERG_LURKERDENMP.value: 1.5,
    UNIT_TYPEID.ZERG_SPIRE.value: 1.0,
    UNIT_TYPEID.ZERG_NYDUSNETWORK.value: 1.5,
    UNIT_TYPEID.ZERG_NYDUSCANAL.value: 1.5,
    UNIT_TYPEID.ZERG_INFESTATIONPIT.value: 1.5,
    UNIT_TYPEID.ZERG_HIVE.value: 2.5,
    UNIT_TYPEID.ZERG_GREATERSPIRE.value: 1.0,
    UNIT_TYPEID.ZERG_ULTRALISKCAVERN.value: 1.5,
}
for u in NEUTRAL_VESPENE:
    BUILDINGS_RADIUS[u] = 1.5
for u in NEUTRAL_MINERAL:
    BUILDINGS_RADIUS[u] = 0.5

# Radius of space for building abilities, used for post rule for building
ABILITY_RADIUS = {
    ABILITY_ID.BUILD_HATCHERY.value: 2.5,
    ABILITY_ID.BUILD_SPINECRAWLER.value: 1.0,
    ABILITY_ID.MORPH_SPINECRAWLERROOT.value: 1.0,
    ABILITY_ID.BUILD_SPORECRAWLER.value: 1.0,
    ABILITY_ID.MORPH_SPORECRAWLERROOT: 1.0,
    # ABILITY_ID.BUILD_EXTRACTOR.value: 1.5, # on unit
    ABILITY_ID.BUILD_SPAWNINGPOOL.value: 1.5,
    ABILITY_ID.BUILD_EVOLUTIONCHAMBER.value: 1.5,
    ABILITY_ID.BUILD_ROACHWARREN.value: 1.5,
    ABILITY_ID.BUILD_BANELINGNEST.value: 1.5,
    ABILITY_ID.BUILD_CREEPTUMOR.value: 0.5,
    ABILITY_ID.BUILD_CREEPTUMOR_TUMOR.value: 0.5,
    ABILITY_ID.BUILD_CREEPTUMOR_QUEEN.value: 0.5,
    # ABILITY_ID.MORPH_LAIR.value: 2.5,  # morph
    ABILITY_ID.BUILD_HYDRALISKDEN.value: 1.5,
    ABILITY_ID.BUILD_LURKERDENMP.value: 1.5,
    ABILITY_ID.BUILD_SPIRE.value: 1.0,
    ABILITY_ID.BUILD_NYDUSWORM.value: 1.5,
    ABILITY_ID.BUILD_NYDUSNETWORK.value: 1.5,
    ABILITY_ID.BUILD_INFESTATIONPIT.value: 1.5,
    # ABILITY_ID.MORPH_HIVE.value: 2.5,  # morph
    # ABILITY_ID.MORPH_GREATERSPIRE.value: 1.5,  # morph
    ABILITY_ID.BUILD_ULTRALISKCAVERN.value: 1.5,
}
