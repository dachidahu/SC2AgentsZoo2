""" make index file for zstat db"""
from os import path
import csv


csv_list_path = '/Users/pengsun/code/sc2_rl/TImitate/timitate/bin4/tmp_mmr_topk.csv'
zstat_db_dir = '/Users/pengsun/code/sc2_rl/TImitate/timitate/bin4/tmp_zstat'


def map_name_transform(map_name):
  # transform map_name in replay_info to map_name used in pysc2
  # Remove 'LE' and spaces
  words = map_name.split(' ')
  if words[-1] == 'LE':
    words = words[:-1]
  return ''.join(words)

assert path.exists(zstat_db_dir)
with open(csv_list_path, 'r') as f:
  lines = list(csv.DictReader(f))
  sample_line = lines[0]

index_fn = '.keys_index-{:s}-{:s}-{:s}'.format(
  map_name_transform(sample_line['map_name']),
  sample_line['start_pos_x'],
  sample_line['start_pos_y']
)

with open(path.join(zstat_db_dir, index_fn), 'w') as f:
  contents = ['{}-{}'.format(line['replay_name'], line['player_id'])
              for line in lines]
  contents = '\n'.join(contents)
  print(contents)
  print('will be written to {}'.format(f.name))
  #f.write(contents)
