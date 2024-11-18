import base64
import re

from aws_lambda_powertools import Logger

logger = Logger()


def is_base64(s):
    """Check if a string is Base64 encoded."""
    try:
        return base64.b64encode(base64.b64decode(s)).decode() == s
    except Exception:
        return False


def remove_base64_prefix(s):
    """Remove the Base64 prefix if it exists."""
    prefix_pattern = r"^data:image/[a-zA-Z]+;base64,"
    return re.sub(prefix_pattern, "", s)


def safe_decode_base64(s):
    """Safely decode a Base64 string if it's encoded, otherwise return the original string."""
    # Remove the prefix if it exists
    s_without_prefix = remove_base64_prefix(s)

    if is_base64(s_without_prefix):
        try:
            return base64.b64decode(s_without_prefix)
        except Exception as e:
            logger.exception(f"Error decoding Base64: {e}")
            return None
    return s.encode("utf-8") if isinstance(s, str) else s
