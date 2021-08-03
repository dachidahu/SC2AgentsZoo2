import numpy as np
from timitate.utils.const import NEUTRAL_MINERAL_SET
from timitate.utils.const import NEUTRAL_VESPENE_SET


RESOURCE_DISTANCE = 7.0

def calculate_distances(x1, y1, x2, y2):
  x = abs(x1 - x2)
  y = abs(y1 - y2)
  distance = x ** 2 + y ** 2
  return distance ** 0.5

def unit_dist(unit1, unit2):
  return calculate_distances(unit1.pos.x, unit1.pos.y,
                             unit2.pos.x, unit2.pos.y)

def min_dist(unit, mtags, gtags, all_minerals, all_gas):
  # minimal dist from unit to mtags and gtags
  d = [unit_dist(unit, all_minerals[tag]) for tag in mtags] + \
      [unit_dist(unit, all_gas[tag]) for tag in gtags]
  return min(d)

def can_build_base(x, y, m_pos):
  for pos in m_pos:
    dx = abs(pos[0] - x)
    dy = abs(pos[1] - y)
    if dx < 6 and dy < 6 and (dx < 5 or dy < 5):
      return False
  return True

def find_ideal_base_position(m_pos, g_pos):
  mean_x, mean_y = m_pos.mean(0)
  max_x, max_y = g_pos.min(0) + 10
  min_x, min_y = g_pos.max(0) - 10
  d_min = None
  ideal_pos = []
  x = min_x
  while x <= max_x:
    y = min_y
    while y <= max_y:
      if can_build_base(x, y, m_pos):
        d = calculate_distances(x, y, mean_x, mean_y)
        if d_min is None or d < d_min:
          ideal_pos = [x, y]
          d_min = d
      y += 1
    x += 1
  return ideal_pos

def find_resource_area(mtags, gtags, all_minerals, all_gas):
  gtags_in_area = []
  tag = mtags.pop()
  mtags_in_area = [tag]
  while mtags:  # not empty
    d_min = None
    mtag = None
    for tag in mtags:
      d = min_dist(all_minerals[tag], mtags_in_area,
                   gtags_in_area, all_minerals, all_gas)
      if d_min is None or d < d_min:
        d_min = d
        mtag = tag
    if d_min > RESOURCE_DISTANCE:
      break
    mtags_in_area.append(mtag)
    mtags.discard(mtag)

  while gtags:  # not empty
    d_min = None
    gtag = None
    for tag in gtags:
      d = min_dist(all_gas[tag], mtags_in_area,
                   gtags_in_area, all_minerals, all_gas)
      if d_min is None or d < d_min:
        d_min = d
        gtag = tag
    if d_min > RESOURCE_DISTANCE:
      break
    gtags_in_area.append(gtag)
    gtags.discard(gtag)

  m_pos = [[all_minerals[tag].pos.x,
            all_minerals[tag].pos.y] for tag in mtags_in_area]
  g_pos = [[all_gas[tag].pos.x,
            all_gas[tag].pos.y] for tag in gtags_in_area]
  ideal_pos = find_ideal_base_position(np.array(m_pos),
                                       np.array(g_pos))
  return ideal_pos

def find_all_base_position(units):
  all_minerals = dict([(u.tag, u) for u in units
                       if u.unit_type in NEUTRAL_MINERAL_SET])
  all_vespenes = dict([(u.tag, u) for u in units
                       if u.unit_type in NEUTRAL_VESPENE_SET])
  mtags = set(all_minerals.keys())
  gtags = set(all_vespenes.keys())
  all_pos = []
  while len(mtags) > 0 and len(gtags) > 0:
    pos = find_resource_area(mtags, gtags, all_minerals, all_vespenes)
    all_pos.append(pos)
  return all_pos

