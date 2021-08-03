from timitate.lib6.zstat_utils import STAT_ABILITY_CANDIDATES
from pysc2.lib import ABILITY_ID
from os import path
import logging
import numpy as np
from timitate.utils.rep_db import RepDBFS

from pysc2.lib.typeenums import UNIT_TYPEID, ABILITY_ID
from timitate.lib6.zstat_utils import BUILD_ORDER_OBJECT_CANDIDATES,\
  RESEARCH_ABILITY_CANDIDATES, BUILD_ORDER_BUILDING_OBJECT_CANDIDATES

def read_bo(bo, is_bt=False):
  bo_object = (BUILD_ORDER_BUILDING_OBJECT_CANDIDATES
               if is_bt else BUILD_ORDER_OBJECT_CANDIDATES)
  def name(i):
    if i < len(bo_object):
      return(UNIT_TYPEID(bo_object[i]).name.split('ZERG_')[-1])
    else:
      return(ABILITY_ID(RESEARCH_ABILITY_CANDIDATES[i-len(bo_object)]).name.split('RESEARCH_')[-1])
  return [name(i) for i in np.nonzero(bo)[1]]

def read_boc(boc):
  real_coors = []
  for coor in boc:
    coor_x = coor[:9]
    coor_y = coor[-9:]
    s = ''
    for a in coor_x:
      s += str(int(a))
    x = int(s, 2) / 2.0
    s = ''
    for a in coor_y:
      s += str(int(a))
    y = int(s, 2) / 2.0
    real_coors.append((x, y))
  return real_coors

class ZStatAnalyzer:
  def __init__(self, zstat_data_src=''):
    self._zstat_db = self._create_db(zstat_data_src, name='zstat')
    self._zstat_db_keys = self._zstat_db.keys()

  def _create_db(self, data_src, name='mydata'):
    if data_src is None or not path.exists(data_src):
      logging.warning('path {} not exists, {} db disabled!'.format(
        data_src, name))
      return None
    return RepDBFS(data_src)

  def get_from_key(self, key):
    return self._zstat_db.get(key)


def print_zstat_info(zstat_maker):
  n = 1
  for k in zstat_maker._zstat_db_keys:
    try:
      zstat = zstat_maker.get_from_key(k)
      print('n: {}, key: {}'.format(n, k))
      print('------------------------------------')
      print(f'BO: {read_bo(zstat[1])}')
      print(f'BOC: {read_boc(zstat[2])}')
      print(f'BOBT: {read_bo(zstat[3], True)}')
      n += 1
    except:
      continue
    for cand, v in zip(STAT_ABILITY_CANDIDATES, zstat[0]):
      print('{}: {}'.format(ABILITY_ID(cand), v))
      # print('{}'.format(v))

def filter_dazhao_func(bo, boc, bobt, bobtc):
  return (bobt[0] == 'SPAWNINGPOOL' and bobt[1] == 'SPINECRAWLER') and (
          ((bobtc[0][0]-bobtc[1][0])**2.0+(bobtc[0][1]-bobtc[1][1])**2.0)**0.5 > 50)

def filter_roach_func(bo, boc, bobt, bobtc):
  return ('ROACH' in bo)

def filter_pure_roach_func(bo, boc, bobt, bobtc):
  return ('ROACH' in bo and 'ZERGLING' not in bo)

def filter_hydralisk_func(bo, boc, bobt, bobtc):
  return ('HYDRALISK' in bo)

def filter_mutalisk_func(bo, boc, bobt, bobtc):
  return ('MUTALISK' in bo)

def filter_swarmhost_func(bo, boc, bobt, bobtc):
  return ('SWARMHOSTMP' in bo)

def filter_infestor_func(bo, boc, bobt, bobtc):
  return ('INFESTOR' in bo)

def filter_nydus_func(bo, boc, bobt, bobtc):
  return (('NYDUSCANAL' in bo + bobt) or ('NYDUSNETWORK' in bo + bobt))

def filter_broodlord_func(bo, boc, bobt, bobtc):
  return ('BROODLORD' in bo or 'GREATERSPIRE' in bobt)

def filter_ultralisk_func(bo, boc, bobt, bobtc):
  return ('ULTRALISK' in bo or 'ULTRALISKCAVERN' in bobt)

def filter_corner_base_func(bo, boc, bobt, bobtc):
  for b, bc in zip(bobt, bobtc):
    if b == 'HATCHERY':
      if (bc[0] < 30 and bc[1] < 30) or (bc[0] > 120 and bc[1] > 120):
        return True
      return False
  return False

def filter_one_base_spire(bo, boc, bobt, bobtc):
  cur_b_list = []
  for b in bobt:
    cur_b_list.append(b)
    if b == 'SPIRE' and 'HATCHERY' not in cur_b_list:
      return True
  return False

def print_func(bo, boc, bobt, bobtc, n, k, type):
  print('n: {}, key: {}, type: {}'.format(n, k, type))
  print('------------------------------------')
  print(f'BO: {bo}')
  print(f'BOC: {boc}')
  print(f'BOBT: {bobt}')
  print(f'BOBTC: {bobtc}')

def filter_zstat(zstat_maker):
  n = 1
  for k in zstat_maker._zstat_db_keys:
    try:
      zstat = zstat_maker.get_from_key(k)
      bo = read_bo(zstat[1])
      boc = read_boc(zstat[2])
      bobt = read_bo(zstat[3], is_bt=True)
      bobtc = read_boc(zstat[4])
      if filter_dazhao_func(bo, boc, bobt, bobtc):
        print_func(bo, boc, bobt, bobtc, n, k, 'dazhao')
      if filter_roach_func(bo, boc, bobt, bobtc):
        print_func(bo, boc, bobt, bobtc, n, k, 'roach')
      if filter_pure_roach_func(bo, boc, bobt, bobtc):
        print_func(bo, boc, bobt, bobtc, n, k, 'pure_roach')
      if filter_hydralisk_func(bo, boc, bobt, bobtc):
        print_func(bo, boc, bobt, bobtc, n, k, 'hydralisk')
      if filter_mutalisk_func(bo, boc, bobt, bobtc):
        print_func(bo, boc, bobt, bobtc, n, k, 'mutalisk')
      if filter_infestor_func(bo, boc, bobt, bobtc):
        print_func(bo, boc, bobt, bobtc, n, k, 'infestor')
      if filter_swarmhost_func(bo, boc, bobt, bobtc):
        print_func(bo, boc, bobt, bobtc, n, k, 'swarmhost')
      if filter_nydus_func(bo, boc, bobt, bobtc):
        print_func(bo, boc, bobt, bobtc, n, k, 'nydus')
      if filter_broodlord_func(bo, boc, bobt, bobtc):
        print_func(bo, boc, bobt, bobtc, n, k, 'broodlord')
      if filter_ultralisk_func(bo, boc, bobt, bobtc):
        print_func(bo, boc, bobt, bobtc, n, k, 'ultralisk')
      if filter_corner_base_func(bo, boc, bobt, bobtc):
        print_func(bo, boc, bobt, bobtc, n, k, 'corner_base')
      if filter_one_base_spire(bo, boc, bobt, bobtc):
        print_func(bo, boc, bobt, bobtc, n, k, 'one_base_spire')
      n += 1
    except:
      continue


if __name__ == '__main__':
  # /root/replay_ds/rp1706-mv7-zstat
  # python -u -m timitate.sandbox.zstat_load
  zstat_maker = ZStatAnalyzer(zstat_data_src='/Users/pengsun/code/tmp/replay_ds/rp1706-mv7-mmr6200-victory-selected-174')
  print_zstat_info(zstat_maker)
  #filter_zstat(zstat_maker)
