"""random sample replays by a csv"""
import csv
import random

from absl import app
from absl import flags


FLAGS = flags.FLAGS
flags.DEFINE_string("input_csv_path", '/csv/input/path', "input csv path",
                    short_name='i')
flags.DEFINE_string("output_csv_path", '/csv/output/path', "output csv path",
                    short_name='o')
flags.DEFINE_multi_string("allowed_map_names", [], "allowed map names",
                          short_name='m')
flags.DEFINE_multi_string("allowed_game_versions", [], "allowed game versions",
                          short_name='g')
flags.DEFINE_integer("max_num_checked", 10, "maximum number to check")


def main(__):
  # shorter names
  input_csv_path = FLAGS.input_csv_path
  output_csv_path = FLAGS.output_csv_path
  allowed_map_names = FLAGS.allowed_map_names
  allowed_game_versions = FLAGS.allowed_game_versions
  max_num_checked = FLAGS.max_num_checked

  # collect all replay infos
  print('processing {}...'.format(input_csv_path), flush=True)
  with open(input_csv_path, 'r') as f:
    lines = list(csv.DictReader(f))

  # now process
  qualified_lines = []
  for map_name in allowed_map_names:
    for game_version in allowed_game_versions:
      items = []
      for i, ell in enumerate(lines):
        if not ell['game_version'].startswith(game_version):
          continue
        if map_name != ell['map_name']:
          continue
        items.append(ell)
        if len(items) >= max_num_checked:
          break
      if not items:
        print('Cannot find for {}, {}'.format(map_name, game_version))
      else:
        qualified_lines.append(random.choice(items))

  # save target csv file
  with open(output_csv_path, 'w') as f:
    fields = qualified_lines[0].keys()
    writer = csv.DictWriter(f, fields)
    writer.writeheader()
    writer.writerows(qualified_lines)
  print('done writing {}.'.format(output_csv_path), flush=True)


if __name__ == '__main__':
  app.run(main)
