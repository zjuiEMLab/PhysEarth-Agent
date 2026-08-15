"""The only place in PhysEarth that opens an outbound connection.

Three rules, all enforced here rather than trusted to callers:

  - the host must be on the allow list, and the URL is always built by us from a DOI or
    an identifier an allowed host itself returned; the agent never supplies a URL
  - a response is read to a byte ceiling, so a slow or enormous document cannot exhaust
    a 2 vCPU instance shared by every visitor
  - a failure comes back as a labelled outcome, never as a silent empty result, because
    "the upstream service is down" and "there is no such paper" must never look alike

`PHYSEARTH_ONLINE=0` closes the whole layer. Nothing else in the system changes when it
is closed: the bundled corpus, the models and the reference data do not go through here.
"""

import json
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request

from physearth import config

ALLOWED_HOSTS = (
    "api.openalex.org",
    "www.ebi.ac.uk",
    "tc.copernicus.org",
    "gmd.copernicus.org",
    "hess.copernicus.org",
    "bg.copernicus.org",
    "acp.copernicus.org",
    "essd.copernicus.org",
    "nhess.copernicus.org",
    "os.copernicus.org",
    "soil.copernicus.org",
    "esurf.copernicus.org",
    "api.github.com",
    "raw.githubusercontent.com",
)

TIMEOUT_S = 20.0
MAX_BYTES = 6_000_000
USER_AGENT = "physearth-agent/0.1 (+https://github.com/zjuiEMLab/PhysEarth-Agent)"


class Offline(Exception):
    """Raised when the online layer is switched off. Not a fault, a configuration."""


class Upstream(Exception):
    """An allowed host failed to answer. Distinct from answering with nothing."""

    def __init__(self, host, detail):
        super().__init__("%s: %s" % (host, detail))
        self.host = host
        self.detail = detail


def online():
    return config.get("PHYSEARTH_ONLINE") != "0"


def _check(url):
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https":
        raise ValueError("only https is allowed, got %r" % parsed.scheme)
    if parsed.hostname not in ALLOWED_HOSTS:
        raise ValueError("%s is not an allowed host" % parsed.hostname)
    return parsed.hostname


def get_bytes(url, timeout=TIMEOUT_S, max_bytes=MAX_BYTES):
    if not online():
        raise Offline("PHYSEARTH_ONLINE is 0, so nothing is fetched")
    host = _check(url)
    started = time.perf_counter()
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(
            request, timeout=timeout, context=ssl.create_default_context()
        ) as response:
            payload = response.read(max_bytes + 1)
    except urllib.error.HTTPError as exc:
        raise Upstream(host, "HTTP %s" % exc.code) from exc
    except (urllib.error.URLError, TimeoutError, ssl.SSLError) as exc:
        raise Upstream(host, "%s: %s" % (type(exc).__name__, exc)) from exc
    if len(payload) > max_bytes:
        raise Upstream(host, "the document is larger than the %d byte ceiling" % max_bytes)
    return payload, round(time.perf_counter() - started, 2)


def get_json(url, **kwargs):
    payload, elapsed = get_bytes(url, **kwargs)
    try:
        return json.loads(payload.decode("utf-8")), elapsed
    except (ValueError, UnicodeDecodeError) as exc:
        raise Upstream(_check(url), "the response was not JSON: %s" % exc) from exc


def get_text(url, **kwargs):
    payload, elapsed = get_bytes(url, **kwargs)
    return payload.decode("utf-8", errors="replace"), elapsed
