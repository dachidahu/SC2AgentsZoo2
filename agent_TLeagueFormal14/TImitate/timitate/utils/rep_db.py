"""Z Statistics Data Base"""
import os
from os import path
import pickle
import random
import logging
from copy import deepcopy

from timitate.utils.utils import map_name_transform


def rep_info_to_unique_key(replay_name, player_id):
  """ convert replay info (replay_name, player_id) to a unique key"""
  return '{}-{}'.format(replay_name, player_id)


def unique_key_to_rep_info(key):
  replay_name, player_id = key.split('-')
  return replay_name, player_id


class RepDBFS(object):
  """Replay related Data Base implemented with File System.

  Can be used to store pre-processed ZStat, MMR, etc."""
  def __init__(self, data_src_path):
    assert path.isdir(data_src_path), 'data_src_path must be a directory!'
    os.makedirs(data_src_path, exist_ok=True)
    self._data_src_path = data_src_path
    self._all_keys = None  # lazy evaluation

  def put(self, key, value):
    """insert key, value"""
    with open(path.join(self._data_src_path, key), 'wb') as f:
      pickle.dump(value, f)
    self._all_keys = None  # set dirty the all_keys
    pass

  def get(self, key):
    """get value by key"""
    fpath = path.join(self._data_src_path, key)
    if not path.exists(fpath):
      return None
    with open(fpath, 'rb') as f:
      v = pickle.load(f)
      return v

  def keys(self):
    """get all keys in a list.

    It guarantees the order of the returned list across multiple calls when
    there is no new key inserted."""
    if self._all_keys is None:
      # get the keys. excluding those hidden files (starting with dot)
      self._all_keys = [f for f in os.listdir(self._data_src_path)
                        if path.isfile(path.join(self._data_src_path, f)) and
                        not f.startswith('.')]
    return deepcopy(self._all_keys)

  def sample(self, keys=None):
    """randomly sample a value from given keys. If keys==None, from all keys"""
    logging.warning(
      'RepDBFS.sample() is deprecated! Instead, first get the keys you want, '
      'do the sampling to get the key, and finally do the RepDBFS.get(key) '
    )
    keys = keys if keys is not None else self.keys()
    k = random.choice(keys)
    v = self.get(k)
    return v

  def __str__(self):
    return 'RepDBFS {}'.format(self._data_src_path)


class RepDBFSKeysIndex(object):
  """ Replay related keys index (pre-saved keys filtered by specific queries),
  an auxiliary class for RepDBFS"""
  def __init__(self, index_path):
    self._index_path = index_path

  def get_keys_by_map_name_start_pos(self, map_name, start_pos):
    """ get Replay DB keys filtered by map_name & start_pos """
    ifn = _map_name_start_pos_to_index_fn(map_name, start_pos)
    logging.info('get by keys_index: {}'.format(ifn))
    with open(path.join(self._index_path, ifn), 'rt') as f:
      return list([line.strip() for line in f.readlines()])

  def put_keys_by_map_name_start_pos(self, the_keys, map_name, start_pos):
    """ put Replay DB keys filtered by map_name & start_pos """
    ifn = _map_name_start_pos_to_index_fn(map_name, start_pos)
    logging.info('put by keys_index: {}'.format(ifn))
    with open(path.join(self._index_path, ifn), 'wt') as f:
      f.write('\n'.join(the_keys))

  def get_keys_by_presort_order(self, presort_order_name):
    fn = '.presort_order-{:s}'.format(presort_order_name)
    logging.info('get by presort_order: {}'.format(fn))
    with open(path.join(self._index_path, fn), 'rt') as f:
      return list([line.strip() for line in f.readlines()])

  def get_keys_by_category(self, category_name):
    fn = '.category-{:s}'.format(category_name)
    logging.info('get by category_name: {}'.format(fn))
    with open(path.join(self._index_path, fn), 'rt') as f:
      return list([line.strip() for line in f.readlines()])


def _map_name_start_pos_to_index_fn(map_name, start_pos):
  return '.keys_index-{:s}-{:.1f}-{:.1f}'.format(
    map_name_transform(map_name), start_pos[0], start_pos[1])


def test_repdbfs():
  data_src_path = '/Users/pengsun/code/sc2_rl/TImitate/timitate/bin4/tmp_zstat'
  replay_name = '3'
  player_id = 2

  db = RepDBFS(data_src_path)
  key = rep_info_to_unique_key(replay_name, player_id)
  val = db.get(key)
  print(type(val))
  print(val)

  keys = db.keys()
  print(keys)

  sv = db.sample()
  print(sv)


def test_repdbfskeysindex():
  index_path = '/Users/pengsun/code/sc2_rl/TImitate/timitate/bin4/tmp_zstat'
  kj_map_name = 'Kairos Junction LE'
  kj_start_pos_1 = (18, 73)
  kj_start_pos_2 = (121, 117)
  keys_1 = [  # replay_name-player_id
    '3-1',
    '4-2'
  ]
  keys_2 = [
    '4-1'
  ]
  # put
  rep_ki = RepDBFSKeysIndex(index_path)
  rep_ki.put_keys_by_map_name_start_pos(keys_1, kj_map_name, kj_start_pos_1)
  rep_ki.put_keys_by_map_name_start_pos(keys_2, kj_map_name, kj_start_pos_2)

  # get
  g_keys_1 = rep_ki.get_keys_by_map_name_start_pos(kj_map_name, kj_start_pos_1)
  g_keys_2 = rep_ki.get_keys_by_map_name_start_pos(kj_map_name, kj_start_pos_2)
  print(g_keys_1)
  print(g_keys_2)


def test_repdbfs_presort_order():
  index_path = '/Users/pengsun/code/sc2_rl/TImitate/timitate/bin4/tmp_zstat'
  presort_order_name = 'type_a'
  rep_ki = RepDBFSKeysIndex(index_path)

  # get
  keys = rep_ki.get_keys_by_presort_order(presort_order_name)
  print(keys)


def test_repdbfs_category():
  index_path = '/Users/pengsun/code/sc2_rl/TImitate/timitate/bin4/tmp_zstat'
  category_name = 'PureRoach'
  rep_ki = RepDBFSKeysIndex(index_path)

  # get
  keys = rep_ki.get_keys_by_category(category_name)
  print(keys)


if __name__ == '__main__':
  test_repdbfs()
  test_repdbfskeysindex()
  test_repdbfs_presort_order()
  test_repdbfs_category()