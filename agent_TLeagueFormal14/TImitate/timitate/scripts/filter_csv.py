""" filter a a csv list."""
import csv
import sys
import random


input_csv_path = '/my/csv/path'
output_csv_path = '/my/csv/out/path'
mmr_thres = 3000
apm_thres = 100
game_duration_loops = 1500
validation_ratio = 0.05
allowed_map_names = []
# allowed_map_names = [
#   'Kairos Junction LE',
#   'Para Site LE',
# ]


# collect all replay infos
with open(input_csv_path, 'r') as f:
  lines = list(csv.DictReader(f))

# random shuffle
random.shuffle(lines)

# now filter them
qualified_lines = []
for i, line in enumerate(lines):
  if int(line['mmr']) < mmr_thres:
    continue
  if int(line['apm']) < apm_thres:
    continue
  if allowed_map_names and line['map_name'] not in allowed_map_names:
    continue
  if int(line['game_duration_loops']) < game_duration_loops:
    continue
  line['validation'] = 0
  qualified_lines.append(line)

# set valadition tasks
total_num = len(qualified_lines)
for line in qualified_lines[-int(validation_ratio*total_num):]:
  line['validation'] = 1

# save target csv file
with open(output_csv_path, 'w') as f:
  fields = qualified_lines[0].keys()
  writer = csv.DictWriter(f, fields)
  writer.writeheader()
  writer.writerows(qualified_lines)
