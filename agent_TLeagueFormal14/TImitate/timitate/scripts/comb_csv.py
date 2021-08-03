""" combine two csv files a and b using a's header order"""
import csv
import sys
import random
from collections import OrderedDict

from absl import app
from absl import flags


FLAGS = flags.FLAGS
flags.DEFINE_string("input_csv_path_a", '/csv/input/path/a', "input csv path a",
                    short_name='a')
flags.DEFINE_string("input_csv_path_b", '/csv/input/path/b', "input csv path b",
                    short_name='b')
flags.DEFINE_string("output_csv_path", '/csv/output/path', "output csv path",
                    short_name='o')


def main(__):
  # shorter names
  input_csv_path_a = FLAGS.input_csv_path_a
  input_csv_path_b = FLAGS.input_csv_path_b
  output_csv_path = FLAGS.output_csv_path

  with open(input_csv_path_a, 'r') as f:
    lines = list(csv.DictReader(f))
    assert lines

  with open(input_csv_path_b, 'r') as f:
    lines_b = list(csv.DictReader(f))
    assert lines_b

  # for each b's line, reorder it using a's order and append it to a
  keys = lines[0].keys()
  for line in lines_b:
    o_line = OrderedDict()
    for k in keys:
      o_line[k] = line[k]
    lines.append(o_line)

  # random shuffle
  #random.shuffle(lines)

  # write output
  with open(output_csv_path, 'w') as f:
    fields = lines[0].keys()
    writer = csv.DictWriter(f, fields)
    writer.writeheader()
    writer.writerows(lines)


if __name__ == '__main__':
  app.run(main)