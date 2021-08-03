""" Run a BackwardBranchOVRWinrateViewer.

Example:
"""
import logging

from absl import app
from absl import flags

from distladder3.frontend_tool.ovr_winrate_viewer import \
  BackwardBranchOVRWinrateViewer


FLAGS = flags.FLAGS
flags.DEFINE_string("player_manager_endpoint", 'localhost:5526',
                    "player_manager_endpoint")
flags.DEFINE_string("match_scheduler_endpoint", 'localhost:6688',
                    "match_scheduler_endpoint")
flags.DEFINE_string("results_collector_endpoint", 'localhost:6888',
                    "results_collector_endpoint")
flags.DEFINE_string("primary_player_name_pattern", 'init_model:0001',
                    "primary_player_name_pattern. ")
flags.DEFINE_multi_string("oppo_player_name", ['AgentJones', 'Default_AI_2'],
                          "opponent player name. can occur multiple times")
flags.DEFINE_integer("cycle", 0, "no. matches to be scheduled")
flags.DEFINE_string("timestamp_criterion", "all",
                    'timestamp criterion. [all] | latest. ')
flags.DEFINE_string("output_dir", '/root/evfrontendYYMMDD',
                    "output dir where the results files go.")


def main(_):
  logging.info('start winrate viewer, output to {}'.format(FLAGS.output_dir))
  wv = BackwardBranchOVRWinrateViewer(
    player_manager_endpoint=FLAGS.player_manager_endpoint,
    match_scheduler_endpoint=FLAGS.match_scheduler_endpoint,
    results_collector_endpoint=FLAGS.results_collector_endpoint,
    primary_player_name_pattern=FLAGS.primary_player_name_pattern,
    oppo_player_names=FLAGS.oppo_player_name,
    cycle=FLAGS.cycle,
    timestamp_criterion=FLAGS.timestamp_criterion,
    output_dir=FLAGS.output_dir
  )
  wv.run()


if __name__ == '__main__':
  app.run(main)