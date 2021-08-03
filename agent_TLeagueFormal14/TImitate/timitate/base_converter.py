from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from gym import spaces


class BaseConverter(object):
  @property
  def space(self):
    return None

  @property
  def tensor_names(self):
    return []

  def reset(self, **kwargs):
    pass

  def _check_space(self, tensor):
    space = self.space
    if isinstance(space, spaces.Tuple):
      assert len(tensor) == len(self.tensor_names)
      for item, sp in zip(tensor, space):
        assert len(item.shape) == len(sp.shape)
        assert tuple(item.shape) == tuple(sp.shape)
    elif isinstance(space, spaces.Dict):
      assert len(tensor.keys()) == len(self.tensor_names)
      assert len(space.spaces.keys()) == len(self.tensor_names)
      for key, sp in space.spaces.items():
        assert tuple(tensor[key].shape) == tuple(sp.shape)
    else:
      assert len(self.tensor_names) == 1
      assert tuple(tensor.shape) == tuple(space.shape)
    return tensor
