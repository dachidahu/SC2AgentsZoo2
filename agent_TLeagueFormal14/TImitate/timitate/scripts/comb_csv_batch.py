import os


cmd_tmpl = "python3 comb_csv.py -a {a_csv} -b {b_csv} -o {o_csv}"
csv_file_list = [
  '4.8.2.filter.csv',
  '4.8.4.filter.csv',
  '4.8.6.filter.csv',
  '4.9.0.filter.csv',
  '4.9.1.filter.csv',
  '4.9.2.filter.csv',
  '4.9.3.filter.csv',
]
o_csv = '48x_49x_mv7.filter.csv'


for i in range(len(csv_file_list)):
  if i == 0:
    continue
  elif i == 1:
    a_csv = csv_file_list[i - 1]
  else:
    a_csv = o_csv
  b_csv = csv_file_list[i]
  cmd = cmd_tmpl.format(a_csv=a_csv, b_csv=b_csv, o_csv=o_csv)
  print(cmd, flush=True)
  os.system(cmd)