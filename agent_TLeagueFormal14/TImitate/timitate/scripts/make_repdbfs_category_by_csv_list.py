""" make category file for zstat db"""
from os import path
import csv

from absl import app
from absl import flags


FLAGS = flags.FLAGS
flags.DEFINE_string("input_csv_path", '/csv/input/path', "input csv path",
                    short_name='i')
flags.DEFINE_string("category_name", 'PureRoach', "category name",
                    short_name='c')
flags.DEFINE_string("zstat_db_dir", '/zstat/src/dir', "input zstat dir",
                    short_name='z')


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
  category_name = FLAGS.category_name
  zstat_db_dir = FLAGS.zstat_db_dir

  assert path.exists(zstat_db_dir)
  with open(input_csv_path, 'r') as f:
    lines = list(csv.DictReader(f))

  category_fn = '.category-{}'.format(category_name)
  with open(path.join(zstat_db_dir, category_fn), 'w') as f:
    contents = [
      '{}-{}'.format(line['replay_name'], line['player_id'])
      for line in lines
    ]
    contents = '\n'.join(contents)
    print('writing below contents to {}'.format(f.name))
    print(contents)
    f.write(contents)


if __name__ == '__main__':
  app.run(main)