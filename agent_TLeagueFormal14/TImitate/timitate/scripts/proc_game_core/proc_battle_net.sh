#!/bin/bash
# process sc2 Battle.net, build a unique softlink for all the game core versions.
# Example:
# bash proc_sc2.sh 4.8.2 4.8.6 4.9.0

work_dir=$(pwd)
echo "working dir: $work_dir"
for v in "$@"
do
    echo "processing $v"
    cd SC2/$v
    rm -r Battle.net/Cache
    ln -s ../../Battle.net/Cache Battle.net/Cache
    cd $work_dir
done