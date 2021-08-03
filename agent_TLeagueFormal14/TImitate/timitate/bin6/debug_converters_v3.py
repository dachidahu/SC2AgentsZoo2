from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import pickle
from os import path

from absl import app
from absl import flags
from s2clientprotocol import sc2api_pb2 as sc_pb
from pysc2 import run_configs

from timitate.lib6.pb2feature_converter import PB2FeatureConverter
from timitate.lib6.pb2all_converter import PB2AllConverter
from timitate.lib6.pb2mask_converter import PB2MaskConverter
from timitate.lib6.z_actions import ZERG_ABILITIES
from timitate.utils_replay import get_replay_actor_interface


FLAGS = flags.FLAGS
flags.DEFINE_string("replay_dir", 'replays/ext_480', "replay dir")
flags.DEFINE_string("replay_name", 'abced', "replay name")
flags.DEFINE_string("game_version", '4.8.0', "game version.")
flags.DEFINE_string("zstat_data_src", './', "zstat_data_src")
flags.DEFINE_integer("step_mul", 1, "step mul.")
flags.DEFINE_integer("player_id", 1, "player id.")
flags.DEFINE_string("prefix", 'dbgv3', 'prefix for debugging printing.')


def debug_pb2all_converter():

  # reset env/process replay from the beginning
  run_config = run_configs.get()
  replay_path = path.join(FLAGS.replay_dir, FLAGS.replay_name + '.SC2Replay')
  replay_data = run_config.replay_data(replay_path)

  # step each frame w. step_mul
  with run_config.start(version=FLAGS.game_version) as controller:
    replay_info = controller.replay_info(replay_data)
    #print(replay_info)

    # ***for debugging, VERY dangerous!!***
    map_name = replay_info.map_name
    #map_name = 'Stasis'

    pb2all = PB2AllConverter(
      zstat_data_src=FLAGS.zstat_data_src,
      input_map_size=(128, 128),
      output_map_size=(128, 128),
      dict_space=True,
      game_version=FLAGS.game_version,
      zmaker_version='v5',
      zstat_zeroing_prob=0.0,
      max_bo_count=50,
      max_bobt_count=20,
      delete_dup_action='v2',
      sort_executors='v2',
      inj_larv_rule=True
    )
    pb2all.reset(
      replay_name=FLAGS.replay_name,
      player_id=FLAGS.player_id,
      mmr=6000,
      map_name=map_name
    )

    controller.start_replay(sc_pb.RequestStartReplay(
      replay_data=replay_data,
      map_data=None,
      options=get_replay_actor_interface(map_name),
      observed_player_id=FLAGS.player_id,
      disable_fog=False))
    controller.step()
    last_pb = None
    last_game_info = None
    step = 0
    while True:
      #print(step)
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

      # printing
      if data:
        # note: data is [((obs, act), w)]
        act = data[0][0][1]
        ab_idx = act['A_AB']
        print(', '.join([
          FLAGS.prefix,
          'gal:{}'.format(pb_obs.observation.game_loop),  # game loop
          'abn:{}'.format(ZERG_ABILITIES[ab_idx][0]),  # ability name
        ]))
      # step the replay
      controller.step(1)  # step_mul
      step += 1


def main(_):
  debug_pb2all_converter()


if __name__ == '__main__':
  app.run(main)
