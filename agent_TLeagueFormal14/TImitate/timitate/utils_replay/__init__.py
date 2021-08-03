from s2clientprotocol import sc2api_pb2 as sc_pb
from pysc2.lib import point
from timitate.utils.utils import map_name_transform
from timitate.utils.const import MAP_ORI_SIZE_DICT, MAP_PLAYABLE_SIZE_DICT


def get_dft_sc2_interface():
  """get default sc2 interface when starting the game.

  It uses a small enough size (16, 16) for the irrelevant feature layers"""
  size = point.Point(16, 16)
  sc_interface = sc_pb.InterfaceOptions(
    raw=True, score=False, feature_layer=sc_pb.SpatialCameraSetup(width=24))
  size.assign_to(sc_interface.feature_layer.resolution)
  size.assign_to(sc_interface.feature_layer.minimap_resolution)
  return sc_interface


def get_replay_actor_interface(map_name, crop=False):
  map_name = map_name_transform(map_name)
  map_size = MAP_PLAYABLE_SIZE_DICT[map_name] if crop else MAP_ORI_SIZE_DICT[map_name]
  screen_size = point.Point(16, 16)
  minimap_size = point.Point(int(map_size[0]), int(map_size[1]))
  interface = sc_pb.InterfaceOptions(
    raw=True, score=True, feature_layer=sc_pb.SpatialCameraSetup(width=24))
  screen_size.assign_to(interface.feature_layer.resolution)
  minimap_size.assign_to(interface.feature_layer.minimap_resolution)
  if crop:
    interface.feature_layer.crop_to_playable_area = True
    interface.raw_crop_to_playable_area = True
  return interface
