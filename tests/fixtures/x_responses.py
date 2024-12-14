"""Test fixtures for X API responses."""

from datetime import datetime, timezone

# Success response fixtures
TWEET_RESPONSE = {
    "data": {
        "id": "1234567890",
        "text": "Test tweet",
        "author_id": "9876543210",
        "conversation_id": "1234567890",
        "created_at": "2024-12-14T10:00:00Z"
    }
}

MENTIONS_RESPONSE = {
    "data": [{
        "id": "1234567891",
        "text": "@gonzo test mention",
        "author_id": "9876543211",
        "conversation_id": "1234567891",
        "created_at": "2024-12-14T10:01:00Z"
    }]
}

CONVERSATION_RESPONSE = {
    "data": [{
        "id": "1234567892",
        "text": "Test conversation tweet",
        "author_id": "9876543212",
        "conversation_id": "1234567892",
        "created_at": "2024-12-14T10:02:00Z"
    }]
}

# Error response fixtures
RATE_LIMIT_RESPONSE = {
    "status": 429,
    "detail": "Too Many Requests",
    "title": "Too Many Requests",
    "type": "about:blank"
}

AUTH_ERROR_RESPONSE = {
    "status": 403,
    "detail": "Forbidden",
    "title": "Forbidden",
    "type": "about:blank"
}

# Rate limit headers
STANDARD_HEADERS = {
    'x-rate-limit-limit': '100',
    'x-rate-limit-remaining': '99',
    'x-rate-limit-reset': str(int((datetime.now(timezone.utc).timestamp() + 900)))
}

EXHAUSTED_HEADERS = {
    'x-rate-limit-limit': '100',
    'x-rate-limit-remaining': '0',
    'x-rate-limit-reset': str(int((datetime.now(timezone.utc).timestamp() + 900)))
}
