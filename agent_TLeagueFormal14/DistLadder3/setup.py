from setuptools import setup

setup(
    name='DistLadder3',
    version='0.1',
    description='Distributed Ladder for SC2, Version 3',
    keywords='Ladder, SC2',
    packages=[
        'distladder3',
    ],

    install_requires=[
        'pyzmq',
        'absl-py',
        'numpy',
        #'matplotlib==3.0',
        'matplotlib==3.1.1',
        'mpld3',
        'Werkzeug==0.15.6',
        'flask',
        'Flask-AutoIndex',
        'Flask-RESTful'
    ],
)
