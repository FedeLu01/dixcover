import tldextract
from validators import domain as validate_domain
from validators.utils import ValidationError


class Security:
    """Domain validator.

    Behavior:
    - Accepts either a plain domain or a URL; tldextract handles URL parsing automatically.
    - Valid domains must be 2LD (second-level domain) only, supporting multi-level TLDs.
      Examples: `example.com`, `example.com.ar`, `example.co.uk`
    - Rejects IP addresses, credentials, subdomains (e.g. `www.example.com`).
    - Uses tldextract for proper TLD handling and validators.domain for format validation.
    """

    def is_valid_domain(self, domain: str) -> bool:
        if not domain or not isinstance(domain, str):
            return False

        raw = domain.strip()
        if not raw:
            return False

        # Reject credentials (user:pass@host) - tldextract doesn't handle this well
        if '@' in raw:
            return False

        # Extract domain components using tldextract (handles URLs, ports, and multi-level TLDs)
        # Examples:
        #   "example.com" -> subdomain="", domain="example", suffix="com"
        #   "https://example.com/path" -> subdomain="", domain="example", suffix="com"
        #   "example.com.ar" -> subdomain="", domain="example", suffix="com.ar"
        #   "www.example.com" -> subdomain="www", domain="example", suffix="com"
        try:
            extracted = tldextract.extract(raw)
        except Exception:
            return False

        # Reject if there's a subdomain (must be empty for 2LD only)
        if extracted.subdomain:
            return False

        # Reject if domain or suffix is empty
        if not extracted.domain or not extracted.suffix:
            return False

        # Reconstruct the full domain for validation (domain + suffix)
        full_domain = f"{extracted.domain}.{extracted.suffix}"

        # Use validators.domain for robust domain format validation
        try:
            return validate_domain(full_domain) is True
        except (ValidationError, UnicodeError):
            return False