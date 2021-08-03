f = open('/Users/pengsun/code/DistLadder3/distladder3/sandbox/tmp_winrates', 'rt')
lines = f.readlines()
for m, w in zip(lines[0].split(' '), lines[1].split(' ')):
  #print(w, m)
  if float(w) >= 0.95:
    print(m, w)