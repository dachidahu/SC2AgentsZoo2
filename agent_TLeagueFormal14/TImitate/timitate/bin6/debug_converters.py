from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import pickle

from absl import app
from absl import flags
from timitate.lib6.pb2feature_converter import PB2FeatureConverter
from timitate.lib6.pb2all_converter import PB2AllConverter
from timitate.lib6.pb2mask_converter import PB2MaskConverter
from pysc2 import run_configs
from os import path
from s2clientprotocol import sc2api_pb2 as sc_pb
from timitate.utils_replay import get_replay_actor_interface


FLAGS = flags.FLAGS
flags.DEFINE_string("pb_filepath", 'example.dat', "pb filepath for debug.")
flags.DEFINE_string("replay_path", './', "replay filepath for debug.")
flags.DEFINE_string("game_version", '4.8.0', "game version.")
flags.DEFINE_string("zstat_data_src", './', "zstat_data_src")
flags.DEFINE_string("map_name", 'KairosJunction', "map name.")
flags.DEFINE_integer("step_mul", 1, "step mul.")
flags.DEFINE_integer("player_id", 1, "player id.")


def debug_pb2mask_converter():
  pb2mask = PB2MaskConverter(max_unit_num=512,
                             map_resolution=(128, 128),
                             game_version='4.7.1',
                             dict_space=True)
  print(pb2mask.space)
  with open(FLAGS.pb_filepath, 'rb') as f:
    frames = pickle.load(f)
  for pb in frames:
    mask = pb2mask.convert(pb)
    print(mask)


def debug_pb2feature_converter():
  import numpy as np
  pb2feature = PB2FeatureConverter(
    zstat_data_src="/Users/hanlei/Desktop/zstat_ana/rp1209-mv-zstat-mmr-selected100/")
  print(pb2feature.space)
  pb2feature.reset(replay_name=None, player_id=FLAGS.player_id, mmr=7000, map_name=FLAGS.map_name)
  with open(FLAGS.pb_filepath, 'rb') as f:
    frames = pickle.load(f)
  for pb in frames:
    feature = pb2feature.convert(pb, last_tar_tag=None, last_units=[])
    for feat in feature:
      print('{}: {}'.format(feat.shape, np.max(feat)))
    print('*' * 50)


def debug_pb2all_converter():
  pb2all = PB2AllConverter(
    zstat_data_src=FLAGS.zstat_data_src,
    dict_space=True,
    game_version=FLAGS.game_version,
    delete_dup_action='v2',
    sort_executors='v2',
    inj_larv_rule=True)
  pb2all.reset(
    replay_name=FLAGS.replay_path.split('/')[-1],
    player_id=FLAGS.player_id,
    mmr=6000,
    map_name=FLAGS.map_name)

  # reset env/process replay from the beginning
  run_config = run_configs.get()
  replay_path = path.join(FLAGS.replay_path)
  replay_data = run_config.replay_data(replay_path)

  # step each frame w. step_mul
  with run_config.start(version=FLAGS.game_version) as controller:
    replay_info = controller.replay_info(replay_data)
    print(replay_info)
    controller.start_replay(sc_pb.RequestStartReplay(
      replay_data=replay_data,
      map_data=None,
      options=get_replay_actor_interface(FLAGS.map_name),
      observed_player_id=FLAGS.player_id,
      disable_fog=False))
    controller.step()
    last_pb = None
    last_game_info = None
    while True:
      pb_obs = controller.observe()
      game_info = controller.game_info()
      if last_pb is None:
        last_pb = pb_obs
        last_game_info = game_info
        continue
      if pb_obs.player_result:
        # episode end, the zstat to this extent is what we need
        break
      # pb2all
      data = pb2all.convert(
        pb=(last_pb, last_game_info),
        next_pb=(pb_obs, game_info))
      last_pb = pb_obs
      last_game_info = game_info
      # step the replay
      controller.step(1)  # step_mul


def main(_):
  # debug_pb2feature_converter()
  debug_pb2all_converter()
  # debug_pb2mask_converter()


if __name__ == '__main__':
  app.run(main)
