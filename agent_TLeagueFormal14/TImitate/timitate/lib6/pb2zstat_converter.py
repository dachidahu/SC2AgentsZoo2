"""PB to Z statistics. See AlphaStar Nature paper."""
from gym.spaces import Box
from gym.spaces import Tuple
import numpy as np

from timitate.base_converter import BaseConverter
from timitate.lib6.zstat_utils import STAT_ABILITY_CANDIDATES, \
  STAT_OBJECT_CANDIDATES, EFFECT_ABILITY_CANDIDATES, \
  RESEARCH_ABILITY_CANDIDATES, BUILD_ORDER_BUILDING_OBJECT_CANDIDATES, \
  STAT_BO_ORDER_CANDIDATES, STAT_BO_OBJECT_CANDIDATES
from timitate.lib6.zstat_utils import BUILD_ORDER_ABILITY_CANDIDATES, \
  BUILD_ORDER_OBJECT_CANDIDATES, UNIT_TYPEID
from timitate.utils.utils import find_action_pos, find_unit_pos


def get_upgrading_tech_act_ids(pb_obs):
  upgrading_tech_act_ids = []
  executors = []
  for unit in pb_obs.observation.raw_data.units:
    if unit.alliance == 1:
      for order in unit.orders:
        if order.ability_id in RESEARCH_ABILITY_CANDIDATES:
          upgrading_tech_act_ids.append(order.ability_id)
          executors.append(unit)
  return upgrading_tech_act_ids, executors


class PB2UnitCountConverter(BaseConverter):
  def __init__(self):
    assert isinstance(STAT_ABILITY_CANDIDATES, list)  # list is strictly ordered!
    self._dcount = {each: 0 for each in STAT_ABILITY_CANDIDATES}
    pass

  def reset(self):
    self._dcount = {each: 0 for each in STAT_ABILITY_CANDIDATES}

  def convert(self, pb_obs):
    actions = pb_obs.actions
    for a in actions:
      ab_id = a.action_raw.unit_command.ability_id
      if ab_id in self._dcount:
        self._dcount[ab_id] += 1
    # now create and return current data
    # NOTE: must be strictly in the same order of STAT_CANDIDATES!
    sorted_counts = [self._dcount[each] for each in STAT_ABILITY_CANDIDATES]
    return np.array(sorted_counts, dtype=np.float32)

  @property
  def tensor_names(self):
    return ['Z_UNIT_COUNT']

  @property
  def space(self):
    sp = (len(self._dcount),)
    return Box(shape=sp, low=0, high=0, dtype=np.float32)


class PB2UnitCountPostActConverter(BaseConverter):
  def __init__(self):
    assert isinstance(STAT_OBJECT_CANDIDATES, list)  # list is strictly ordered!
    assert isinstance(EFFECT_ABILITY_CANDIDATES, list)  # no effect obj in old pysc2
    assert isinstance(RESEARCH_ABILITY_CANDIDATES, list)
    self._obj_count = {each: 0 for each in STAT_OBJECT_CANDIDATES}
    self._eff_count = {each: 0 for each in EFFECT_ABILITY_CANDIDATES}
    self._upg_count = {each: 0 for each in RESEARCH_ABILITY_CANDIDATES}
    self._historic_tag_set = {}

  def reset(self):
    self._obj_count = {each: 0 for each in STAT_OBJECT_CANDIDATES}
    self._eff_count = {each: 0 for each in EFFECT_ABILITY_CANDIDATES}
    self._upg_count = {each: 0 for each in RESEARCH_ABILITY_CANDIDATES}
    self._historic_tag_set = {}

  def convert(self, pb_obs):
    actions = pb_obs.actions  # for effects
    units = pb_obs.observation.raw_data.units  # for objects
    # upgraded_techs = pb_obs.observation.raw_data.player.upgrade_ids
    upgrading_tech_act_ids, _ = get_upgrading_tech_act_ids(pb_obs)  # for upgrades
    for u in units:
      if u.alliance == 1 and u.unit_type in STAT_OBJECT_CANDIDATES and \
        (u.tag not in self._historic_tag_set or
           u.unit_type not in self._historic_tag_set[u.tag]):
        # Note that burrowed_xxx or unrooted_xxx are not included in
        # STAT_OBJECT_CANDIDATES, so do not worry about tag problem.
        # Found a valid object_id
        self._obj_count[u.unit_type] += 0.5 \
          if u.unit_type == UNIT_TYPEID.ZERG_ZERGLING.value else 1
        # update _historic_tag_set
        if u.tag not in self._historic_tag_set:
          self._historic_tag_set[u.tag] = [u.unit_type]
        else:
          self._historic_tag_set[u.tag] += [u.unit_type]
    for a in actions:
      ab_id = a.action_raw.unit_command.ability_id
      if ab_id in self._eff_count:
        self._eff_count[ab_id] += 1
    for tec_act_id in upgrading_tech_act_ids:
      if tec_act_id in RESEARCH_ABILITY_CANDIDATES:
        if self._upg_count[tec_act_id] == 0:
          self._upg_count[tec_act_id] = 1
    # now create and return current data
    # NOTE: must be strictly in the same order of
    # STAT_OBJECT_CANDIDATES + EFFECT_ABILITY_CANDIDATES + RESEARCH_OBJECT_CANDIDATES!
    sorted_counts = [self._obj_count[each] for each in STAT_OBJECT_CANDIDATES]
    sorted_counts += [self._eff_count[each] for each in EFFECT_ABILITY_CANDIDATES]
    sorted_counts += [self._upg_count[each] for each in RESEARCH_ABILITY_CANDIDATES]
    return np.array(sorted_counts, dtype=np.float32)

  @property
  def tensor_names(self):
    return ['Z_UNIT_COUNT']

  @property
  def space(self):
    sp = (len(self._obj_count)+len(self._eff_count)+len(self._upg_count),)
    return Box(shape=sp, low=0, high=0, dtype=np.float32)


class PB2BuildOrderWithCoordConverter(object):
  """Build Order with the unit coordinate (x, y)"""
  VOCAB_SIZE = len(BUILD_ORDER_ABILITY_CANDIDATES)
  COORD_ENCODING_LEN = 9  # binary digit. lxhan's choice

  def __init__(self, max_bo_count=20, use_coord_encoding=True):
    assert isinstance(BUILD_ORDER_ABILITY_CANDIDATES, list)
    self._max_bo_count = max_bo_count
    self._use_coord_encoding = use_coord_encoding

    self._last_pb_obs = None
    self._valid_bo_count = 0
    self._bo = np.zeros(shape=self.space.spaces[0].shape, dtype=np.float32)
    self._boc = np.zeros(shape=self.space.spaces[1].shape, dtype=np.float32)
    pass

  def reset(self):
    self._last_pb_obs = None
    self._valid_bo_count = 0
    self._bo = np.zeros(shape=self.space.spaces[0].shape, dtype=np.float32)
    self._boc = np.zeros(shape=self.space.spaces[1].shape, dtype=np.float32)

  def _encode_pos(self, x, y):
    if self._use_coord_encoding:
      # lxhan's choice: binary encoding and 2x resolution
      bxy = ([int(i) for i in '{0:09b}'.format(int(x * 2))] +
             [int(i) for i in '{0:09b}'.format(int(y * 2))])
      return bxy
    else:
      return [x, y]

  def convert(self, pb_obs):
    actions = pb_obs.actions
    if self._last_pb_obs is None:
      self._last_pb_obs = pb_obs
      return self._bo, self._boc
    last_units = self._last_pb_obs.observation.raw_data.units
    for a in actions:
      if self._valid_bo_count >= self._max_bo_count:
        return self._bo, self._boc
      ab_id = a.action_raw.unit_command.ability_id
      if ab_id in BUILD_ORDER_ABILITY_CANDIDATES:  # found a valid ability_id
        # build order: set to 1.0 the correct entry
        idx = BUILD_ORDER_ABILITY_CANDIDATES.index(ab_id)
        self._bo[self._valid_bo_count, idx] = 1.0
        # build order coordinate: the encoded coord
        ax, ay = find_action_pos(a, last_units)
        self._boc[self._valid_bo_count] = self._encode_pos(ax, ay)
        # update the count
        self._valid_bo_count += 1
    # before leaving step, update the last_pb_obs
    self._last_pb_obs = pb_obs
    return self._bo, self._boc

  @property
  def tensor_names(self):
    return ['Z_BUILD_ORDER', 'Z_BUILD_ORDER_COORD']

  @property
  def space(self):
    s0 = (self._max_bo_count, self.VOCAB_SIZE)
    coord_len = (1 if not self._use_coord_encoding
                 else self.COORD_ENCODING_LEN)
    s1 = (self._max_bo_count, 2 * coord_len)
    return Tuple([
      Box(shape=s0, low=0, high=1, dtype=np.float32),
      Box(shape=s1, low=0, high=1, dtype=np.float32)
    ])


class PB2BuildOrderWithCoordPostActConverter(PB2BuildOrderWithCoordConverter):
  """Build Order with the unit coordinate (x, y)"""
  MY_BO_OBJ_CANDIDATES = BUILD_ORDER_OBJECT_CANDIDATES
  VOCAB_SIZE = len(MY_BO_OBJ_CANDIDATES)+len(RESEARCH_ABILITY_CANDIDATES)
  COORD_ENCODING_LEN = 9  # binary digit. lxhan's choice

  def __init__(self, max_bo_count=100, use_coord_encoding=True):
    super(PB2BuildOrderWithCoordPostActConverter, self).__init__(max_bo_count, use_coord_encoding)
    assert isinstance(self.MY_BO_OBJ_CANDIDATES, list)
    self._historic_tag_set = {}
    self._historic_upg_set = set()

  def reset(self):
    super(PB2BuildOrderWithCoordPostActConverter, self).reset()
    self._historic_tag_set = {}
    self._historic_upg_set = set()

  def convert(self, pb_obs):
    if self._last_pb_obs is None:
      self._last_pb_obs = pb_obs
      return self._bo, self._boc

    last_units = self._last_pb_obs.observation.raw_data.units
    units = pb_obs.observation.raw_data.units
    # update _historic_tag_set
    for u in last_units:
      if u.alliance == 1 and u.unit_type in self.MY_BO_OBJ_CANDIDATES:
        if u.tag not in self._historic_tag_set:
          self._historic_tag_set[u.tag] = [u.unit_type]
        elif u.unit_type not in self._historic_tag_set[u.tag]:
          self._historic_tag_set[u.tag] += [u.unit_type]
        else:
          pass
    # count units
    new_zergling_cnt = 0
    for u in units:
      if self._valid_bo_count >= self._max_bo_count:
        return self._bo, self._boc
      if u.alliance == 1 and u.unit_type in self.MY_BO_OBJ_CANDIDATES and \
        (u.tag not in self._historic_tag_set or
             u.unit_type not in self._historic_tag_set[u.tag]):
        # found a valid object_id
        # build order: set to 1.0 the correct entry
        if u.unit_type == UNIT_TYPEID.ZERG_ZERGLING.value:
          new_zergling_cnt += 1
          if new_zergling_cnt % 2 != 0:
            continue
        idx = self.MY_BO_OBJ_CANDIDATES.index(u.unit_type)
        self._bo[self._valid_bo_count, idx] = 1.0
        # build order coordinate: the encoded coord
        ux, uy = find_unit_pos(u)
        self._boc[self._valid_bo_count] = self._encode_pos(ux, uy)
        # update the count
        self._valid_bo_count += 1

    # count upgrades
    upgrading_tech_act_ids, executors = get_upgrading_tech_act_ids(pb_obs)
    last_upgrading_tech_act_ids, _ = get_upgrading_tech_act_ids(self._last_pb_obs)
    self._historic_upg_set.update(set(last_upgrading_tech_act_ids))
    for tec_act_id, e_u in zip(upgrading_tech_act_ids, executors):
      if self._valid_bo_count >= self._max_bo_count:
        return self._bo, self._boc
      if tec_act_id in RESEARCH_ABILITY_CANDIDATES and \
          tec_act_id not in self._historic_upg_set:
        # build order: set to 1.0 the correct entry
        idx = RESEARCH_ABILITY_CANDIDATES.index(tec_act_id)
        idx += len(self.MY_BO_OBJ_CANDIDATES)
        self._bo[self._valid_bo_count, idx] = 1.0
        # build order coordinate from the executors
        ux, uy = find_unit_pos(e_u)
        self._boc[self._valid_bo_count] = self._encode_pos(ux, uy)
        # update the count
        self._valid_bo_count += 1

    # before leaving step, update the last_pb_obs
    self._last_pb_obs = pb_obs
    return self._bo, self._boc


class PB2BOBTWithCoordPostActConverter(PB2BuildOrderWithCoordPostActConverter):
  """Build Order with the unit coordinate (x, y) for only Buildings and Techs"""
  MY_BO_OBJ_CANDIDATES = BUILD_ORDER_BUILDING_OBJECT_CANDIDATES
  VOCAB_SIZE = len(MY_BO_OBJ_CANDIDATES)+len(RESEARCH_ABILITY_CANDIDATES)

  def __init__(self, max_bo_count=100, use_coord_encoding=True):
    super(PB2BOBTWithCoordPostActConverter, self).__init__(max_bo_count, use_coord_encoding)

  def reset(self):
    super(PB2BOBTWithCoordPostActConverter, self).reset()

  @property
  def tensor_names(self):
    return ['Z_BUILD_ORDER_BT', 'Z_BUILD_ORDER_COORD_BT']


class PB2BuildOrderWithCoordPostActConverterV2(PB2BuildOrderWithCoordConverter):
  """Build Order with the unit coordinate (x, y)"""
  MY_BO_OBJ_CANDIDATES = BUILD_ORDER_OBJECT_CANDIDATES
  VOCAB_SIZE = len(MY_BO_OBJ_CANDIDATES) + len(RESEARCH_ABILITY_CANDIDATES)
  COORD_ENCODING_LEN = 9  # binary digit. lxhan's choice

  def __init__(self, max_bo_count=100, use_coord_encoding=True):
    super(PB2BuildOrderWithCoordPostActConverterV2, self).__init__(max_bo_count, use_coord_encoding)
    self._historic_tag2order_dict = {}
    self._ability2unit = dict(zip(BUILD_ORDER_ABILITY_CANDIDATES, BUILD_ORDER_OBJECT_CANDIDATES))
    self._bo_unit_candidates = [x for x in self.MY_BO_OBJ_CANDIDATES if x in STAT_BO_OBJECT_CANDIDATES]
    self._bo_order_condidates = [BUILD_ORDER_ABILITY_CANDIDATES[BUILD_ORDER_OBJECT_CANDIDATES.index(x)]
                                 for x in self.MY_BO_OBJ_CANDIDATES if x not in STAT_BO_OBJECT_CANDIDATES]
    assert all([x in STAT_BO_ORDER_CANDIDATES for x in self._bo_order_condidates])

  def reset(self):
    super(PB2BuildOrderWithCoordPostActConverterV2, self).reset()
    self._historic_tag2order_dict = {}

  @staticmethod
  def unit_order_with_progress(unit):
    if len(unit.orders) == 0:
      return None, 0
    else:
      return unit.orders[0].ability_id, unit.orders[0].progress

  def update_hist(self, units):
    new_units = []
    diff_old_units = []
    for u in units:
      if u.alliance == 1:
        current_order, progress = self.unit_order_with_progress(u)
        if u.tag not in self._historic_tag2order_dict:
          new_units.append(u)
        elif current_order != self._historic_tag2order_dict[u.tag][0] \
            or (current_order is not None and progress < self._historic_tag2order_dict[u.tag][1]):
          diff_old_units.append(u)
        else:
          pass
        self._historic_tag2order_dict[u.tag] = (current_order, progress)
    return new_units, diff_old_units

  def convert(self, pb_obs):
    if self._valid_bo_count >= self._max_bo_count:
      return self._bo, self._boc
    units = pb_obs.observation.raw_data.units
    if self._last_pb_obs is None:
      self._last_pb_obs = pb_obs
      self.update_hist(units)
      return self._bo, self._boc
    new_units, diff_old_units = self.update_hist(units)

    # count new units
    for u in new_units:
      if u.unit_type in self._bo_unit_candidates:
        # found a valid object_id
        # build order: set to 1.0 the correct entry
        idx = self.MY_BO_OBJ_CANDIDATES.index(u.unit_type)
        self._bo[self._valid_bo_count, idx] = 1.0
        # build order coordinate: the encoded coord
        ux, uy = find_unit_pos(u)
        self._boc[self._valid_bo_count] = self._encode_pos(ux, uy)
        # update the count
        self._valid_bo_count += 1
        if self._valid_bo_count >= self._max_bo_count:
          return self._bo, self._boc

    # count new orders for old units (Morph, Research, etc.)
    for u in diff_old_units:
      order = self._historic_tag2order_dict[u.tag][0]
      if order in self._bo_order_condidates:
        idx = self.MY_BO_OBJ_CANDIDATES.index(self._ability2unit[order])
        self._bo[self._valid_bo_count, idx] = 1.0
      elif order in RESEARCH_ABILITY_CANDIDATES:
        idx = RESEARCH_ABILITY_CANDIDATES.index(order) + len(self.MY_BO_OBJ_CANDIDATES)
        self._bo[self._valid_bo_count, idx] = 1.0
      else:
        continue
      # build order coordinate: the encoded coord
      ux, uy = find_unit_pos(u)
      self._boc[self._valid_bo_count] = self._encode_pos(ux, uy)
      # update the count
      self._valid_bo_count += 1
      if self._valid_bo_count >= self._max_bo_count:
        return self._bo, self._boc

    # before leaving step, update the last_pb_obs
    self._last_pb_obs = pb_obs
    return self._bo, self._boc


class PB2BOBTWithCoordPostActConverterV2(PB2BuildOrderWithCoordPostActConverterV2):
  """Build Order with the unit coordinate (x, y) for only Buildings and Techs"""
  MY_BO_OBJ_CANDIDATES = BUILD_ORDER_BUILDING_OBJECT_CANDIDATES
  VOCAB_SIZE = len(MY_BO_OBJ_CANDIDATES)+len(RESEARCH_ABILITY_CANDIDATES)

  def __init__(self, max_bo_count=100, use_coord_encoding=True):
    super(PB2BOBTWithCoordPostActConverterV2, self).__init__(max_bo_count, use_coord_encoding)

  def reset(self):
    super(PB2BOBTWithCoordPostActConverterV2, self).reset()

  @property
  def tensor_names(self):
    return ['Z_BUILD_ORDER_BT', 'Z_BUILD_ORDER_COORD_BT']


class PB2ZStatConverterV2(BaseConverter):
  """PB to Z statistics Converter, V2. See AlphaStar Nature paper.

  It exposes:
  - Build Order
  - Build Order Unit Coordinates
  - Unit Count
  """

  def __init__(self, max_bo_count=20):
    self._uc_cvt = PB2UnitCountConverter()
    self._bo_cvt = PB2BuildOrderWithCoordConverter(max_bo_count)
    pass

  def reset(self):
    self._uc_cvt.reset()
    self._bo_cvt.reset()

  def convert(self, pb_obs):
    stat_z = [self._uc_cvt.convert(pb_obs)]  # length-1 list
    stat_z += self._bo_cvt.convert(pb_obs)  # length-2 list
    return stat_z

  @property
  def space(self):
    return Tuple([
      self._uc_cvt.space,
      self._bo_cvt.space.spaces[0],
      self._bo_cvt.space.spaces[1]
    ])

  @property
  def tensor_names(self):
    return self._uc_cvt.tensor_names + self._bo_cvt.tensor_names


class PB2ZStatConverterV3(PB2ZStatConverterV2):
  """PB to Z statistics Converter, V3, based on completed objects.
  See AlphaStar Nature paper.

  It exposes:
  - Build Order
  - Build Order Unit Coordinates
  - Unit Count
  """
  def __init__(self, max_bo_count=100):
    self._uc_cvt = PB2UnitCountPostActConverter()
    self._bo_cvt = PB2BuildOrderWithCoordPostActConverter(max_bo_count=max_bo_count)


class PB2ZStatConverterV4(PB2ZStatConverterV3):
  """PB to Z statistics Converter, V4

  It exposes:
  - Build Order
  - Build Order Unit Coordinates
  - Build Order for Building and Techs
  - Build Order for Building and Techs Coordinates
  - Unit Count
  """
  def __init__(self, max_bo_count=100, max_bobt_count=100):
    super(PB2ZStatConverterV4, self).__init__(max_bo_count)
    self._bobt_cvt = PB2BOBTWithCoordPostActConverter(max_bo_count=max_bobt_count)

  def reset(self):
    super(PB2ZStatConverterV4, self).reset()
    self._bobt_cvt.reset()

  def convert(self, pb_obs):
    stat_z = super(PB2ZStatConverterV4, self).convert(pb_obs)
    stat_z += self._bobt_cvt.convert(pb_obs)  # length-2 list
    return stat_z

  @property
  def space(self):
    return Tuple(super(PB2ZStatConverterV4, self).space.spaces +
                 [self._bobt_cvt.space.spaces[0],
                  self._bobt_cvt.space.spaces[1]])

  @property
  def tensor_names(self):
    return super(PB2ZStatConverterV4, self).tensor_names + \
           self._bobt_cvt.tensor_names


class PB2ZStatConverterV5(PB2ZStatConverterV2):
  """PB to Z statistics Converter, V5

  It exposes:
  - Build Order
  - Build Order Unit Coordinates
  - Build Order for Building and Techs
  - Build Order for Building and Techs Coordinates
  - Unit Count
  """
  def __init__(self, max_bo_count=100, max_bobt_count=100):
    self._uc_cvt = PB2UnitCountPostActConverter()
    self._bo_cvt = PB2BuildOrderWithCoordPostActConverterV2(max_bo_count=max_bo_count)
    self._bobt_cvt = PB2BOBTWithCoordPostActConverterV2(max_bo_count=max_bobt_count)

  def reset(self):
    super(PB2ZStatConverterV5, self).reset()
    self._bobt_cvt.reset()

  def convert(self, pb_obs):
    stat_z = super(PB2ZStatConverterV5, self).convert(pb_obs)
    stat_z += self._bobt_cvt.convert(pb_obs)  # length-2 list
    return stat_z

  @property
  def space(self):
    return Tuple(super(PB2ZStatConverterV5, self).space.spaces +
                 [self._bobt_cvt.space.spaces[0],
                  self._bobt_cvt.space.spaces[1]])

  @property
  def tensor_names(self):
    return super(PB2ZStatConverterV5, self).tensor_names + \
           self._bobt_cvt.tensor_names


class PB2ZStatConverter(BaseConverter):
  """PB to Z statistics Converter. See AlphaStar Nature paper.

  Be consistent with other PB2XXXConverter sc_interface."""
  def __init__(self):
    raise NotImplementedError('Deprecated. Use PB2ZStatConverterV2')
