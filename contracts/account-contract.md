# Instagram Account Target Contract

## 1. Overview
Defines accepted target input formats, validation criteria, normalization pipeline, and API schemas for target identity validation in SocialGuard.

## 2. Permitted Target Input Formats

### A. Raw Username
- May be prefixed with an optional `@` symbol (e.g. `@johndoe` or `johndoe`).
- Leading and trailing whitespace is stripped.
- Permitted character set: letters `[a-zA-Z]`, digits `[0-9]`, periods `.`, and underscores `_`.
- Length: 1 to 30 characters.
- Must not start or end with a period (`.`).
- Must not contain consecutive periods (`..`).
- Must not match Instagram system/reserved paths (e.g. `explore`, `reels`, `stories`, `accounts`, `developer`, `legal`, `terms`, `privacy`, `api`, `about`).

### B. Profile URL
- Permitted schemes: `http://` or `https://`.
- Permitted hostnames: `instagram.com`, `www.instagram.com`.
- No user credentials (`username:password@...` rejected).
- No custom ports (only default HTTP 80 and HTTPS 443 permitted).
- No query parameters (`?utm_source=...` rejected).
- No URL fragments (`#section` rejected).
- Path must match exactly `/<username>` or `/<username>/`.
- Must not point to non-profile resources (e.g. `/p/<post_id>`, `/stories/...`, etc.).

## 3. Canonical Form
All valid inputs are normalized to:
- `normalized_username`: Lowercase alphanumeric string matching `^[a-z0-9._]{1,30}$`.
- `canonical_profile_url`: `https://www.instagram.com/<normalized_username>/`.
- `input_type`: Enum `username` or `profile_url`.

## 4. API Schema (`POST /api/v1/accounts/validate`)

### Request
```json
{
  "input": "https://www.instagram.com/valid_user/"
}
```

### Successful Response (HTTP 200)
```json
{
  "success": true,
  "timestamp": "2026-10-11T01:50:00.000000Z",
  "data": {
    "is_valid": true,
    "target": {
      "original_input": "https://www.instagram.com/valid_user/",
      "normalized_username": "valid_user",
      "canonical_profile_url": "https://www.instagram.com/valid_user/",
      "input_type": "profile_url"
    },
    "message": "Target is syntactically valid. Account data collection is planned for Phase 2."
  }
}
```

### Validation Error Response (HTTP 422)
```json
{
  "success": false,
  "timestamp": "2026-10-11T01:50:00.000000Z",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid host 'evil.com'. Target must be an Instagram domain (instagram.com).",
    "details": [...]
  }
}
```
