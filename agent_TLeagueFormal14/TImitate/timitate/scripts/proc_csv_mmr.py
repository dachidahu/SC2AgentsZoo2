""" process the replay dataset CSV file, filter/output the mmr"""
import csv
import progressbar


csv_path = '/Users/pengsun/code/sc2_rl/TImitate/timitate/bin4/tmp_infos.csv'
K = 3  # output topK mmr


# select the top K from all TODO: heap sorting
mmr_d = {}
with open(csv_path, 'r') as f:
  lines = list(csv.DictReader(f))
  with progressbar.ProgressBar(max_value=len(lines)) as bb:
    for i, line in enumerate(lines):
      bb.update(i)
      # insert it
      key = int(line['mmr'])
      value = (
        str(line['replay_name']),
        str(line['player_id']),
        str(line['map_name'])
      )
      mmr_d[key] = value
      if len(mmr_d) > K:
        # delete the smallest (key, value)
        key = min(mmr_d.keys())
        mmr_d.pop(key)

# output the sorted top K
items = list(zip(mmr_d.keys(), mmr_d.values()))
sitems = sorted(items, key=lambda x: x[0], reverse=True)  # x[0] is mmr
print('top K mmr')
for each in sitems:
  tmp = '{}-{} {}'.format(each[1][0], each[1][1], each[1][2])
  print('{}: {}'.format(each[0], tmp))
