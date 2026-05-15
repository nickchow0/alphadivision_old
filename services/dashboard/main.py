import sys
sys.path.insert(0, "/app")

from shared.logger import get_logger
from flask import Flask

log = get_logger("dashboard")
app = Flask(__name__)

@app.route("/health")
def health():
    return {"status": "ok"}, 200

@app.route("/")
def index():
    return "<h1>AlphaDivision Dashboard</h1><p>Coming soon.</p>"

if __name__ == "__main__":
    log.info("Dashboard Service starting — placeholder")
    app.run(host="0.0.0.0", port=8080)
