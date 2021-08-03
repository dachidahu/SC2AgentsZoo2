""" filter replays by a csv list."""
import csv
import os
from os import path
from shutil import copyfile

import progressbar


csv_list_path = '/Users/pengsun/code/sc2_rl/TImitate/timitate/bin4/tmp_infos.csv'
src_replay_dir = '/Users/pengsun/code/sc2_rl/TImitate/timitate/bin4/tmp_replay'
dst_replay_dir = '/Users/pengsun/code/sc2_rl/TImitate/timitate/bin4/tmp_replay_selected'
mmr_thres = 10
apm_thres = 5
allowed_map_names = [
  '凯罗斯中转站-天梯版',
  'Kairos Junction LE',
  'Para Site LE',
]


# collect all replay infos
with open(csv_list_path, 'r') as f:
  lines = list(csv.DictReader(f))

# now filter them
os.makedirs(dst_replay_dir, exist_ok=True)
with progressbar.ProgressBar(max_value=len(lines)) as bb:
  for i, line in enumerate(lines):
    bb.update(i)
    if int(line['mmr']) < mmr_thres:
      continue
    if int(line['apm']) < apm_thres:
      continue
    if line['map_name'] not in allowed_map_names:
      continue
    # now we can copy the replay from src to dst
    fn = '{:s}.SC2Replay'.format(line['replay_name'])
    src = path.join(src_replay_dir, fn)
    dst = path.join(dst_replay_dir, fn)
    if path.exists(dst):
      continue
    #print('copying {}'.format(dst))
    copyfile(src=src, dst=dst)
