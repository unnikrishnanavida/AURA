"""Configuration, authentication, retry, and serialization tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aura_sdk import (  # noqa: E402
    ApiKeyAuthenticator,
    RetryConfig,
    SdkConfig,
    SdkConfigurationError,
)
from aura_sdk.authentication import authenticator_for  # noqa: E402
from aura_sdk.config import TransportMode  # noqa: E402
from aura_sdk.retry import RetryPolicy  # noqa: E402


def test_local_mode_rejects_api_key() -> None:
    with pytest.raises(SdkConfigurationError):
        SdkConfig(mode=TransportMode.LOCAL, api_key="super_secret_key_123")


def test_api_key_min_length() -> None:
    with pytest.raises(SdkConfigurationError):
        SdkConfig(mode=TransportMode.HTTP, api_key="short")


def test_config_rejects_nonpositive_timeout() -> None:
    with pytest.raises(SdkConfigurationError):
        SdkConfig(timeout_seconds=0)


def test_retry_config_validation() -> None:
    with pytest.raises(SdkConfigurationError):
        RetryConfig(max_attempts=-1)


def test_authenticator_for_none_is_anonymous() -> None:
    auth = authenticator_for(None)
    assert auth.authorization_header() is None
    assert auth.describe() == "anonymous"


def test_api_key_authenticator_never_echoes_secret() -> None:
    auth = ApiKeyAuthenticator("this_is_a_very_long_secret_key_987")
    assert auth.authorization_header() == "Bearer this_is_a_very_long_secret_key_987"
    assert "this_is_a_very_long_secret_key_987" not in auth.describe()


def test_retry_policy_not_retryable_fails_immediately() -> None:
    from aura_sdk.errors import SdkValidationError

    policy = RetryPolicy(RetryConfig(max_attempts=3))

    class Boom(SdkValidationError):
        code = "sdk.validation"

    with pytest.raises(SdkValidationError):
        policy.run(lambda: (_ for _ in ()).throw(Boom("bad request")))


def test_retry_policy_exhausts_on_transient() -> None:
    from aura_sdk.errors import SdkRetryExhaustedError, SdkTimeoutError

    attempts = {"n": 0}

    def flaky() -> object:
        attempts["n"] += 1
        raise SdkTimeoutError("timeout")

    policy = RetryPolicy(RetryConfig(max_attempts=2, backoff_base_seconds=0.01), sleep=lambda _s: None)
    with pytest.raises(SdkRetryExhaustedError):
        policy.run(flaky)
    # initial + 2 retries
    assert attempts["n"] == 3