""" make index file for zstat db"""
from os import path
import csv

from absl import app
from absl import flags


FLAGS = flags.FLAGS
flags.DEFINE_string("input_csv_path", '/csv/input/path', "input csv path",
                    short_name='i')
flags.DEFINE_string("zstat_db_dir", '/zstat/src/dir', "input zstat dir",
                    short_name='z')
# input_csv_path = sys.argv[1]
# zstat_db_dir = sys.argv[2]


def map_name_transform(map_name):
  # transform map_name in replay_info to map_name used in pysc2
  # Remove 'LE' and spaces
  words = map_name.split(' ')
  if words[-1] == 'LE':
    words = words[:-1]
  return ''.join(words)


def main(__):
  # shorter names
  input_csv_path = FLAGS.input_csv_path
  zstat_db_dir = FLAGS.zstat_db_dir

  assert path.exists(zstat_db_dir)
  with open(input_csv_path, 'r') as f:
    lines = list(csv.DictReader(f))

  index_fn_to_lines = {}
  for line in lines:
    index_fn = '.keys_index-{:s}-{:s}-{:s}'.format(
      map_name_transform(line['map_name']),
      line['start_pos_x'],
      line['start_pos_y']
    )
    if index_fn not in index_fn_to_lines:
      index_fn_to_lines[index_fn] = []
    index_fn_to_lines[index_fn].append(line)
  print('will write to index_fns', list(index_fn_to_lines.keys()))

  for each_index_fn in index_fn_to_lines.keys():
    with open(path.join(zstat_db_dir, each_index_fn), 'w') as f:
      contents = [
        '{}-{}'.format(line['replay_name'], line['player_id'])
        for line in index_fn_to_lines[each_index_fn]
      ]
      contents = '\n'.join(contents)
      print('writing below contents to {}'.format(f.name))
      print(contents)
      f.write(contents)


if __name__ == '__main__':
  app.run(main)