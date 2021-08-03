""" shuffle a csv file"""
import csv
import random

from absl import app
from absl import flags


FLAGS = flags.FLAGS
flags.DEFINE_string("input_csv_path", '/csv/input/path/a', "input csv path ",
                    short_name='i')
flags.DEFINE_string("output_csv_path", '/csv/output/path', "output csv path",
                    short_name='o')


def main(__):
  # shorter names
  input_csv_path = FLAGS.input_csv_path
  output_csv_path = FLAGS.output_csv_path

  with open(input_csv_path, 'r') as f:
    lines = list(csv.DictReader(f))
    assert lines

  # random shuffle
  random.shuffle(lines)

  # write output
  with open(output_csv_path, 'w') as f:
    fields = lines[0].keys()
    writer = csv.DictWriter(f, fields)
    writer.writeheader()
    writer.writerows(lines)


if __name__ == '__main__':
  app.run(main)