import json
import time
import csv
import os
from datetime import datetime, timedelta

import requests

CONFIG_PATH = "config/config.json"


def load_config(path=CONFIG_PATH):
    with open(path, "r") as f:
        return json.load(f)


def init_log(log_path):
    # Ensure logs directory exists
    log_dir = os.path.dirname(log_path)
    if log_dir and not os.path.isdir(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    file_exists = os.path.isfile(log_path)
    if not file_exists:
        with open(log_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "faucet", "coin", "amount", "status", "message"])


def log_claim(log_path, faucet_name, coin, amount, status, message=""):
    with open(log_path, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.utcnow().isoformat(),
            faucet_name,
            coin,
            amount,
            status,
            message
        ])


def get_session(config):
    """
    Returns a requests.Session that optionally routes through Tor SOCKS5.
    """
    session = requests.Session()

    if config.get("use_tor") and config.get("tor_socks_proxy"):
        proxy = config["tor_socks_proxy"]
        session.proxies = {
            "http": proxy,
            "https": proxy,
        }
        print(f"[INFO] Using Tor proxy: {proxy}")
    else:
        print("[INFO] Not using proxy")

    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Linux; Android 14; Termux) Python/requests CryptoDripFarm/0.1"
    })
    return session


def can_claim(faucet, last_run_at):
    """
    Check if it's time to claim again based on interval.
    """
    interval_min = faucet.get("claim_interval_minutes", 30)
    if last_run_at is None:
        return True
    return datetime.utcnow() - last_run_at >= timedelta(minutes=interval_min)


def simulate_faucet_claim(session, faucet, wallet_address):
    """
    v1: Simulated faucet claim.

    Later, you can replace this with real faucet logic for services
    that explicitly allow API or programmatic claims.
    """
    name = faucet["name"]
    coin = faucet["coin"]

    print(f"[SIM] Claiming from faucet: {name} for coin: {coin} -> wallet: {wallet_address}")

    import random
    success = random.random() > 0.1  # ~90% simulated success rate
    if success:
        amount = random.randint(1, 20)  # fake units for testing
        return True, amount, "ok"
    else:
        return False, 0, "simulated error"


def main_loop():
    config = load_config()

    log_path = config.get("logging", {}).get("log_file", "logs/farm_log.csv")
    init_log(log_path)

    session = get_session(config)

    faucets = [f for f in config.get("faucets", []) if f.get("enabled", True)]
    if not faucets:
        print("[WARN] No faucets enabled in config. Exiting.")
        return

    last_run = {f["name"]: None for f in faucets}

    print("[INFO] Starting Crypto Drip Farm loop. Press Ctrl+C to stop.")

    while True:
        for faucet in faucets:
            name = faucet["name"]
            coin = faucet["coin"]
            wallet = config.get("wallets", {}).get(coin)

            if not wallet:
                print(f"[WARN] No wallet configured for coin '{coin}', skipping faucet '{name}'")
                continue

            if not can_claim(faucet, last_run[name]):
                continue

            print(f"[INFO] Time to claim from {name} ({coin})")

            try:
                # For now this is a simulation function.
                # Later, swap it for a real claim function per faucet/API.
                success, amount, message = simulate_faucet_claim(session, faucet, wallet)
                last_run[name] = datetime.utcnow()

                status_str = "success" if success else "fail"
                log_claim(log_path, name, coin, amount, status_str, message)
                print(f"[INFO] Claim result from {name}: {status_str}, amount={amount}, msg={message}")
            except Exception as e:
                msg = str(e)
                log_claim(log_path, name, coin, 0, "error", msg)
                print(f"[ERROR] Error claiming from {name}: {msg}")

        # Sleep a bit before the next pass; each faucet respects its own interval
        time.sleep(30)


if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        print("\n[INFO] Stopped by user.")
