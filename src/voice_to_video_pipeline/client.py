"""Shared HTTP client and cost tracker for OpenRouter calls."""


import requests

from . import config
from typing import Any


# Track the costs of each step (in USD).
costs: dict[str, float] = {}


def add_cost(
    label: str,
    amount: float | str | None,
) -> None:
    """Add a cost to the running total for a step.

    Parameters
    ----------
    label : str
        Name of the step (e.g., `"image"`).
    amount : float or str or None
        Cost in USD. `None` is treated as zero.
    """
    costs[label] = costs.get(label, 0.0) + float(amount or 0)


def request(
    method: str,
    url: str,
    **kwargs: Any,
) -> requests.Response:
    """Send an authenticated HTTP request.

    Parameters
    ----------
    method : str
        HTTP method (e.g., `"GET"` or `"POST"`).
    url : str
        Full URL, or a path starting with `/` that is appended to
        `config.BASE_URL`.
    **kwargs : Any
        Extra arguments for `requests.request` (`json`, `headers`,
        `timeout` ...). `timeout` defaults to 120 seconds.

    Returns
    -------
    requests.Response
        The successful response.

    Raises
    ------
    RuntimeError
        If the response status is not OK.
    """
    if url.startswith("/"):
        url = config.BASE_URL + url
    headers: dict[str, str] = {
        "Authorization": f"Bearer {config.API_KEY}",
    }
    headers.update(kwargs.pop("headers", {}))
    resp: requests.Response = requests.request(
        method=method,
        url=url,
        headers=headers,
        timeout=kwargs.pop("timeout", 120),
        **kwargs,
    )
    if not resp.ok:
        raise RuntimeError(
            f"[RuntimeError - client.py] {method} {url} -> "
            f"{resp.status_code}: {resp.text[:500]}\n"
        )
    return resp


def post_json(
    path: str,
    payload: dict[str, Any],
    timeout: int = 120,
) -> dict[str, Any]:
    """POST a JSON payload and return the decoded JSON reply.

    Parameters
    ----------
    path : str
        API path such as `"/chat/completions"`.
    payload : dict
        JSON-serializable request body.
    timeout : int, default 120
        Seconds to wait for the server.

    Returns
    -------
    dict
        Decoded JSON response.
    """
    return request(
        method="POST",
        url=path,
        json=payload,
        timeout=timeout,
    ).json()


def print_costs() -> None:
    """Print a per-step and total cost summary in USD."""
    print("\n[INFO - client.py] Cost summary (USD)\n")
    for label, amount in costs.items():
        print(f"    - {label:<14} ${amount:.4f}\n")
    print(f"    - {'TOTAL':<14} ${sum(costs.values()):.4f}\n")
