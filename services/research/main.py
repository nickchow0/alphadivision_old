# services/research/main.py
import sys
sys.path.insert(0, "/app")

from flask import Flask
from shared.logger import get_logger

log = get_logger("research")

app = Flask(__name__)


@app.route("/health")
def health():
    return {"status": "ok"}, 200


if __name__ == "__main__":
    log.info("Research Service starting")
    app.run(host="0.0.0.0", port=8081)
