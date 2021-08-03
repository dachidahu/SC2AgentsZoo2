""" copyfile (zstat & replay) by a csv list. """
import os
from os import path
from shutil import copyfile
import csv


csv_list_path = '/mnt/replays/471_48x_49x_mv9.filter.shuffle.mmr3500.small_sample1.csv'
zstat_src_dir = '/mnt/replay_ds/rp1706-mv9-zstat'
replay_src_dir = '/mnt/replays/extmv10_zvz'
dst_dir = '/mnt/replay_ds/rp1706-sample'


os.makedirs(dst_dir, exist_ok=True)
with open(csv_list_path, 'r') as f:
  lines = list(csv.DictReader(f))
  for line in lines:
    zstat_fn = '{}-{}'.format(line['replay_name'], line['player_id'])
    zstat_src = path.join(zstat_src_dir, zstat_fn)
    zstat_dst = path.join(dst_dir, zstat_fn)
    copyfile(src=zstat_src, dst=zstat_dst)

    replay_fn = '{}.SC2Replay'.format(line['replay_name'])
    replay_src = path.join(replay_src_dir, replay_fn)
    replay_dst = path.join(dst_dir, replay_fn)
    copyfile(src=replay_src, dst=replay_dst)
