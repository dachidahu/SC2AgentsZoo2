#!/bin/bash
# undo the processing glibc for sc2 game cores. Replace the original executable with an sh that specifies the glibc-build folder explicitly.
# Example:
# bash proc_glibc_undo.sh 4.8.2 4.8.6 4.9.0

work_dir=$(pwd)
for v in "$@"
do
    echo "processing $v"
    cd $work_dir || exit

    # do the trick
    cd SC2/$v/Versions/Base* || exit
    pwd
    if [ ! -f SC2_x64.original ];
    then
        echo "SC2_x64.original not exists, skipped";
        continue
    fi

    # undo the trick
    mv SC2_x64.original SC2_x64
done