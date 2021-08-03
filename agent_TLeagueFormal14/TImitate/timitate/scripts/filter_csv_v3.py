"""filter a csv file and generate a new csv file"""
import csv
import random

from absl import app
from absl import flags


FLAGS = flags.FLAGS
flags.DEFINE_string("input_csv_path", '/csv/input/path', "input csv path",
                    short_name='i')
flags.DEFINE_string("output_csv_path", '/csv/output/path', "output csv path",
                    short_name='o')
flags.DEFINE_integer("mmr_thres", None, "mmr threshold")
flags.DEFINE_integer("apm_thres", None, "apm threshold")
flags.DEFINE_integer("game_duration_loops_thres", None,
                     "game_duration_loops threshold")
flags.DEFINE_multi_string("allowed_map_names", [], "allowed map names",
                          short_name='m')
flags.DEFINE_string("result", None, "result: Victor, Defeat, etc.")
flags.DEFINE_string("start_pos_x", None, "start_pos_x in string")
flags.DEFINE_string("start_pos_y", None, "start_pos_y in string")
flags.DEFINE_float("validation_ratio", None, "validation ratio, "
                                             "0.05 means 5 percent")


def main(__):
  # shorter names
  input_csv_path = FLAGS.input_csv_path
  output_csv_path = FLAGS.output_csv_path
  mmr_thres = FLAGS.mmr_thres
  apm_thres = FLAGS.apm_thres
  game_duration_loops = FLAGS.game_duration_loops_thres
  validation_ratio = FLAGS.validation_ratio
  result = FLAGS.result
  start_pos_x = FLAGS.start_pos_x
  start_pos_y = FLAGS.start_pos_y
  allowed_map_names = FLAGS.allowed_map_names

  # collect all replay infos
  print('processing {}...'.format(input_csv_path), flush=True)
  with open(input_csv_path, 'r') as f:
    lines = list(csv.DictReader(f))

  # random shuffle
  random.shuffle(lines)

  # now filter them
  qualified_lines = []
  for i, line in enumerate(lines):
    if mmr_thres and int(line['mmr']) < mmr_thres:
      continue
    if apm_thres and int(line['apm']) < apm_thres:
      continue
    if allowed_map_names and line['map_name'] not in allowed_map_names:
      continue
    if game_duration_loops and (int(line['game_duration_loops'])
                                < game_duration_loops):
      continue
    if result and line['result'] != result:
      continue
    if start_pos_x and line['start_pos_x'] != start_pos_x:
      continue
    if start_pos_y and line['start_pos_y'] != start_pos_y:
      continue
    assert 'validation' in line
    qualified_lines.append(line)

  # set validation tasks
  total_num = len(qualified_lines)
  if validation_ratio is not None and validation_ratio > 0.0:
    for line in qualified_lines[-int(validation_ratio*total_num):]:
      line['validation'] = 1

  # save target csv file
  with open(output_csv_path, 'w') as f:
    fields = qualified_lines[0].keys()
    writer = csv.DictWriter(f, fields)
    writer.writeheader()
    writer.writerows(qualified_lines)
  print('done writing {}.'.format(output_csv_path), flush=True)


if __name__ == '__main__':
  app.run(main)
