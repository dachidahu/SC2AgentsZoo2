""" run web service

Example:
python3 run_web_svc.py \
  --watched_dir /root/eval_results/evYYMMDD \
  --port 8888
"""
import os
import argparse

from flask import Flask
from flask_autoindex import AutoIndex

parser = argparse.ArgumentParser()
parser.add_argument("--watched_dir", type=str,
                    default="/root/eval_results/evYYMMDD",
                    help="watched working dir.")
parser.add_argument("--port", type=int, default=8888, help="web service port")
args = parser.parse_args()


app = Flask(__name__)
idx = AutoIndex(app, browse_root=args.watched_dir, add_url_rules=False)


@app.route('/')
@app.route('/<path:path>')
def autoindex(path='.'):
  recognized_suffix = ['.pgn', '.elo.ratings', '.ratings', '.ini', '.log',
                       '.err', '.txt', '.list']
  mimetype = ('text/plain' if any([path.endswith(s) for s in recognized_suffix])
              else None)
  return idx.render_autoindex(path, sort_by='name', order=1, mimetype=mimetype)


if __name__ == "__main__":
  app.run(debug=False, port=args.port, host='0.0.0.0')
