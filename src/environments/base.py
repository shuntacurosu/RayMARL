"""
Environment Adapter Base Class

環境アダプタの抽象基底クラス定義
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
from datetime import datetime

from ..utils.exceptions import EnvironmentAdapterError


class EnvironmentAdapter(ABC):
    """
    環境アダプタの抽象基底クラス
    
    異なるRL環境（Gym、PettingZoo等）に対する
    統一インターフェースを提供
    """
    
    def __init__(self, env_name: str, config: Dict[str, Any]):
        """
        環境アダプタ初期化
        
        Args:
            env_name: 環境名
            config: 環境設定辞書
        """
        self.env_name = env_name
        self.config = config
        self.created_at = datetime.now()
        self._environment = None
        self._observation_space = None
        self._action_space = None
        
    @abstractmethod
    def create_environment(self) -> Any:
        """
        環境インスタンスを作成
        
        Returns:
            環境インスタンス
        """
        pass
    
    @abstractmethod
    def reset(self) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        環境をリセット
        
        Returns:
            初期観測値とメタ情報
        """
        pass
    
    @abstractmethod
    def step(self, action: Union[int, np.ndarray]) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        """
        環境でアクションを実行
        
        Args:
            action: 実行するアクション
            
        Returns:
            observation, reward, terminated, truncated, info
        """
        pass
    
    @abstractmethod
    def close(self) -> None:
        """
        環境を閉じる
        """
        pass
    
    @abstractmethod
    def get_observation_space(self) -> Any:
        """
        観測空間を取得
        
        Returns:
            観測空間オブジェクト
        """
        pass
    
    @abstractmethod
    def get_action_space(self) -> Any:
        """
        行動空間を取得
        
        Returns:
            行動空間オブジェクト
        """
        pass
    
    def normalize_observation(self, observation: Any) -> np.ndarray:
        """
        観測値を正規化
        
        Args:
            observation: 元の観測値
            
        Returns:
            正規化された観測値
        """
        if isinstance(observation, np.ndarray):
            return observation.astype(np.float32)
        elif isinstance(observation, (list, tuple)):
            return np.array(observation, dtype=np.float32)
        else:
            raise EnvironmentAdapterError(f"Unsupported observation type: {type(observation)}")
    
    def normalize_action(self, action: Any) -> Union[int, np.ndarray]:
        """
        アクションを正規化
        
        Args:
            action: 元のアクション
            
        Returns:
            正規化されたアクション
        """
        if isinstance(action, (int, float)):
            return int(action)
        elif isinstance(action, np.ndarray):
            return action
        else:
            raise EnvironmentAdapterError(f"Unsupported action type: {type(action)}")
    
    def get_environment_info(self) -> Dict[str, Any]:
        """
        環境情報を取得
        
        Returns:
            環境情報辞書
        """
        return {
            "env_name": self.env_name,
            "observation_space": str(self.get_observation_space()),
            "action_space": str(self.get_action_space()),
            "config": self.config,
            "created_at": self.created_at.isoformat()
        }
    
    def validate_action(self, action: Any) -> bool:
        """
        アクションの妥当性を検証
        
        Args:
            action: 検証するアクション
            
        Returns:
            妥当性フラグ
        """
        try:
            action_space = self.get_action_space()
            if hasattr(action_space, 'contains'):
                return action_space.contains(action)
            return True
        except Exception:
            return False
    
    def get_render_modes(self) -> List[str]:
        """
        利用可能な描画モードを取得
        
        Returns:
            描画モードのリスト
        """
        if self._environment and hasattr(self._environment, 'render_modes'):
            return self._environment.render_modes
        return ["human", "rgb_array"]


class EnvironmentSpec:
    """環境仕様クラス"""
    
    def __init__(self, name: str, adapter_class: str, config: Dict[str, Any]):
        self.name = name
        self.adapter_class = adapter_class
        self.config = config
        self.registered_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "adapter_class": self.adapter_class,
            "config": self.config,
            "registered_at": self.registered_at.isoformat()
        }