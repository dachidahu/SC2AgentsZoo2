""" process the replay dataset CSV file, filter/output the mmr"""
import csv
import progressbar


csv_path = '/Users/pengsun/code/sc2_rl/TImitate/timitate/bin4/tmp_infos.csv'
K = 3  # output topK mmr
filter_map_name = 'Kairos Junction LE'
filter_start_pos_x = '31.5'
filter_start_pos_y = '140.5'
output_csv_path = '/Users/pengsun/code/sc2_rl/TImitate/timitate/bin4/tmp_mmr_topk.csv'


# select the top K from all TODO: heap sorting
mmr_d = {}
with open(csv_path, 'r') as f:
  lines = list(csv.DictReader(f))
  with progressbar.ProgressBar(max_value=len(lines)) as bb:
    for i, line in enumerate(lines):
      bb.update(i)
      # should insert it?
      if filter_map_name is not None and line['map_name'] != filter_map_name:
        continue
      if filter_start_pos_x is not None and line['start_pos_x'] != filter_start_pos_x:
        continue
      if filter_start_pos_y is not None and line['start_pos_y'] != filter_start_pos_y:
        continue
      key = int(line['mmr'])
      mmr_d[key] = line
      if len(mmr_d) > K:
        # delete the smallest (key, value)
        key = min(mmr_d.keys())
        mmr_d.pop(key)

# the sorted top K
items = list(zip(mmr_d.keys(), mmr_d.values()))
sitems = sorted(items, key=lambda x: x[0], reverse=True)  # x[0] is mmr

# to stdout
for each in sitems:
  line = each[1]
  print('{}: {}-{} {}'.format(each[0], line['replay_name'], line['player_id'],
                              line['map_name']))

# to file
fieldnames = lines[0].keys()
with open(output_csv_path, 'w') as ff:
  writer = csv.DictWriter(ff, fieldnames=fieldnames)
  writer.writeheader()
  for each in sitems:
    line = each[1]
    writer.writerow(line)