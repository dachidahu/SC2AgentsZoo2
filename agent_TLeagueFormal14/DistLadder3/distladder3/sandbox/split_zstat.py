import os
from os import path
from shutil import copyfile

zstat_dir = '/Users/pengsun/code/DistLadder3/distladder3/sandbox/tmp_rp1522-mmr-ge6000-winner-selected-8'

hidden_files = []
for f in os.listdir(zstat_dir):
  if f == '.' or f == '..':
    continue
  if not f.startswith('.'):
    continue
  hidden_files.append(f)

for f in os.listdir(zstat_dir):
  if not path.isfile(path.join(zstat_dir, f)):
    continue
  if f in hidden_files:
    continue
  dst_zstat_dir = zstat_dir + '-{}'.format(f[0:5])
  os.makedirs(dst_zstat_dir, exist_ok=True)
  # copy zstat
  copyfile(path.join(zstat_dir, f), path.join(dst_zstat_dir, f))
  # copy any hidden files
  for hf in hidden_files:
    copyfile(path.join(zstat_dir, hf), path.join(dst_zstat_dir, hf))

