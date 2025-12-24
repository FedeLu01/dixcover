import re
from urllib.parse import urlparse


class Security:
    """Domain validator.

    Behavior:
    - Accepts either a plain domain or a URL; if a URL is provided the hostname is extracted.
    - Valid domains must be exactly two labels (examples: `example.com`).
    - Rejects IP addresses, credentials, subdomains (e.g. `www.example.com`), and inputs containing paths.
    - The final label (TLD) must be alphabetic (2-63 chars); the left label follows DNS label rules.
    """

    # Domain validation regex: exactly two labels (second-level domain + TLD)
    # - left label: 1-63 chars, letters/digits/hyphen, cannot start/end with hyphen
    # - right label (TLD): letters only, 2-63 chars
    # - overall length up to 253
    _DOMAIN_RE = re.compile(r"^(?=.{1,253}$)[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.[A-Za-z]{2,63}$")

    def is_valid_domain(self, domain: str) -> bool:
        if not domain or not isinstance(domain, str):
            return False

        raw = domain.strip()
        if not raw:
            return False

        # If the user provided a URL, extract the hostname (removes scheme, path, query)
        if '://' in raw or raw.startswith('http'):
            try:
                parsed = urlparse(raw)
                host = parsed.hostname or ''
            except Exception:
                return False
        else:
            # If there's a path component, take the first segment before '/'
            host = raw.split('/')[0]

        host = host.lower().strip()
        if not host:
            return False

        # Reject credentials (user:pass@host)
        if '@' in host:
            return False

        # Strip port if present (host:port)
        if ':' in host:
            host = host.split(':', 1)[0]

        # remove trailing dot if present (FQDN form)
        if host.endswith('.'):
            host = host[:-1]

        # Accept only domain forms with exactly 2 labels (no subdomains)
        parts = host.split('.')
        if len(parts) != 2:
            return False

        return bool(self._DOMAIN_RE.match(host))