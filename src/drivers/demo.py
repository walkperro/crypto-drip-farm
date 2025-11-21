import random
from typing import Tuple

import requests


def claim(session: requests.Session, faucet: dict, wallet_address: str) -> Tuple[bool, float, str]:
    """
    HTTP-based demo faucet driver.

    This is a TEMPLATE for a real faucet driver:
      - Reads config from the `faucet` block in config.json
      - Makes an HTTP request with optional parameters
      - Interprets the response to decide success/amount/message

    For a real faucet:
      - Replace the placeholder logic with the faucet's actual API/URL behavior.
      - Only automate faucets that explicitly allow API/programmatic access.
    """
    name = faucet.get("name", "unknown_faucet")
    coin = faucet.get("coin", "unknown")
    endpoint = faucet.get("endpoint")
    method = (faucet.get("method") or "GET").upper()

    print(f"[DRIVER:demo] Claiming from faucet '{name}' ({coin}) at {endpoint} -> {wallet_address or 'NO_WALLET_SET'}")

    if not endpoint:
        # Fallback to simulation if no endpoint is defined
        return _simulate(coin, name)

    # Example payload building:
    params = {}
    data = {}

    # If the faucet expects the wallet in query params:
    if faucet.get("wallet_in_params", True):
        params["address"] = wallet_address

    # If the faucet expects a token or API key:
    api_key = faucet.get("api_key")
    if api_key:
        params["api_key"] = api_key

    try:
        if method == "GET":
            resp = session.get(endpoint, params=params, timeout=15)
        else:
            # POST or anything else -> POST
            data["address"] = wallet_address
            if api_key:
                data["api_key"] = api_key
            resp = session.post(endpoint, params=params, data=data, timeout=15)

        text = resp.text.strip()
        status_code = resp.status_code

        # ---- EXAMPLE PARSING LOGIC ----
        # For a real faucet, you will inspect `text` or `resp.json()`
        # and set these based on the actual API contract.
        #
        # Placeholder: treat 200 as "success" with a fake amount.
        if status_code == 200:
            # For a real faucet, parse the actual reward amount from JSON/body.
            amount = _extract_amount_placeholder(text)
            return True, amount, f"HTTP {status_code}"
        else:
            return False, 0.0, f"HTTP {status_code}: {text[:200]}"

    except Exception as e:
        return False, 0.0, f"exception: {e}"


def _simulate(coin: str, name: str):
    """
    Fallback simulation if no endpoint is provided.
    """
    print(f"[SIM] No endpoint configured for faucet '{name}' ({coin}). Using simulated payout.")
    success = random.random() > 0.1  # ~90% success
    if success:
        amount = random.randint(1, 20)  # fake units
        return True, float(amount), "simulated_ok"
    else:
        return False, 0.0, "simulated_error"


def _extract_amount_placeholder(body: str) -> float:
    """
    Placeholder parser: in a real implementation, this would parse
    JSON or text to extract the real payout amount.

    For now:
      - Just return a random small number to keep the system running.
    """
    return float(random.randint(1, 20))
