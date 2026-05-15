import sys
import time
sys.path.insert(0, "/app")

from shared.logger import get_logger

log = get_logger("data")

def main():
    log.info("Data Service starting — placeholder")
    while True:
        time.sleep(60)

if __name__ == "__main__":
    main()
