"""
Data Validation Base Classes

データ検証の抽象基底クラス定義
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from datetime import datetime
from dataclasses import dataclass

from .exceptions import DataValidationError


@dataclass
class ValidationResult:
    """データ検証結果"""
    is_valid: bool
    quality_score: float
    anomaly_flags: List[str]
    constraint_violations: List[str]
    validated_at: datetime
    
    def __post_init__(self):
        if self.validated_at is None:
            self.validated_at = datetime.now()


@dataclass 
class Experience:
    """学習経験データ"""
    state: np.ndarray
    action: int
    reward: float
    next_state: np.ndarray
    done: bool
    agent_id: str
    timestamp: datetime
    priority: float = 1.0
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class DataValidator(ABC):
    """
    データ検証器の抽象基底クラス
    
    学習データの品質検証とバリデーション機能を提供
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        データ検証器初期化
        
        Args:
            config: 検証設定辞書
        """
        self.config = config
        self.created_at = datetime.now()
        self._validation_history: List[ValidationResult] = []
        
    @abstractmethod
    def validate_experience(self, experience: Experience) -> ValidationResult:
        """
        単一の経験データを検証
        
        Args:
            experience: 検証する経験データ
            
        Returns:
            検証結果
        """
        pass
    
    @abstractmethod
    def detect_outliers(self, data: np.ndarray, method: str = "iqr") -> List[int]:
        """
        異常値を検出
        
        Args:
            data: 検証するデータ配列
            method: 検出手法 ("iqr", "zscore", "isolation_forest")
            
        Returns:
            異常値のインデックスリスト
        """
        pass
    
    @abstractmethod
    def check_consistency(self, multi_agent_data: Dict[str, List[Experience]]) -> Dict[str, List[str]]:
        """
        マルチエージェント環境でのデータ整合性をチェック
        
        Args:
            multi_agent_data: エージェントIDをキーとした経験データ辞書
            
        Returns:
            エージェント別整合性問題リスト
        """
        pass
    
    @abstractmethod
    def apply_physical_constraints(self, state_sequence: List[np.ndarray]) -> List[bool]:
        """
        物理制約の妥当性をチェック
        
        Args:
            state_sequence: 連続する状態データ
            
        Returns:
            各状態遷移の妥当性フラグ
        """
        pass
    
    def validate_batch(self, experiences: List[Experience]) -> List[ValidationResult]:
        """
        経験データバッチを検証
        
        Args:
            experiences: 検証する経験データリスト
            
        Returns:
            検証結果リスト
        """
        results = []
        for exp in experiences:
            result = self.validate_experience(exp)
            results.append(result)
            self._validation_history.append(result)
        return results
    
    def get_validation_statistics(self) -> Dict[str, float]:
        """
        検証統計を取得
        
        Returns:
            検証統計辞書
        """
        if not self._validation_history:
            return {"total_validations": 0, "success_rate": 0.0, "average_quality": 0.0}
            
        total = len(self._validation_history)
        valid_count = sum(1 for r in self._validation_history if r.is_valid)
        avg_quality = np.mean([r.quality_score for r in self._validation_history])
        
        return {
            "total_validations": total,
            "success_rate": valid_count / total,
            "average_quality": float(avg_quality),
            "last_validation": self._validation_history[-1].validated_at.isoformat()
        }
    
    def clear_history(self) -> None:
        """検証履歴をクリア"""
        self._validation_history.clear()
    
    def set_threshold(self, threshold_name: str, value: float) -> None:
        """
        検証閾値を設定
        
        Args:
            threshold_name: 閾値名
            value: 閾値
        """
        if "thresholds" not in self.config:
            self.config["thresholds"] = {}
        self.config["thresholds"][threshold_name] = value
    
    def get_threshold(self, threshold_name: str, default: float = 0.5) -> float:
        """
        検証閾値を取得
        
        Args:
            threshold_name: 閾値名
            default: デフォルト値
            
        Returns:
            閾値
        """
        return self.config.get("thresholds", {}).get(threshold_name, default)


class ConsistencyReport:
    """整合性レポートクラス"""
    
    def __init__(self):
        self.violations: Dict[str, List[str]] = {}
        self.warnings: Dict[str, List[str]] = {}
        self.summary: Dict[str, Any] = {}
    
    def add_violation(self, agent_id: str, violation: str) -> None:
        """違反を追加"""
        if agent_id not in self.violations:
            self.violations[agent_id] = []
        self.violations[agent_id].append(violation)
    
    def add_warning(self, agent_id: str, warning: str) -> None:
        """警告を追加"""
        if agent_id not in self.warnings:
            self.warnings[agent_id] = []
        self.warnings[agent_id].append(warning)
    
    def get_total_violations(self) -> int:
        """総違反数を取得"""
        return sum(len(v) for v in self.violations.values())
    
    def get_total_warnings(self) -> int:
        """総警告数を取得"""
        return sum(len(w) for w in self.warnings.values())
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式で出力"""
        return {
            "violations": self.violations,
            "warnings": self.warnings,
            "summary": {
                "total_violations": self.get_total_violations(),
                "total_warnings": self.get_total_warnings(),
                "agents_with_violations": len(self.violations),
                "agents_with_warnings": len(self.warnings)
            }
        }