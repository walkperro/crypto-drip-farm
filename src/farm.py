import json
import time
import csv
import os
from datetime import datetime, timedelta

import requests

from drivers import get_driver

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
        "User-Agent": "Mozilla/5.0 (Linux; Android 14; Termux) Python/requests CryptoDripFarm/0.2"
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


def prompt_wallets_for_faucets(faucets):
    """
    Ask the user for a wallet address per coin type used by faucets.
    """
    coins = sorted({f.get("coin") for f in faucets if f.get("coin")})
    wallets = {}

    print("[SETUP] Wallet configuration")
    for coin in coins:
        while True:
            addr = input(f"Enter wallet address for coin '{coin}': ").strip()
            if addr:
                wallets[coin] = addr
                break
            else:
                print("Wallet address cannot be empty. Try again.")
    print("[SETUP] Wallets configured:", wallets)
    return wallets


def main_loop():
    config = load_config()

    faucets = [f for f in config.get("faucets", []) if f.get("enabled", True)]
    if not faucets:
        print("[WARN] No faucets enabled in config. Exiting.")
        return

    # Prompt user for wallet addresses per coin
    wallets = prompt_wallets_for_faucets(faucets)

    log_path = config.get("logging", {}).get("log_file", "logs/farm_log.csv")
    init_log(log_path)

    session = get_session(config)

    last_run = {f["name"]: None for f in faucets}

    print("[INFO] Starting Crypto Drip Farm loop. Press Ctrl+C to stop.")

    while True:
        for faucet in faucets:
            name = faucet["name"]
            coin = faucet.get("coin")
            driver_name = faucet.get("driver", "demo")

            if not coin:
                print(f"[WARN] Faucet '{name}' has no coin specified, skipping.")
                continue

            wallet = wallets.get(coin)
            if not wallet:
                print(f"[WARN] No wallet configured for coin '{coin}', skipping faucet '{name}'.")
                continue

            if not can_claim(faucet, last_run[name]):
                continue

            print(f"[INFO] Time to claim from {name} ({coin}) via driver '{driver_name}'")

            try:
                driver = get_driver(driver_name)
            except ValueError as e:
                msg = str(e)
                log_claim(log_path, name, coin, 0, "driver_error", msg)
                print(f"[ERROR] {msg}")
                continue

            try:
                success, amount, message = driver(session, faucet, wallet)
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
