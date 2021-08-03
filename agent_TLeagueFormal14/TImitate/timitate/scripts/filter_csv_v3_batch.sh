python3 filter_csv_v3.py \
  -i 471_48x_49x_mv9.filter.csv \
  -o 471_48x_49x_mv9.filter.mmr6500.KairosJunction.csv \
  --mmr_thres 6500 \
  -m "Kairos Junction LE"

python3 filter_csv_v3.py \
  -i 471_48x_49x_mv9.filter.mmr6500.KairosJunction.csv \
  -o 471_48x_49x_mv9.filter.mmr6500.KairosJunction.Victor.csv \
  --result Victor

python3 filter_csv_v3.py \
  -i 471_48x_49x_mv9.filter.mmr6500.KairosJunction.Victor.csv \
  -o 471_48x_49x_mv9.filter.mmr6500.KairosJunction-120.5-27.5-Victor.csv \
  --start_pos_x 120.5 \
  --start_pos_y 27.5

python3 filter_csv_v3.py \
  -i 471_48x_49x_mv9.filter.mmr6500.KairosJunction.Victor.csv \
  -o 471_48x_49x_mv9.filter.mmr6500.KairosJunction-31.5-140.5-Victor.csv \
  --start_pos_x 31.5 \
  --start_pos_y 140.5


##############
python3 filter_csv_v3.py \
  -i 471_48x_49x_mv9.filter.csv \
  -o 471_48x_49x_mv9.filter.shuffle.mmr5500.Victor.csv \
  --mmr_thres 5500 \
  --result Victor

python3 filter_csv_v3.py \
  -i 471_48x_49x_mv9.filter.csv \
  -o 471_48x_49x_mv9.filter.mmr6000.Victor.csv \
  --mmr_thres 6000 \
  --result Victor

python3 filter_csv_v3.py \
  -i 471_48x_49x_mv9.filter.csv \
  -o 471_48x_49x_mv9.filter.mmr6200.Victor.csv \
  --mmr_thres 6200 \
  --result Victor

python3 filter_csv_v3.py \
  -i 471_48x_49x_mv9.filter.csv \
  -o 471_48x_49x_mv9.filter.mmr6200.csv \
  --mmr_thres 6200


####
python3 filter_csv_v3.py \
  -i 482x_49x_mv7.filter.csv \
  -o 482x_49x_mv7.filter.shuffle.mmr3500.csv \
  --mmr_thres 3500

python3 filter_csv_v3.py \
  -i 482x_49x_mv7.filter.csv \
  -o 482x_49x_mv7.filter.shuffle.mmr5500.Victor.csv \
  --mmr_thres 5500 \
  --result Victor

python3 filter_csv_v3.py \
  -i 482x_49x_mv7.filter.csv \
  -o 482x_49x_mv7.filter.shuffle.mmr6000.Victor.csv \
  --mmr_thres 6000 \
  --result Victor

python3 filter_csv_v3.py \
  -i 482x_49x_mv7.filter.csv \
  -o 482x_49x_mv7.filter.shuffle.mmr6200.Victor.csv \
  --mmr_thres 6200 \
  --result Victor


###
python3 filter_csv_v3.py \
  -i 482x_49x_mv7.filter.shuffle.mmr3500.Victor.TunnelingClaws.csv \
  -o 482x_49x_mv7.filter.shuffle.mmr5500.KairosJunction.Victor.TunnelingClaws.csv \
  --mmr_thres 5500 \
  -m "Kairos Junction LE" \
  --result Victor