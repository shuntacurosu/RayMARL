"""
Logging Utilities

構造化ログとパフォーマンス監視機能
"""

import logging
import logging.handlers
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional, Union
from datetime import datetime
from contextlib import contextmanager

from .exceptions import ConfigurationError
from .config import get_config_value


class StructuredFormatter(logging.Formatter):
    """
    構造化ログフォーマッター
    
    JSON形式の構造化ログを出力
    """
    
    def __init__(self, include_metadata: bool = True):
        super().__init__()
        self.include_metadata = include_metadata
    
    def format(self, record: logging.LogRecord) -> str:
        """
        ログレコードをJSON形式にフォーマット
        
        Args:
            record: ログレコード
            
        Returns:
            JSON形式のログメッセージ
        """
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        if self.include_metadata:
            log_data.update({
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
                "thread": record.thread,
                "process": record.process,
            })
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)


class PerformanceLogger:
    """
    パフォーマンス監視ロガー
    
    実行時間とリソース使用量を監視
    """
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self._start_times: Dict[str, float] = {}
    
    @contextmanager
    def timer(self, operation_name: str, extra_fields: Dict[str, Any] = None):
        """
        実行時間測定用コンテキストマネージャー
        
        Args:
            operation_name: 操作名
            extra_fields: 追加フィールド
        """
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.log_performance(operation_name, duration, extra_fields)
    
    def start_timer(self, operation_name: str) -> None:
        """
        タイマー開始
        
        Args:
            operation_name: 操作名
        """
        self._start_times[operation_name] = time.time()
    
    def end_timer(self, operation_name: str, extra_fields: Dict[str, Any] = None) -> float:
        """
        タイマー終了
        
        Args:
            operation_name: 操作名
            extra_fields: 追加フィールド
            
        Returns:
            実行時間（秒）
        """
        if operation_name not in self._start_times:
            self.logger.warning(f"Timer for '{operation_name}' was not started")
            return 0.0
        
        duration = time.time() - self._start_times[operation_name]
        del self._start_times[operation_name]
        
        self.log_performance(operation_name, duration, extra_fields)
        return duration
    
    def log_performance(self, operation_name: str, duration: float, 
                       extra_fields: Dict[str, Any] = None) -> None:
        """
        パフォーマンスログを出力
        
        Args:
            operation_name: 操作名
            duration: 実行時間（秒）
            extra_fields: 追加フィールド
        """
        fields = {
            "operation": operation_name,
            "duration_seconds": duration,
            "duration_ms": duration * 1000,
            "performance_log": True
        }
        
        if extra_fields:
            fields.update(extra_fields)
        
        # Create log record with extra fields
        record = self.logger.makeRecord(
            self.logger.name, logging.INFO, __file__, 0, 
            f"Performance: {operation_name} completed in {duration:.3f}s",
            None, None
        )
        record.extra_fields = fields
        self.logger.handle(record)


class AdaptiveMALogger:
    """
    AdaptiveMA システム専用ロガー
    
    構造化ログとパフォーマンス監視を統合
    """
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        """
        ロガー初期化
        
        Args:
            name: ロガー名
            config: ログ設定辞書
        """
        self.name = name
        self.config = config or self._load_config()
        self.logger = self._setup_logger()
        self.performance = PerformanceLogger(self.logger)
    
    def _load_config(self) -> Dict[str, Any]:
        """設定をロード"""
        try:
            return get_config_value("logging", {})
        except Exception:
            # Fallback to default config
            return {
                "level": "INFO",
                "handlers": {
                    "console": {"enabled": True, "level": "INFO"},
                    "file": {"enabled": False}
                }
            }
    
    def _setup_logger(self) -> logging.Logger:
        """ロガーをセットアップ"""
        logger = logging.getLogger(self.name)
        logger.setLevel(getattr(logging, self.config.get("level", "INFO")))
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # Setup console handler
        console_config = self.config.get("handlers", {}).get("console", {})
        if console_config.get("enabled", True):
            self._add_console_handler(logger, console_config)
        
        # Setup file handler
        file_config = self.config.get("handlers", {}).get("file", {})
        if file_config.get("enabled", False):
            self._add_file_handler(logger, file_config)
        
        return logger
    
    def _add_console_handler(self, logger: logging.Logger, config: Dict[str, Any]) -> None:
        """コンソールハンドラーを追加"""
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(getattr(logging, config.get("level", "INFO")))
        
        if self.config.get("structured_logging", {}).get("enabled", False):
            formatter = StructuredFormatter(
                include_metadata=self.config.get("structured_logging", {}).get("include_metadata", True)
            )
        else:
            format_str = config.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            formatter = logging.Formatter(format_str)
        
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    def _add_file_handler(self, logger: logging.Logger, config: Dict[str, Any]) -> None:
        """ファイルハンドラーを追加"""
        filename = config.get("filename", "logs/adaptive_ma.log")
        log_file = Path(filename)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        max_size = config.get("max_size", 10 * 1024 * 1024)  # 10MB
        backup_count = config.get("backup_count", 5)
        
        handler = logging.handlers.RotatingFileHandler(
            filename=str(log_file),
            maxBytes=max_size,
            backupCount=backup_count
        )
        handler.setLevel(getattr(logging, config.get("level", "DEBUG")))
        
        if self.config.get("structured_logging", {}).get("enabled", False):
            formatter = StructuredFormatter(
                include_metadata=self.config.get("structured_logging", {}).get("include_metadata", True)
            )
        else:
            format_str = config.get("format", 
                "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s")
            formatter = logging.Formatter(format_str)
        
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    def debug(self, message: str, **kwargs) -> None:
        """Debug レベルログ"""
        self._log(logging.DEBUG, message, kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        """Info レベルログ"""
        self._log(logging.INFO, message, kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Warning レベルログ"""
        self._log(logging.WARNING, message, kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """Error レベルログ"""
        self._log(logging.ERROR, message, kwargs)
    
    def critical(self, message: str, **kwargs) -> None:
        """Critical レベルログ"""
        self._log(logging.CRITICAL, message, kwargs)
    
    def _log(self, level: int, message: str, extra_fields: Dict[str, Any]) -> None:
        """内部ログメソッド"""
        record = self.logger.makeRecord(
            self.logger.name, level, __file__, 0, message, None, None
        )
        if extra_fields:
            record.extra_fields = extra_fields
        self.logger.handle(record)
    
    def log_agent_event(self, agent_id: str, event: str, **kwargs) -> None:
        """エージェントイベントログ"""
        fields = {"agent_id": agent_id, "event_type": "agent_event", "event": event}
        fields.update(kwargs)
        self.info(f"Agent {agent_id}: {event}", **fields)
    
    def log_environment_event(self, env_name: str, event: str, **kwargs) -> None:
        """環境イベントログ"""
        fields = {"env_name": env_name, "event_type": "environment_event", "event": event}
        fields.update(kwargs)
        self.info(f"Environment {env_name}: {event}", **fields)
    
    def log_validation_result(self, validation_result: Dict[str, Any]) -> None:
        """データ検証結果ログ"""
        fields = {"event_type": "validation_result"}
        fields.update(validation_result)
        is_valid = validation_result.get("is_valid", False)
        quality_score = validation_result.get("quality_score", 0.0)
        
        message = f"Validation result: valid={is_valid}, quality={quality_score:.3f}"
        if is_valid:
            self.info(message, **fields)
        else:
            self.warning(message, **fields)
    
    def log_distributed_event(self, event: str, worker_id: str = None, **kwargs) -> None:
        """分散処理イベントログ"""
        fields = {"event_type": "distributed_event", "event": event}
        if worker_id:
            fields["worker_id"] = worker_id
        fields.update(kwargs)
        self.info(f"Distributed: {event}", **fields)


# Global logger registry
_loggers: Dict[str, AdaptiveMALogger] = {}


def get_logger(name: str, config: Dict[str, Any] = None) -> AdaptiveMALogger:
    """
    ロガーを取得（シングルトン）
    
    Args:
        name: ロガー名
        config: ログ設定辞書
        
    Returns:
        ロガーインスタンス
    """
    if name not in _loggers:
        _loggers[name] = AdaptiveMALogger(name, config)
    return _loggers[name]


def setup_logging(config: Dict[str, Any] = None) -> None:
    """
    グローバルログ設定をセットアップ
    
    Args:
        config: ログ設定辞書
    """
    # Set component-specific log levels
    if config and "loggers" in config:
        for logger_name, level in config["loggers"].items():
            logging.getLogger(logger_name).setLevel(getattr(logging, level))


# Convenience functions
def log_performance(operation_name: str, duration: float, logger_name: str = "adaptive_ma.performance") -> None:
    """パフォーマンスログの便利関数"""
    logger = get_logger(logger_name)
    logger.performance.log_performance(operation_name, duration)