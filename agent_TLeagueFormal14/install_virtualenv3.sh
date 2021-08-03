#!/bin/bash
## install virtual env and install dependencies, using DistLadder3!

virtualenv -p python3 myenv
source myenv/bin/activate

##
pip install tensorflow==1.15.0
##
cd pysc2 && pip install -e . && cd ..
cd Arena && pip install -e . && cd ..
cd TLeague && pip install -e . && cd ..
cd TPolicies && pip install -e . && cd ..
cd TImitate && pip install -e . && cd ..
cd DistLadder3 && pip install -e . && cd ..

deactivate

echo "done installing agent_TLeagueFormal14 virtualenv, using DistLadder3"