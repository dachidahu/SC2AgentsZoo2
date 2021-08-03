from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from setuptools import setup


setup(
    name='TImitate',
    version='0.1',
    description='Tencent Imitation Learning Platform for StarCraft-II',
    keywords='Imitation Learning, SC2',
    packages=[
      'timitate',
    ],
    install_requires=[
      #'tensorflow==1.8',
      'gym==0.12.1',
      'numpy',
      'joblib',
      'pysc2',
      's2clientprotocol>=4.8.3',
      'pyzmq',
      'matplotlib==3.1.1',
      'scikit-image==0.15',
    ]
)
