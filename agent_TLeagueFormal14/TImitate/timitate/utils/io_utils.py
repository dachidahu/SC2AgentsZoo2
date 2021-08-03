from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import zlib
import pickle

import tensorflow as tf
import numpy as np


def write_to_tfrecord(data, output_file, compress=True):
  with tf.python_io.TFRecordWriter(output_file) as record_writer:
    for frame in data:
      record_writer.write(compress_serialize(frame) if compress else frame)


def compress_serialize(data):
  data['feature'] = tuple(_np_dense_to_sparse(dense)
                          for dense in data['feature'])
  return zlib.compress(pickle.dumps(data))


def decompress_deserialize(data):
  data = pickle.loads(zlib.decompress(data))
  data['feature'] = tuple(_np_sparse_to_dense(sparse)
                          for sparse in data['feature'])
  return data


def _np_dense_to_sparse(tensor):
  for dim in tensor.shape: assert dim < 65535
  index = tuple(arr.astype(np.uint16) for arr in np.nonzero(tensor))
  value = tensor[index]
  return tensor.shape, index, value


def _np_sparse_to_dense(sparse):
  shape, index, value = sparse
  tensor = np.zeros(shape, dtype=value.dtype)
  tensor[index] = value
  return tensor
