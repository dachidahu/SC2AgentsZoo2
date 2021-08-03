#!/bin/bash
# process glibc for sc2 game cores. Replace the original executable with an sh that specifies the glibc-build folder explicitly.
# Example:
# bash proc_glibc.sh 4.8.2 4.8.6 4.9.0

work_dir=$(pwd)
for v in "$@"
do
    echo "processing $v"
    cd $work_dir || exit

    # do the trick
    cd SC2/$v/Versions/Base* || exit
    pwd
    if [  -f SC2_x64.original ];
    then
        echo "SC2_x64.original exists, skipped";
        continue
    fi
    cp ${work_dir}/SC2_x64_trick_bak .
    mv SC2_x64 SC2_x64.original
    mv SC2_x64_trick_bak SC2_x64
    chmod 751 SC2_x64

    # undo the trick
    #mv SC2_x64.original SC2_x64
done