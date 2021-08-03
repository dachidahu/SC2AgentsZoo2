# mmr
python3 filter_csv_v3.py \
  -i 471_48x_49x_mv9.filter.shuffle.csv \
  -o 471_48x_49x_mv9.filter.shuffle.mmr3500.csv \
  --mmr_thres 3500

# mmr
python3 filter_csv_v3.py \
  -i 471_48x_49x_mv9.filter.shuffle.csv \
  -o 471_48x_49x_mv9.filter.shuffle.mmr5000.csv \
  --mmr_thres 5000

# mmr
python3 filter_csv_v3.py \
  -i 471_48x_49x_mv9.filter.shuffle.csv \
  -o 471_48x_49x_mv9.filter.shuffle.mmr6000.csv \
  --mmr_thres 6000
