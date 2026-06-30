"""
app.py
------
Flask web dashboard for the MovieLens user dataset.

Routes:
  /            -> HTML dashboard (charts via Chart.js)
  /api/stats   -> JSON of all analyses (handy for tests & debugging)
  /health      -> lightweight health check for Jenkins / load balancers
"""

import os

from flask import Flask, jsonify, render_template

from data_analysis import build_summary, data_source_label

app = Flask(__name__)
# Preserve dict insertion order (occupations are pre-sorted most-common-first);
# Flask's JSON provider alphabetizes keys by default, which would undo that.
app.json.sort_keys = False


@app.route("/")
def dashboard():
    summary = build_summary()
    return render_template("index.html", s=summary)


@app.route("/api/stats")
def api_stats():
    return jsonify(build_summary())


@app.route("/health")
def health():
    return jsonify({"status": "ok", "data_source": data_source_label()})


if __name__ == "__main__":
    # Host 0.0.0.0 so the app is reachable from outside the EC2 instance.
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
