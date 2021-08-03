# make 482x_49x_mv7.filter.shuffle.KairosJunction.Victor.Misc.csv
cp \
  482x_49x_mv7.filter.shuffle.mmr6200.KairosJunction.Victor.csv \
  482x_49x_mv7.filter.shuffle.KairosJunction.Victor.Misc.csv

python3 comb_csv_v2.py \
  -a 482x_49x_mv7.filter.shuffle.KairosJunction.Victor.Misc.csv \
  -b 482x_49x_mv7.filter.shuffle.mmr5500.KairosJunction.Victor.Dazhao.csv \
  -o 482x_49x_mv7.filter.shuffle.KairosJunction.Victor.Misc.csv

python3 comb_csv_v2.py \
  -a 482x_49x_mv7.filter.shuffle.KairosJunction.Victor.Misc.csv \
  -b 482x_49x_mv7.filter.shuffle.mmr5500.KairosJunction.Victor.PureRoach.csv \
  -o 482x_49x_mv7.filter.shuffle.KairosJunction.Victor.Misc.csv

python3 comb_csv_v2.py \
  -a 482x_49x_mv7.filter.shuffle.KairosJunction.Victor.Misc.csv \
  -b 482x_49x_mv7.filter.shuffle.mmr5500.KairosJunction.Victor.Hydralisk.csv \
  -o 482x_49x_mv7.filter.shuffle.KairosJunction.Victor.Misc.csv

python3 comb_csv_v2.py \
  -a 482x_49x_mv7.filter.shuffle.KairosJunction.Victor.Misc.csv \
  -b 482x_49x_mv7.filter.shuffle.mmr5000.KairosJunction.Victor.Infestor.csv \
  -o 482x_49x_mv7.filter.shuffle.KairosJunction.Victor.Misc.csv

python3 comb_csv_v2.py \
  -a 482x_49x_mv7.filter.shuffle.KairosJunction.Victor.Misc.csv \
  -b 482x_49x_mv7.filter.shuffle.mmr5000.KairosJunction.Victor.Swarmhost.csv \
  -o 482x_49x_mv7.filter.shuffle.KairosJunction.Victor.Misc.csv

python3 comb_csv_v2.py \
  -a 482x_49x_mv7.filter.shuffle.KairosJunction.Victor.Misc.csv \
  -b 482x_49x_mv7.filter.shuffle.mmr5000.KairosJunction.Victor.Ultralisk.csv \
  -o 482x_49x_mv7.filter.shuffle.KairosJunction.Victor.Misc.csv

python3 comb_csv_v2.py \
  -a 482x_49x_mv7.filter.shuffle.KairosJunction.Victor.Misc.csv \
  -b 482x_49x_mv7.filter.shuffle.mmr5000.KairosJunction.Victor.Broodlord.csv \
  -o 482x_49x_mv7.filter.shuffle.KairosJunction.Victor.Misc.csv

python3 comb_csv_v2.py \
  -a 482x_49x_mv7.filter.shuffle.KairosJunction.Victor.Misc.csv \
  -b 482x_49x_mv7.filter.shuffle.mmr5500.KairosJunction.Victor.Nydus.csv \
  -o 482x_49x_mv7.filter.shuffle.KairosJunction.Victor.Misc.csv

python3 comb_csv_v2.py \
  -a 482x_49x_mv7.filter.shuffle.KairosJunction.Victor.Misc.csv \
  -b 482x_49x_mv7.filter.shuffle.mmr5500.KairosJunction.Victor.Mutalisk.csv \
  -o 482x_49x_mv7.filter.shuffle.KairosJunction.Victor.Misc.csv

#
python3 comb_csv_v2.py \
  -a 482x_49x_4100_mv8.filter.shuffle.KairosJunction.Victor.Misc.csv \
  -b 4100.filter.shuffle.KairosJunction.Victor.FastLurker.Lxhan.csv \
  -o 482x_49x_4100_mv8.filter.shuffle.KairosJunction.Victor.Misc.csv

python3 comb_csv_v2.py \
  -a 482x_49x_4100_mv8.filter.shuffle.KairosJunction.Victor.Misc.csv \
  -b 4100.filter.shuffle.KairosJunction.Victor.CornerBase.LM.csv \
  -o 482x_49x_4100_mv8.filter.shuffle.KairosJunction.Victor.Misc.csv

#
python3 comb_csv_v2.py \
  -a 482x_49x_4100_mv8.filter.shuffle.KairosJunction.Victor.Misc.csv \
  -b 482x_49x_mv7.filter.shuffle.mmr5500.KairosJunction.Victor.TunnelingClaws.csv \
  -o 482x_49x_4100_mv8.filter.shuffle.KairosJunction.Victor.Misc.csv