from random import shuffle


filelist_path = 'rp1113-filter.list'
tr_ratio = 0.95


with open(filelist_path, 'rt') as f:
  items = [line.strip() for line in f.readlines()]

shuffle(items)
n_tr = int(len(items) * tr_ratio)

# first tr_ratio: training
with open('{}.train'.format(filelist_path), 'wt') as f:
  for i in range(n_tr):
    f.write('{}\n'.format(items[i]))

# last (1-tr_ratio): validation
with open('{}.val'.format(filelist_path), 'wt') as f:
  for i in range(n_tr, len(items)):
    f.write('{}\n'.format(items[i]))
