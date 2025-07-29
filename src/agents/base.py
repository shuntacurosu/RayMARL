"""
Base Agent Class

エージェントの抽象基底クラス定義
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import ray
from datetime import datetime

from ..utils.exceptions import AgentManagementError


@ray.remote
class BaseAgent(ABC):
    """
    エージェントの抽象基底クラス
    
    全てのエージェント実装はこのクラスを継承し、
    必要なメソッドを実装する必要があります。
    """
    
    def __init__(self, agent_id: str, config: Dict[str, Any]):
        """
        エージェント初期化
        
        Args:
            agent_id: エージェントの一意識別子
            config: エージェント設定辞書
        """
        self.agent_id = agent_id
        self.config = config
        self.created_at = datetime.now()
        self.last_updated = datetime.now()
        self._is_training = False
        
    @abstractmethod
    def act(self, observation: np.ndarray, epsilon: float = 0.1) -> int:
        """
        観測値に基づいてアクションを選択
        
        Args:
            observation: 環境からの観測値
            epsilon: 探索率（ε-greedy用）
            
        Returns:
            選択されたアクション
        """
        pass
    
    @abstractmethod
    def learn(self, experiences: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        経験データから学習
        
        Args:
            experiences: 学習用経験データのリスト
            
        Returns:
            学習メトリクス（loss等）
        """
        pass
    
    @abstractmethod
    def save_checkpoint(self, path: str) -> bool:
        """
        モデルチェックポイントを保存
        
        Args:
            path: 保存先パス
            
        Returns:
            保存成功フラグ
        """
        pass
    
    @abstractmethod
    def load_checkpoint(self, path: str) -> bool:
        """
        モデルチェックポイントをロード
        
        Args:
            path: チェックポイントファイルパス
            
        Returns:
            ロード成功フラグ
        """
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """
        エージェントの現在状態を取得
        
        Returns:
            状態情報辞書
        """
        return {
            "agent_id": self.agent_id,
            "is_training": self._is_training,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "config": self.config
        }
    
    def set_training_mode(self, training: bool) -> None:
        """
        学習モードの設定
        
        Args:
            training: 学習モードフラグ
        """
        self._is_training = training
        self.last_updated = datetime.now()
    
    def update_config(self, new_config: Dict[str, Any]) -> None:
        """
        設定の更新
        
        Args:
            new_config: 新しい設定辞書
        """
        self.config.update(new_config)
        self.last_updated = datetime.now()
        
    def get_performance_metrics(self) -> Dict[str, float]:
        """
        パフォーマンスメトリクスを取得
        
        Returns:
            メトリクス辞書
        """
        return {
            "episodes_completed": 0,
            "average_reward": 0.0,
            "learning_rate": self.config.get("learning_rate", 0.001),
            "epsilon": self.config.get("epsilon", 0.1)
        }


class AgentStatus:
    """エージェント状態定数"""
    INITIALIZING = "initializing"
    READY = "ready" 
    TRAINING = "training"
    PAUSED = "paused"
    ERROR = "error"