""" copyfile (zstat and/or replay) by a csv list. """
import os
from os import path
from shutil import copyfile
import csv

from absl import app
from absl import flags


FLAGS = flags.FLAGS
flags.DEFINE_string("input_csv_path", '/csv/input/path', "input csv path",
                    short_name='i')
flags.DEFINE_string("zstat_src_dir", '/zstat/src/dir', "input zstat dir",
                    short_name='z')
flags.DEFINE_string("replay_src_dir", None,
                    "replay dir, None means not copying replays",
                    short_name='r')
flags.DEFINE_string("dst_dir", '/dst/dir', "output dir", short_name='o')
# input_csv_path = '/mnt/replays/471_48x_49x_mv9.filter.shuffle.mmr3500.small_sample1.csv'
# zstat_src_dir = '/mnt/replay_ds/rp1706-mv9-zstat'
# replay_src_dir = '/mnt/replays/extmv10_zvz'
# dst_dir = '/mnt/replay_ds/rp1706-sample'


def main(__):
  # shorter names
  input_csv_path = FLAGS.input_csv_path
  zstat_src_dir = FLAGS.zstat_src_dir
  replay_src_dir = FLAGS.replay_src_dir
  dst_dir = FLAGS.dst_dir

  os.makedirs(dst_dir, exist_ok=True)
  with open(input_csv_path, 'r') as f:
    lines = list(csv.DictReader(f))
    for line in lines:
      zstat_fn = '{}-{}'.format(line['replay_name'], line['player_id'])
      zstat_src = path.join(zstat_src_dir, zstat_fn)
      zstat_dst = path.join(dst_dir, zstat_fn)
      copyfile(src=zstat_src, dst=zstat_dst)

      if replay_src_dir is not None:
        replay_fn = '{}.SC2Replay'.format(line['replay_name'])
        replay_src = path.join(replay_src_dir, replay_fn)
        replay_dst = path.join(dst_dir, replay_fn)
        copyfile(src=replay_src, dst=replay_dst)


if __name__ == '__main__':
  app.run(main)