""" Run a greedy chkpoint player maker
"""
import logging

from absl import app
from absl import flags

from distladder3.player_manager.chkpoint_player_maker import (
  GreedyChkpointPlayerMaker
)


FLAGS = flags.FLAGS
flags.DEFINE_string('player_manager_endpoint', 'localhost:5526', 'pm ep')
flags.DEFINE_string("agent_dir", '/root/SC2AgentsZoo/agent_TLeagueFormal2',
                    "full agent directory")
flags.DEFINE_multi_string(
  "agent_config_kv",
  ["nv,17", "policy_type,tpolicies.convnet.pure_conv.PureConv"],
  "agent_config key,value. E.g., n_v,17 "
  "policy_type,tpolicies.convnet.pure_conv.PureConv "
  "Can occur multiple times."
)
# flags.DEFINE_string("policy", 'tpolicies.convnet.pure_conv.PureConv',
#                     "policy name", short_name='p')
# flags.DEFINE_integer("n_v", 1,
#                      "number of values head for policy")
flags.DEFINE_string("watched_chkpoints_root_dir",
                    '/root/tleague_outdir/aaa_chkpoints',
                    "Watched tleague chkpoints dir during training.")
flags.DEFINE_string("output_agent_configs_dir", "/root/zzz_configs",
                    "output agent configs dir")


def main(_):
  logging.info('start watching {}'.format(FLAGS.watched_chkpoints_root_dir))

  agent_config_kvs = {}
  for item in FLAGS.agent_config_kv:
    k, v = item.split(',')
    agent_config_kvs[k] = v
  cfg_maker = GreedyChkpointPlayerMaker(
    player_manager_endpoint=FLAGS.player_manager_endpoint,
    agent_dir=FLAGS.agent_dir,
    agent_config_kvs=agent_config_kvs,
    watched_chkpoints_root_dir=FLAGS.watched_chkpoints_root_dir,
    output_agent_configs_dir=FLAGS.output_agent_configs_dir,
  )
  cfg_maker.run()


if __name__ == '__main__':
  app.run(main)