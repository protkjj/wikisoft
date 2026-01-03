"""
통합 로깅 시스템

체계적인 로깅을 위한 구조화된 로거:
- JSON 형식 로그 (분석 용이)
- 컨텍스트 정보 자동 추가
- 성능 메트릭 수집
"""
import logging
import json
import time
from datetime import datetime
from typing import Any, Dict, Optional
from functools import wraps
from contextlib import contextmanager
import traceback
import os


# 로그 레벨 설정
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = os.getenv("LOG_FORMAT", "json")  # json 또는 text


class StructuredLogger:
    """구조화된 로거"""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(name)
        self._setup_handler()
        
        # 컨텍스트 정보
        self._context: Dict[str, Any] = {}
    
    def _setup_handler(self):
        """핸들러 설정"""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
            
            if LOG_FORMAT == "json":
                handler.setFormatter(JsonFormatter())
            else:
                handler.setFormatter(logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                ))
            
            self.logger.addHandler(handler)
            self.logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
    
    def bind(self, **kwargs) -> 'StructuredLogger':
        """컨텍스트 바인딩 (체이닝)"""
        new_logger = StructuredLogger(self.name)
        new_logger._context = {**self._context, **kwargs}
        return new_logger
    
    def _log(self, level: str, message: str, **kwargs):
        """내부 로깅 메서드"""
        extra = {
            "timestamp": datetime.utcnow().isoformat(),
            "logger_name": self.name,
            **self._context,
            **kwargs
        }
        
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(message, extra={"structured": extra})
    
    def info(self, message: str, **kwargs):
        self._log("info", message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        self._log("warning", message, **kwargs)
    
    def error(self, message: str, **kwargs):
        self._log("error", message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        self._log("debug", message, **kwargs)
    
    def exception(self, message: str, **kwargs):
        kwargs["traceback"] = traceback.format_exc()
        self._log("error", message, **kwargs)


class JsonFormatter(logging.Formatter):
    """JSON 형식 로그 포매터"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # 구조화된 데이터 추가
        if hasattr(record, "structured"):
            log_data.update(record.structured)
        
        return json.dumps(log_data, ensure_ascii=False, default=str)


class MetricsCollector:
    """성능 메트릭 수집기"""
    
    def __init__(self):
        self._metrics: Dict[str, list] = {}
    
    def record(self, metric_name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """메트릭 기록"""
        if metric_name not in self._metrics:
            self._metrics[metric_name] = []
        
        self._metrics[metric_name].append({
            "value": value,
            "timestamp": datetime.utcnow().isoformat(),
            "tags": tags or {}
        })
        
        # 최근 1000개만 유지
        if len(self._metrics[metric_name]) > 1000:
            self._metrics[metric_name] = self._metrics[metric_name][-1000:]
    
    def get_summary(self, metric_name: str) -> Dict[str, Any]:
        """메트릭 요약"""
        if metric_name not in self._metrics or not self._metrics[metric_name]:
            return {"count": 0}
        
        values = [m["value"] for m in self._metrics[metric_name]]
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "last": values[-1]
        }
    
    def get_all_summaries(self) -> Dict[str, Dict[str, Any]]:
        """모든 메트릭 요약"""
        return {name: self.get_summary(name) for name in self._metrics}


# 전역 인스턴스
_loggers: Dict[str, StructuredLogger] = {}
_metrics = MetricsCollector()


def get_logger(name: str) -> StructuredLogger:
    """로거 인스턴스 가져오기"""
    if name not in _loggers:
        _loggers[name] = StructuredLogger(name)
    return _loggers[name]


def get_metrics() -> MetricsCollector:
    """메트릭 수집기 가져오기"""
    return _metrics


@contextmanager
def log_operation(logger: StructuredLogger, operation: str, **kwargs):
    """
    작업 로깅 컨텍스트 매니저
    
    사용법:
        with log_operation(logger, "parse_file", filename="test.xlsx"):
            # 작업 수행
            pass
    """
    start_time = time.time()
    logger.info(f"{operation}_started", **kwargs)
    
    try:
        yield
        duration = time.time() - start_time
        logger.info(
            f"{operation}_completed",
            duration_ms=round(duration * 1000, 2),
            **kwargs
        )
        _metrics.record(f"{operation}_duration_ms", duration * 1000)
        _metrics.record(f"{operation}_success", 1)
    
    except Exception as e:
        duration = time.time() - start_time
        logger.exception(
            f"{operation}_failed",
            duration_ms=round(duration * 1000, 2),
            error=str(e),
            **kwargs
        )
        _metrics.record(f"{operation}_duration_ms", duration * 1000)
        _metrics.record(f"{operation}_failure", 1)
        raise


def log_function(logger_name: str = None):
    """
    함수 로깅 데코레이터
    
    사용법:
        @log_function("api")
        def my_function(arg1, arg2):
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            name = logger_name or func.__module__
            logger = get_logger(name)
            
            with log_operation(logger, func.__name__):
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


# 편의 함수
def info(message: str, **kwargs):
    get_logger("app").info(message, **kwargs)

def warning(message: str, **kwargs):
    get_logger("app").warning(message, **kwargs)

def error(message: str, **kwargs):
    get_logger("app").error(message, **kwargs)

def debug(message: str, **kwargs):
    get_logger("app").debug(message, **kwargs)
