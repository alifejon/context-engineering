"""
Tests for error handling module.

Example of production-quality unit tests.
"""

import pytest
import time

from examples.production_ready.core.error_handling import (
    with_retry,
    validate_input,
    ValidationError,
    CircuitBreaker
)


class TestRetryDecorator:
    """Test retry logic."""

    @pytest.fixture(autouse=True)
    def _no_sleep(self, monkeypatch):
        """Prevent actual sleeping during retry tests."""
        monkeypatch.setattr(
            "examples.production_ready.core.error_handling.time.sleep",
            lambda _: None,
        )

    def test_success_on_first_attempt(self):
        """Function succeeds on first attempt."""
        call_count = 0

        @with_retry(max_attempts=3)
        def succeeding_function():
            nonlocal call_count
            call_count += 1
            return "success"

        result = succeeding_function()

        assert result == "success"
        assert call_count == 1

    def test_success_after_retries(self):
        """Function succeeds after some failures."""
        call_count = 0

        @with_retry(max_attempts=3, exceptions=(ValueError,))
        def flaky_function():
            nonlocal call_count
            call_count += 1

            if call_count < 3:
                raise ValueError("Temporary error")

            return "success"

        result = flaky_function()

        assert result == "success"
        assert call_count == 3

    def test_failure_after_max_attempts(self):
        """Function fails after max attempts."""
        call_count = 0

        @with_retry(max_attempts=3, exceptions=(ValueError,))
        def always_failing_function():
            nonlocal call_count
            call_count += 1
            raise ValueError("Permanent error")

        with pytest.raises(ValueError):
            always_failing_function()

        assert call_count == 3

    def test_exponential_backoff(self, monkeypatch):
        """Verify exponential backoff timing without real sleeping."""
        call_times = []
        fake_time = 0.0

        def fake_sleep(duration):
            nonlocal fake_time
            fake_time += duration

        def fake_time_fn():
            return fake_time

        monkeypatch.setattr(
            "examples.production_ready.core.error_handling.time.sleep",
            fake_sleep,
        )
        monkeypatch.setattr(
            "examples.production_ready.core.error_handling.time.time",
            fake_time_fn,
        )

        @with_retry(max_attempts=3, backoff_factor=2.0, exceptions=(ValueError,))
        def timed_function():
            call_times.append(fake_time_fn())
            if len(call_times) < 3:
                raise ValueError("Error")
            return "success"

        result = timed_function()

        assert result == "success"
        assert len(call_times) == 3
        assert call_times == [0.0, 2.0, 6.0]

    def test_on_retry_callback(self):
        """Verify on_retry callback is called."""
        retry_attempts = []

        def on_retry_callback(attempt, exception):
            retry_attempts.append((attempt, str(exception)))

        @with_retry(
            max_attempts=3,
            exceptions=(ValueError,),
            on_retry=on_retry_callback
        )
        def failing_function():
            if len(retry_attempts) < 2:
                raise ValueError(f"Error {len(retry_attempts)}")
            return "success"

        result = failing_function()

        assert result == "success"
        assert len(retry_attempts) == 2
        assert retry_attempts[0] == (0, "Error 0")
        assert retry_attempts[1] == (1, "Error 1")


class TestInputValidation:
    """Test input validation."""

    def test_valid_inputs(self):
        """Valid inputs pass validation."""
        query, context = validate_input(
            query="What is context engineering?",
            context="Context engineering is...",
            min_quality=0.8,
            max_cost=1.0
        )

        assert query == "What is context engineering?"
        assert context == "Context engineering is..."

    def test_none_query_raises_error(self):
        """None query raises ValidationError."""
        with pytest.raises(ValidationError, match="Query cannot be None"):
            validate_input(None, "context", 0.8)

    def test_non_string_query_raises_error(self):
        """Non-string query raises ValidationError."""
        with pytest.raises(ValidationError, match="Query must be string"):
            validate_input(123, "context", 0.8)

    def test_empty_query_raises_error(self):
        """Empty query raises ValidationError."""
        with pytest.raises(ValidationError, match="Query cannot be empty"):
            validate_input("", "context", 0.8)

        with pytest.raises(ValidationError, match="Query cannot be empty"):
            validate_input("   ", "context", 0.8)

    def test_query_too_long_raises_error(self):
        """Query that's too long raises ValidationError."""
        long_query = "x" * 60000

        with pytest.raises(ValidationError, match="Query too long"):
            validate_input(long_query, "context", 0.8)

    def test_none_context_defaults_to_empty(self):
        """None context defaults to empty string."""
        query, context = validate_input("query", None, 0.8)

        assert query == "query"
        assert context == ""

    def test_context_too_long_raises_error(self):
        """Context that's too long raises ValidationError."""
        long_context = "x" * 600000

        with pytest.raises(ValidationError, match="Context too long"):
            validate_input("query", long_context, 0.8)

    def test_invalid_min_quality_raises_error(self):
        """Invalid min_quality raises ValidationError."""
        with pytest.raises(ValidationError, match="min_quality must be number"):
            validate_input("query", "context", "not a number")

        with pytest.raises(ValidationError, match="min_quality must be 0-1"):
            validate_input("query", "context", -0.1)

        with pytest.raises(ValidationError, match="min_quality must be 0-1"):
            validate_input("query", "context", 1.5)

    def test_invalid_max_cost_raises_error(self):
        """Invalid max_cost raises ValidationError."""
        with pytest.raises(ValidationError, match="max_cost must be number"):
            validate_input("query", "context", 0.8, "not a number")

        with pytest.raises(ValidationError, match="max_cost must be positive"):
            validate_input("query", "context", 0.8, -1.0)

    def test_input_sanitization(self):
        """Inputs are trimmed/sanitized."""
        query, context = validate_input(
            query="  query with spaces  ",
            context="  context with spaces  ",
            min_quality=0.8
        )

        assert query == "query with spaces"
        assert context == "context with spaces"


class TestCircuitBreaker:
    """Test circuit breaker pattern."""

    def test_closed_state_allows_calls(self):
        """Circuit breaker in CLOSED state allows calls."""
        breaker = CircuitBreaker(failure_threshold=3)

        def working_function():
            return "success"

        result = breaker.call(working_function)

        assert result == "success"
        assert breaker.state == CircuitBreaker.CLOSED

    def test_opens_after_threshold_failures(self):
        """Circuit breaker opens after threshold failures."""
        breaker = CircuitBreaker(failure_threshold=3)

        def failing_function():
            raise Exception("Error")

        # Fail 3 times
        for _ in range(3):
            with pytest.raises(Exception):
                breaker.call(failing_function)

        # Should be OPEN now
        assert breaker.state == CircuitBreaker.OPEN

        # Further calls should be rejected
        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            breaker.call(failing_function)

    def test_half_open_state_after_timeout(self):
        """Circuit breaker transitions to HALF_OPEN after timeout."""
        breaker = CircuitBreaker(
            failure_threshold=2,
            recovery_timeout=0.1  # 100ms for testing
        )

        def failing_function():
            raise Exception("Error")

        # Trigger OPEN state
        for _ in range(2):
            with pytest.raises(Exception):
                breaker.call(failing_function)

        assert breaker.state == CircuitBreaker.OPEN

        # Wait for recovery timeout
        time.sleep(0.15)

        # Next call should transition to HALF_OPEN
        # (and fail, but that's ok for this test)
        with pytest.raises(Exception):
            breaker.call(failing_function)

        # After the failed call in HALF_OPEN, should revert to OPEN
        assert breaker.state == CircuitBreaker.OPEN

    def test_closes_after_successful_half_open_call(self):
        """Circuit breaker closes after successful call in HALF_OPEN state."""
        breaker = CircuitBreaker(
            failure_threshold=2,
            recovery_timeout=0.1
        )

        call_count = [0]

        def sometimes_failing_function():
            call_count[0] += 1
            if call_count[0] <= 2:
                raise Exception("Error")
            return "success"

        # Trigger OPEN state
        for _ in range(2):
            with pytest.raises(Exception):
                breaker.call(sometimes_failing_function)

        assert breaker.state == CircuitBreaker.OPEN

        # Wait for recovery timeout
        time.sleep(0.15)

        # This call should succeed and close the circuit
        result = breaker.call(sometimes_failing_function)

        assert result == "success"
        assert breaker.state == CircuitBreaker.CLOSED
        assert breaker.failure_count == 0


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
