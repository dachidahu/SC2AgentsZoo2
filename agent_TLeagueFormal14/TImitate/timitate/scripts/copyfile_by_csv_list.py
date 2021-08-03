""" copyfile by a csv list. each filename replay_name-player_id """
import os
from os import path
from shutil import copyfile
import csv


csv_list_path = '/Users/pengsun/code/sc2_rl/TImitate/timitate/bin4/tmp_mmr_topk.csv'
src_dir = '/Users/pengsun/code/sc2_rl/TImitate/timitate/bin4/tmp_zstat'
dst_dir = '/Users/pengsun/code/sc2_rl/TImitate/timitate/bin4/tmp_zstat_top3'


os.makedirs(dst_dir, exist_ok=True)
with open(csv_list_path, 'r') as f:
  lines = list(csv.DictReader(f))
  for line in lines:
    fn = '{}-{}'.format(line['replay_name'], line['player_id'])
    src = path.join(src_dir, fn)
    dst = path.join(dst_dir, fn)
    copyfile(src=src, dst=dst)
