""" Run a match scheduler

The match scheduler
* Receives message that requires starting new match series
* Send message to match server

Example:

python3 run_match_scheduler.py \
  --port 6688
  --match_server_endpoint localhost:6788 \
"""
from absl import app
from absl import flags

from distladder3.cores.match_scheduler import MatchScheduler


FLAGS = flags.FLAGS
flags.DEFINE_string("port", '6688', "Port")
flags.DEFINE_string("match_server_endpoint", 'localhost:6788',
                    "match server Endpoint")

def main(_):
  ms = MatchScheduler(port=FLAGS.port,
                      match_server_ep=FLAGS.match_server_endpoint)
  ms.run()


if __name__ == '__main__':
  app.run(main)

