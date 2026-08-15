"""Classifying an upstream failure: transient, rate limited, or done for the day."""


def _fault(exc):
    """A short label for an upstream failure, carrying the HTTP status when there is one."""
    status = getattr(exc, "status_code", None)
    if status == 429:
        if _dead_for_today(exc) == "quota":
            return "model quota or balance exhausted (HTTP 429)"
        return "rate limited (HTTP 429)"
    if status:
        return "HTTP %s" % status
    return type(exc).__name__


def _upstream_text(exc):
    """Whatever the endpoint actually said, bounded. This is what makes a fault diagnosable."""
    body = getattr(exc, "body", None)
    if isinstance(body, dict):
        message = body.get("message") or (body.get("error") or {}).get("message")
        if message:
            return str(message)[:400]
    return str(exc)[:400]


def _rate_limited(exc):
    """A limit counted over a window, which waiting clears. Not the same as a spent quota.

    The endpoint expresses this two ways: an SDK RateLimitError, and a plain message about
    requests per minute. Both mean wait, not stop.
    """
    if "RateLimit" in type(exc).__name__:
        return True
    text = _upstream_text(exc).lower()
    return "rpm" in text or "rate limit" in text or "too many requests" in text


def _dead_for_today(exc):
    """Faults that belong to one model and will not clear by retrying.

    Two are known: the free quota is per model and per day, and a model can be withdrawn
    from the endpoint entirely, which it reports as having no provider.
    """
    status = getattr(exc, "status_code", None)
    text = _upstream_text(exc).lower()
    exhausted = (
        "quota" in text
        or "insufficient balance" in text
        or "insufficient credit" in text
        or "balance is insufficient" in text
    )
    if status == 429 and exhausted:
        return "quota"
    if status == 400 and "no provider" in text:
        return "withdrawn"
    return ""
