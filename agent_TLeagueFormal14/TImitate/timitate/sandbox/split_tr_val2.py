"""assure the replay_name-* in the same tr/val set"""
from random import shuffle


filelist_path = 'rp1113-filter.list'
tr_ratio = 0.95


def make_rep_name_player_id_dict(items):
  d = {}
  for each in items:
    rn, pid = each.split('-')
    if rn in d:
      d[rn].append(pid)
    else:
      d[rn] = [pid]
  return d


with open(filelist_path, 'rt') as f:
  items = [line.strip() for line in f.readlines()]
rep_player = make_rep_name_player_id_dict(items)
rep_names = list(rep_player.keys())
shuffle(rep_names)
n_tr = int(len(rep_names) * tr_ratio)

# first tr_ratio: training
with open('{}.train'.format(filelist_path), 'wt') as f:
  for i in range(n_tr):
    rn = rep_names[i]
    player_ids = rep_player[rn]
    for pid in player_ids:
      f.write('{}-{}\n'.format(rn, pid))

# last (1-tr_ratio): validation
with open('{}.val'.format(filelist_path), 'wt') as f:
  for i in range(n_tr, len(rep_names)):
    rn = rep_names[i]
    player_ids = rep_player[rn]
    for pid in player_ids:
      f.write('{}-{}\n'.format(rn, pid))
