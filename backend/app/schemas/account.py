import re
from enum import Enum
from urllib.parse import urlparse
from pydantic import BaseModel, Field, field_validator


class TargetInputType(str, Enum):
    USERNAME = "username"
    PROFILE_URL = "profile_url"


INSTAGRAM_USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9._]{1,30}$")
ALLOWED_HOSTS = {"instagram.com", "www.instagram.com"}
RESERVED_SYSTEM_PATHS = {
    "about",
    "explore",
    "reels",
    "stories",
    "direct",
    "accounts",
    "legal",
    "developer",
    "terms",
    "privacy",
    "api",
}


def sanitize_and_validate_target(raw_input: str) -> tuple[str, str, TargetInputType]:
    """
    Validates and normalizes an Instagram username or profile URL.
    Returns: (normalized_username, canonical_profile_url, input_type)
    Raises: ValueError with a clear, user-facing error message.
    """
    cleaned = raw_input.strip()
    if not cleaned:
        raise ValueError("Target input cannot be empty.")

    # Reject newlines, carriage returns, or control characters anywhere in the input
    if any(ord(c) < 32 or ord(c) == 127 for c in cleaned):
        raise ValueError("Target input contains invalid control characters or line breaks.")

    # Check if URL form (starts with http:// or https:// or contains instagram.com)
    is_url_pattern = cleaned.startswith("http://") or cleaned.startswith("https://") or "instagram.com" in cleaned.lower()

    if is_url_pattern:
        # Prepend scheme if user typed instagram.com/... directly
        parse_target = cleaned if "://" in cleaned else f"https://{cleaned}"
        try:
            parsed = urlparse(parse_target)
        except Exception:
            raise ValueError("Malformed URL provided.")

        if parsed.scheme.lower() not in ("http", "https"):
            raise ValueError("Invalid URL scheme. Only HTTP and HTTPS are permitted.")

        # Reject credentials or ports
        if parsed.username or parsed.password:
            raise ValueError("URLs containing user credentials are not permitted.")
        if parsed.port and parsed.port not in (80, 443):
            raise ValueError("Custom network ports are not permitted.")

        # Validate host
        hostname = (parsed.hostname or "").lower()
        if hostname not in ALLOWED_HOSTS:
            raise ValueError(f"Invalid host '{hostname}'. Target must be an Instagram domain (instagram.com).")

        # Reject query or fragments
        if parsed.query:
            raise ValueError("URL query parameters are not permitted for profile targets.")
        if parsed.fragment:
            raise ValueError("URL fragments are not permitted for profile targets.")

        # Parse path
        path_segments = [seg for seg in parsed.path.strip("/").split("/") if seg]
        if not path_segments or len(path_segments) != 1:
            raise ValueError("Invalid Instagram profile URL path. Expected format: https://instagram.com/<username>")

        extracted_candidate = path_segments[0]
        input_type = TargetInputType.PROFILE_URL
    else:
        # Direct username: strip leading '@' if provided
        extracted_candidate = cleaned[1:] if cleaned.startswith("@") else cleaned
        input_type = TargetInputType.USERNAME

    # Validate extracted candidate username
    candidate = extracted_candidate.strip()
    if not candidate:
        raise ValueError("Username cannot be empty.")

    if candidate.lower() in RESERVED_SYSTEM_PATHS:
        raise ValueError(f"'{candidate}' is a reserved Instagram path, not a user profile.")

    if not INSTAGRAM_USERNAME_REGEX.match(candidate):
        raise ValueError(
            "Invalid Instagram username format. Usernames must be 1-30 characters "
            "and contain only letters, numbers, periods, and underscores."
        )

    if candidate.startswith(".") or candidate.endswith("."):
        raise ValueError("Instagram usernames cannot start or end with a period.")

    if ".." in candidate:
        raise ValueError("Instagram usernames cannot contain consecutive periods.")

    normalized_username = candidate.lower()
    canonical_profile_url = f"https://www.instagram.com/{normalized_username}/"

    return normalized_username, canonical_profile_url, input_type


class AccountTargetValidateRequest(BaseModel):
    input: str = Field(..., min_length=1, max_length=255, description="Instagram username or profile URL")

    @field_validator("input")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Target input cannot be empty or purely whitespace.")
        return s


class AccountTarget(BaseModel):
    original_input: str
    normalized_username: str
    canonical_profile_url: str
    input_type: TargetInputType


class AccountValidateResponseData(BaseModel):
    is_valid: bool = True
    target: AccountTarget
    message: str


class AccountValidateResponse(BaseModel):
    success: bool = True
    data: AccountValidateResponseData
