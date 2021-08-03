#!/bin/bash
# process sc2 game cores. Unzip them and re-arrange the folder layout.
# Example:
# bash proc_sc2.sh 4.8.2 4.8.6 4.9.0

for v in "$@"
do
    echo "processing $v"
    #unzip -P iagreetotheeula SC2.$v.zip -d SC2/$v

    # move both hidden and non-hiddent files
    mv SC2/$v/StarCraftII/* SC2/$v/ && mv SC2/$v/StarCraftII/.* SC2/$v/ && sleep 2 &&  echo 'moved'
    # remove the useless directory
    #rm -r SC2/$v/StarCraftII
done