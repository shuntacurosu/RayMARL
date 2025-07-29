"""
Metrics Collection and Monitoring

パフォーマンスメトリクス収集とモニタリング機能
"""

import time
import threading
from collections import defaultdict, deque
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import statistics
import numpy as np

from .exceptions import MetricsError
from .logging import get_logger


@dataclass
class MetricPoint:
    """単一メトリクスポイント"""
    timestamp: datetime
    value: float
    tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "value": self.value,
            "tags": self.tags
        }


@dataclass
class MetricSummary:
    """メトリクス統計サマリー"""
    name: str
    count: int
    mean: float
    std: float
    min_value: float
    max_value: float
    percentiles: Dict[int, float]  # {50: median, 95: p95, 99: p99}
    rate_per_second: float
    last_updated: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "count": self.count,
            "mean": self.mean,
            "std": self.std,
            "min": self.min_value,
            "max": self.max_value,
            "percentiles": self.percentiles,
            "rate_per_second": self.rate_per_second,
            "last_updated": self.last_updated.isoformat()
        }


class MetricsCollector:
    """
    メトリクス収集器
    
    リアルタイムでメトリクスを収集・集計
    """
    
    def __init__(self, window_size: int = 1000, retention_minutes: int = 60):
        """
        メトリクス収集器を初期化
        
        Args:
            window_size: 統計計算用のウィンドウサイズ
            retention_minutes: データ保持時間（分）
        """
        self.window_size = window_size
        self.retention_duration = timedelta(minutes=retention_minutes)
        
        # Thread-safe storage
        self._lock = threading.RLock()
        self._metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=window_size))
        self._counters: Dict[str, int] = defaultdict(int)
        self._gauges: Dict[str, float] = defaultdict(float)
        self._timers: Dict[str, List[float]] = defaultdict(list)
        
        # Last cleanup time
        self._last_cleanup = datetime.now()
        
        self.logger = get_logger("adaptive_ma.metrics")
    
    def record_counter(self, name: str, increment: int = 1, tags: Dict[str, str] = None) -> None:
        """
        カウンターメトリクスを記録
        
        Args:
            name: メトリクス名
            increment: 増分値
            tags: タグ辞書
        """
        with self._lock:
            full_name = self._build_metric_name(name, tags)
            self._counters[full_name] += increment
            
            point = MetricPoint(
                timestamp=datetime.now(),
                value=increment,
                tags=tags or {}
            )
            self._metrics[full_name].append(point)
            
        self._maybe_cleanup()
    
    def record_gauge(self, name: str, value: float, tags: Dict[str, str] = None) -> None:
        """
        ゲージメトリクスを記録
        
        Args:
            name: メトリクス名
            value: 値
            tags: タグ辞書
        """
        with self._lock:
            full_name = self._build_metric_name(name, tags)
            self._gauges[full_name] = value
            
            point = MetricPoint(
                timestamp=datetime.now(),
                value=value,
                tags=tags or {}
            )
            self._metrics[full_name].append(point)
            
        self._maybe_cleanup()
    
    def record_timer(self, name: str, duration: float, tags: Dict[str, str] = None) -> None:
        """
        タイマーメトリクスを記録
        
        Args:
            name: メトリクス名
            duration: 実行時間（秒）
            tags: タグ辞書
        """
        with self._lock:
            full_name = self._build_metric_name(name, tags)
            self._timers[full_name].append(duration)
            
            point = MetricPoint(
                timestamp=datetime.now(),
                value=duration,
                tags=tags or {}
            )
            self._metrics[full_name].append(point)
            
        self._maybe_cleanup()
    
    def record_histogram(self, name: str, value: float, tags: Dict[str, str] = None) -> None:
        """
        ヒストグラムメトリクスを記録
        
        Args:
            name: メトリクス名
            value: 値
            tags: タグ辞書
        """
        # ヒストグラムは現在タイマーと同じ実装
        self.record_timer(name, value, tags)
    
    def get_summary(self, name: str, tags: Dict[str, str] = None) -> Optional[MetricSummary]:
        """
        メトリクスサマリーを取得
        
        Args:
            name: メトリクス名
            tags: タグ辞書
            
        Returns:
            メトリクスサマリー
        """
        with self._lock:
            full_name = self._build_metric_name(name, tags)
            if full_name not in self._metrics:
                return None
            
            points = list(self._metrics[full_name])
            if not points:
                return None
            
            values = [p.value for p in points]
            
            # Calculate statistics
            count = len(values)
            mean_val = statistics.mean(values)
            std_val = statistics.stdev(values) if count > 1 else 0.0
            min_val = min(values)
            max_val = max(values)
            
            # Calculate percentiles
            percentiles = {}
            if count > 0:
                percentiles[50] = np.percentile(values, 50)
                percentiles[95] = np.percentile(values, 95)
                percentiles[99] = np.percentile(values, 99)
            
            # Calculate rate (points per second)
            if count > 1:
                time_span = (points[-1].timestamp - points[0].timestamp).total_seconds()
                rate = count / time_span if time_span > 0 else 0.0
            else:
                rate = 0.0
            
            return MetricSummary(
                name=name,
                count=count,
                mean=mean_val,
                std=std_val,
                min_value=min_val,
                max_value=max_val,
                percentiles=percentiles,
                rate_per_second=rate,
                last_updated=points[-1].timestamp
            )
    
    def get_all_summaries(self) -> Dict[str, MetricSummary]:
        """
        全メトリクスサマリーを取得
        
        Returns:
            メトリクス名をキーとしたサマリー辞書
        """
        summaries = {}
        with self._lock:
            for full_name in self._metrics:
                # Extract base name from full name
                base_name = full_name.split("{")[0] if "{" in full_name else full_name
                summary = self.get_summary(base_name)
                if summary:
                    summaries[full_name] = summary
        return summaries
    
    def reset_metric(self, name: str, tags: Dict[str, str] = None) -> None:
        """
        メトリクスをリセット
        
        Args:
            name: メトリクス名
            tags: タグ辞書
        """
        with self._lock:
            full_name = self._build_metric_name(name, tags)
            if full_name in self._metrics:
                self._metrics[full_name].clear()
            if full_name in self._counters:
                self._counters[full_name] = 0
            if full_name in self._gauges:
                del self._gauges[full_name]
            if full_name in self._timers:
                self._timers[full_name].clear()
    
    def reset_all(self) -> None:
        """全メトリクスをリセット"""
        with self._lock:
            self._metrics.clear()
            self._counters.clear()
            self._gauges.clear()
            self._timers.clear()
    
    def _build_metric_name(self, name: str, tags: Dict[str, str] = None) -> str:
        """
        タグ付きメトリクス名を構築
        
        Args:
            name: ベースメトリクス名
            tags: タグ辞書
            
        Returns:
            完全なメトリクス名
        """
        if not tags:
            return name
        
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}{{{tag_str}}}"
    
    def _maybe_cleanup(self) -> None:
        """古いデータの定期的なクリーンアップ"""
        now = datetime.now()
        if now - self._last_cleanup > timedelta(minutes=5):  # Clean every 5 minutes
            self._cleanup_old_data(now)
            self._last_cleanup = now
    
    def _cleanup_old_data(self, current_time: datetime) -> None:
        """
        保持期間を超えた古いデータを削除
        
        Args:
            current_time: 現在時刻
        """
        cutoff_time = current_time - self.retention_duration
        
        with self._lock:
            for metric_name, points in self._metrics.items():
                # Remove old points
                while points and points[0].timestamp < cutoff_time:
                    points.popleft()


class MetricsReporter:
    """
    メトリクスレポーター
    
    定期的にメトリクスを出力・送信
    """
    
    def __init__(self, collector: MetricsCollector, report_interval: int = 60):
        """
        レポーター初期化
        
        Args:
            collector: メトリクス収集器
            report_interval: レポート間隔（秒）
        """
        self.collector = collector
        self.report_interval = report_interval
        self.logger = get_logger("adaptive_ma.metrics.reporter")
        
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._callbacks: List[Callable[[Dict[str, MetricSummary]], None]] = []
    
    def add_callback(self, callback: Callable[[Dict[str, MetricSummary]], None]) -> None:
        """
        レポートコールバックを追加
        
        Args:
            callback: コールバック関数
        """
        self._callbacks.append(callback)
    
    def start(self) -> None:
        """レポーターを開始"""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._report_loop, daemon=True)
        self._thread.start()
        self.logger.info("Metrics reporter started", report_interval=self.report_interval)
    
    def stop(self) -> None:
        """レポーターを停止"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5.0)
        self.logger.info("Metrics reporter stopped")
    
    def _report_loop(self) -> None:
        """レポートループ"""
        while self._running:
            try:
                summaries = self.collector.get_all_summaries()
                if summaries:
                    self._generate_report(summaries)
                    
                    # Call registered callbacks
                    for callback in self._callbacks:
                        try:
                            callback(summaries)
                        except Exception as e:
                            self.logger.error(f"Metrics callback error: {e}")
                
                time.sleep(self.report_interval)
                
            except Exception as e:
                self.logger.error(f"Metrics report error: {e}")
                time.sleep(1.0)  # Brief pause before retry
    
    def _generate_report(self, summaries: Dict[str, MetricSummary]) -> None:
        """
        レポートを生成
        
        Args:
            summaries: メトリクスサマリー辞書
        """
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "metrics_count": len(summaries),
            "summaries": {name: summary.to_dict() for name, summary in summaries.items()}
        }
        
        self.logger.info("Metrics report generated", **report_data)


# Global metrics collector
_global_collector: Optional[MetricsCollector] = None
_global_reporter: Optional[MetricsReporter] = None


def get_metrics_collector() -> MetricsCollector:
    """グローバルメトリクス収集器を取得"""
    global _global_collector
    if _global_collector is None:
        _global_collector = MetricsCollector()
    return _global_collector


def start_metrics_reporting(report_interval: int = 60) -> None:
    """グローバルメトリクスレポートを開始"""
    global _global_reporter
    if _global_reporter is None:
        collector = get_metrics_collector()
        _global_reporter = MetricsReporter(collector, report_interval)
        _global_reporter.start()


def stop_metrics_reporting() -> None:
    """グローバルメトリクスレポートを停止"""
    global _global_reporter
    if _global_reporter:
        _global_reporter.stop()
        _global_reporter = None


# Convenience functions
def record_counter(name: str, increment: int = 1, **tags) -> None:
    """カウンター記録の便利関数"""
    get_metrics_collector().record_counter(name, increment, tags)


def record_gauge(name: str, value: float, **tags) -> None:
    """ゲージ記録の便利関数"""
    get_metrics_collector().record_gauge(name, value, tags)


def record_timer(name: str, duration: float, **tags) -> None:
    """タイマー記録の便利関数"""
    get_metrics_collector().record_timer(name, duration, tags)


def record_histogram(name: str, value: float, **tags) -> None:
    """ヒストグラム記録の便利関数"""
    get_metrics_collector().record_histogram(name, value, tags)