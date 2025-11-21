from .demo import claim as demo_claim

DRIVERS = {
    "demo": demo_claim,
}


def get_driver(name: str):
    """
    Return a driver claim function by name.
    Each driver must be a function(session, faucet_config, wallet_address)
    -> (success: bool, amount: float, message: str)
    """
    driver = DRIVERS.get(name)
    if driver is None:
        raise ValueError(f"No driver registered with name '{name}'")
    return driver
