"""
Production-Ready Logging Configuration

실제 프로덕션 환경에서 사용 가능한 구조화된 로깅 시스템
"""

import logging
import sys
import json
from datetime import datetime
from typing import Any, Dict
from pythonjsonlogger import jsonlogger


class StructuredFormatter(jsonlogger.JsonFormatter):
    """
    구조화된 JSON 로그 포맷터.

    로그를 JSON으로 출력하여 Elasticsearch, CloudWatch 등에서 쉽게 파싱 가능.
    """

    def add_fields(self, log_record: Dict, record: logging.LogRecord, message_dict: Dict):
        """Add custom fields to log record."""
        super().add_fields(log_record, record, message_dict)

        # Add timestamp
        log_record['timestamp'] = datetime.utcnow().isoformat()

        # Add log level
        log_record['level'] = record.levelname

        # Add logger name
        log_record['logger'] = record.name

        # Add source location
        log_record['source'] = {
            'file': record.filename,
            'function': record.funcName,
            'line': record.lineno
        }

        # Add process/thread info
        log_record['process'] = {
            'id': record.process,
            'name': record.processName
        }

        log_record['thread'] = {
            'id': record.thread,
            'name': record.threadName
        }


def setup_logging(
    level: str = "INFO",
    json_logs: bool = False,
    log_file: str = None
) -> None:
    """
    Configure application logging.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_logs: Whether to output logs in JSON format
        log_file: Optional file path for file logging

    Example:
        setup_logging(level="INFO", json_logs=True)
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    root_logger.handlers = []

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    if json_logs:
        # JSON formatter for production
        formatter = StructuredFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s'
        )
    else:
        # Human-readable formatter for development
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - '
            '[%(filename)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Set third-party loggers to WARNING to reduce noise
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('openai').setLevel(logging.INFO)
    logging.getLogger('httpx').setLevel(logging.WARNING)


class RequestLogger:
    """
    Request-scoped logger with correlation ID.

    모든 로그에 request_id를 포함시켜 분산 시스템에서 요청 추적 가능.
    """

    def __init__(self, logger: logging.Logger, request_id: str):
        self.logger = logger
        self.request_id = request_id

    def _add_context(self, extra: Dict = None) -> Dict:
        """Add request context to log."""
        context = {'request_id': self.request_id}
        if extra:
            context.update(extra)
        return context

    def debug(self, msg: str, **kwargs):
        self.logger.debug(msg, extra=self._add_context(kwargs))

    def info(self, msg: str, **kwargs):
        self.logger.info(msg, extra=self._add_context(kwargs))

    def warning(self, msg: str, **kwargs):
        self.logger.warning(msg, extra=self._add_context(kwargs))

    def error(self, msg: str, **kwargs):
        self.logger.error(msg, extra=self._add_context(kwargs), exc_info=True)

    def critical(self, msg: str, **kwargs):
        self.logger.critical(msg, extra=self._add_context(kwargs), exc_info=True)


class MetricsLogger:
    """
    성능 메트릭 로깅.

    타이밍, 비용, 토큰 사용량 등 메트릭을 구조화된 형태로 로깅.
    """

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def log_query_metrics(
        self,
        request_id: str,
        query_length: int,
        context_tokens: int,
        response_tokens: int,
        model: str,
        cost: float,
        latency_ms: float,
        cached: bool = False,
        quality_score: float = None
    ):
        """Log query execution metrics."""
        self.logger.info(
            "query_executed",
            extra={
                'event_type': 'query_metrics',
                'request_id': request_id,
                'metrics': {
                    'query_length': query_length,
                    'context_tokens': context_tokens,
                    'response_tokens': response_tokens,
                    'total_tokens': context_tokens + response_tokens,
                    'model': model,
                    'cost_usd': cost,
                    'latency_ms': latency_ms,
                    'cached': cached,
                    'quality_score': quality_score
                }
            }
        )

    def log_optimization_metrics(
        self,
        request_id: str,
        original_tokens: int,
        optimized_tokens: int,
        compression_ratio: float,
        strategy: str
    ):
        """Log context optimization metrics."""
        self.logger.info(
            "context_optimized",
            extra={
                'event_type': 'optimization_metrics',
                'request_id': request_id,
                'metrics': {
                    'original_tokens': original_tokens,
                    'optimized_tokens': optimized_tokens,
                    'tokens_saved': original_tokens - optimized_tokens,
                    'compression_ratio': compression_ratio,
                    'strategy': strategy
                }
            }
        )

    def log_cache_metrics(
        self,
        request_id: str,
        cache_hit: bool,
        cache_key: str = None
    ):
        """Log cache hit/miss."""
        self.logger.info(
            "cache_access",
            extra={
                'event_type': 'cache_metrics',
                'request_id': request_id,
                'metrics': {
                    'cache_hit': cache_hit,
                    'cache_key': cache_key
                }
            }
        )

    def log_error_metrics(
        self,
        request_id: str,
        error_type: str,
        error_message: str,
        recoverable: bool
    ):
        """Log error occurrence."""
        self.logger.error(
            "error_occurred",
            extra={
                'event_type': 'error_metrics',
                'request_id': request_id,
                'metrics': {
                    'error_type': error_type,
                    'error_message': error_message,
                    'recoverable': recoverable
                }
            }
        )


# Example usage
if __name__ == "__main__":
    print("="*60)
    print("Example 1: Basic Logging Setup")
    print("="*60)

    # Development mode (human-readable)
    setup_logging(level="DEBUG", json_logs=False)

    logger = logging.getLogger(__name__)
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")

    print("\n" + "="*60)
    print("Example 2: JSON Structured Logging")
    print("="*60)

    # Production mode (JSON)
    setup_logging(level="INFO", json_logs=True)

    logger = logging.getLogger("production")
    logger.info(
        "Query processed",
        extra={
            'request_id': 'req_123',
            'user_id': 'user_456',
            'cost': 0.0123,
            'tokens': 1500
        }
    )

    print("\n" + "="*60)
    print("Example 3: Request Logger with Correlation ID")
    print("="*60)

    # Back to readable format
    setup_logging(level="INFO", json_logs=False)

    base_logger = logging.getLogger("request_handler")
    request_logger = RequestLogger(base_logger, request_id="req_789")

    request_logger.info(
        "Request started",
        user_id="user_123",
        endpoint="/api/optimize"
    )

    request_logger.info(
        "Query optimized",
        tokens_saved=500,
        cost_saved=0.015
    )

    request_logger.info("Request completed")

    print("\n" + "="*60)
    print("Example 4: Metrics Logging")
    print("="*60)

    metrics_logger = MetricsLogger(logging.getLogger("metrics"))

    # Log query metrics
    metrics_logger.log_query_metrics(
        request_id="req_001",
        query_length=50,
        context_tokens=2000,
        response_tokens=500,
        model="gpt-4-turbo",
        cost=0.0125,
        latency_ms=1234.5,
        cached=False,
        quality_score=0.87
    )

    # Log optimization metrics
    metrics_logger.log_optimization_metrics(
        request_id="req_001",
        original_tokens=5000,
        optimized_tokens=2000,
        compression_ratio=0.4,
        strategy="hybrid_compression"
    )

    # Log cache hit
    metrics_logger.log_cache_metrics(
        request_id="req_002",
        cache_hit=True,
        cache_key="cache_key_abc123"
    )

    # Log error
    metrics_logger.log_error_metrics(
        request_id="req_003",
        error_type="RateLimitError",
        error_message="Rate limit exceeded",
        recoverable=True
    )

    print("\n✓ Logging examples complete!")
    print("\n💡 In production, these logs can be:")
    print("  • Sent to Elasticsearch for analysis")
    print("  • Streamed to CloudWatch Logs")
    print("  • Ingested by Datadog/New Relic")
    print("  • Analyzed with Grafana Loki")
