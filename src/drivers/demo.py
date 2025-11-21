import random


def claim(session, faucet_config, wallet_address):
    """
    Demo faucet driver.

    This simulates a faucet claim. Later you can replace this logic
    with a real API call for a faucet that explicitly allows automation.
    """
    name = faucet_config.get("name", "demo_faucet")
    coin = faucet_config.get("coin", "unknown")

    print(f"[DEMO] Claiming from faucet: {name} ({coin}) -> wallet: {wallet_address}")

    # Simulate success or failure
    success = random.random() > 0.1  # ~90% success
    if success:
        amount = random.randint(1, 20)  # Fake drip amount
        message = "demo-ok"
    else:
        amount = 0
        message = "demo-fail"

    return success, float(amount), message
