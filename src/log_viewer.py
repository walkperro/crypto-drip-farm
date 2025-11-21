import csv
import os
from collections import defaultdict
from datetime import datetime

LOG_PATH = "logs/farm_log.csv"


def load_log(path=LOG_PATH):
    if not os.path.isfile(path):
        print(f"[WARN] Log file not found at {path}")
        return []

    rows = []
    with open(path, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def summarize(rows):
    """
    Summarize by date, coin, and faucet.
    """
    by_date_coin = defaultdict(float)
    by_faucet = defaultdict(float)
    status_counts = defaultdict(int)

    for row in rows:
        ts = row.get("timestamp")
        coin = row.get("coin", "unknown")
        faucet = row.get("faucet", "unknown")
        status = row.get("status", "unknown")
        try:
            amount = float(row.get("amount", 0))
        except ValueError:
            amount = 0.0

        # Extract date only (YYYY-MM-DD)
        try:
            dt = datetime.fromisoformat(ts)
            date_str = dt.date().isoformat()
        except Exception:
            date_str = "unknown"

        key = (date_str, coin)
        by_date_coin[key] += amount
        by_faucet[faucet] += amount
        status_counts[status] += 1

    return by_date_coin, by_faucet, status_counts


def print_summary(by_date_coin, by_faucet, status_counts):
    print("\n=== Summary by Date & Coin ===")
    if not by_date_coin:
        print("No data.")
    else:
        for (date_str, coin), total in sorted(by_date_coin.items()):
            print(f"{date_str}  |  {coin}: {total}")

    print("\n=== Summary by Faucet (Total Amount) ===")
    if not by_faucet:
        print("No data.")
    else:
        for faucet, total in sorted(by_faucet.items(), key=lambda x: x[0]):
            print(f"{faucet}: {total}")

    print("\n=== Status Counts ===")
    if not status_counts:
        print("No data.")
    else:
        for status, count in status_counts.items():
            print(f"{status}: {count}")
