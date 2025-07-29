"""
Configuration Management System

Hydra-based hierarchical configuration management
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional, Union
from omegaconf import DictConfig, OmegaConf
import hydra
from hydra import compose, initialize_config_dir
from hydra.core.global_hydra import GlobalHydra

from .exceptions import ConfigurationError


class ConfigManager:
    """
    設定管理クラス
    
    Hydra を使用した階層的設定管理を提供
    """
    
    def __init__(self, config_dir: Union[str, Path] = None):
        """
        設定管理器を初期化
        
        Args:
            config_dir: 設定ディレクトリパス（デフォルト: ./config）
        """
        if config_dir is None:
            config_dir = Path(__file__).parent.parent.parent / "config"
        
        self.config_dir = Path(config_dir).resolve()
        self._config: Optional[DictConfig] = None
        self._initialized = False
        
        if not self.config_dir.exists():
            raise ConfigurationError(
                f"Configuration directory not found: {self.config_dir}",
                config_key="config_dir"
            )
    
    def initialize(self, config_name: str = "config", overrides: list = None) -> DictConfig:
        """
        設定を初期化
        
        Args:
            config_name: メイン設定ファイル名
            overrides: 設定オーバーライドリスト
            
        Returns:
            初期化された設定
        """
        try:
            # Clear any existing Hydra instance
            if GlobalHydra().is_initialized():
                GlobalHydra.instance().clear()
            
            # Initialize Hydra with config directory
            with initialize_config_dir(config_dir=str(self.config_dir), version_base=None):
                # Compose configuration with overrides
                cfg = compose(config_name=config_name, overrides=overrides or [])
                
                self._config = cfg
                self._initialized = True
                
                # Validate configuration
                self._validate_config(cfg)
                
                return cfg
                
        except Exception as e:
            raise ConfigurationError(f"Failed to initialize configuration: {e}")
    
    def get_config(self) -> DictConfig:
        """
        現在の設定を取得
        
        Returns:
            設定オブジェクト
        """
        if not self._initialized:
            raise ConfigurationError("Configuration not initialized. Call initialize() first.")
        return self._config
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        設定値を取得
        
        Args:
            key: 設定キー（ドット記法対応）
            default: デフォルト値
            
        Returns:
            設定値
        """
        if not self._initialized:
            raise ConfigurationError("Configuration not initialized. Call initialize() first.")
        
        try:
            return OmegaConf.select(self._config, key, default=default)
        except Exception as e:
            raise ConfigurationError(f"Failed to get config key '{key}': {e}", config_key=key)
    
    def set(self, key: str, value: Any) -> None:
        """
        設定値を更新
        
        Args:
            key: 設定キー（ドット記法対応）
            value: 新しい値
        """
        if not self._initialized:
            raise ConfigurationError("Configuration not initialized. Call initialize() first.")
        
        try:
            OmegaConf.set(self._config, key, value)
        except Exception as e:
            raise ConfigurationError(f"Failed to set config key '{key}': {e}", config_key=key)
    
    def update(self, update_dict: Dict[str, Any]) -> None:
        """
        設定を辞書で一括更新
        
        Args:
            update_dict: 更新する設定辞書
        """
        if not self._initialized:
            raise ConfigurationError("Configuration not initialized. Call initialize() first.")
        
        try:
            update_cfg = OmegaConf.create(update_dict)
            self._config = OmegaConf.merge(self._config, update_cfg)
        except Exception as e:
            raise ConfigurationError(f"Failed to update configuration: {e}")
    
    def save(self, path: Union[str, Path]) -> None:
        """
        設定をファイルに保存
        
        Args:
            path: 保存先パス
        """
        if not self._initialized:
            raise ConfigurationError("Configuration not initialized. Call initialize() first.")
        
        try:
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w') as f:
                OmegaConf.save(config=self._config, f=f)
                
        except Exception as e:
            raise ConfigurationError(f"Failed to save configuration to {path}: {e}")
    
    def load(self, path: Union[str, Path]) -> DictConfig:
        """
        設定をファイルから読み込み
        
        Args:
            path: 設定ファイルパス
            
        Returns:
            読み込まれた設定
        """
        try:
            path = Path(path)
            if not path.exists():
                raise ConfigurationError(f"Configuration file not found: {path}")
            
            cfg = OmegaConf.load(path)
            self._config = cfg
            self._initialized = True
            
            self._validate_config(cfg)
            return cfg
            
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration from {path}: {e}")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        設定を辞書形式で取得
        
        Returns:
            設定辞書
        """
        if not self._initialized:
            raise ConfigurationError("Configuration not initialized. Call initialize() first.")
        
        return OmegaConf.to_container(self._config, resolve=True)
    
    def _validate_config(self, cfg: DictConfig) -> None:
        """
        設定の妥当性を検証
        
        Args:
            cfg: 検証する設定
        """
        # Required top-level keys
        required_keys = ["system", "execution"]
        for key in required_keys:
            if key not in cfg:
                raise ConfigurationError(f"Required configuration section '{key}' is missing")
        
        # Validate system section
        if "name" not in cfg.system:
            raise ConfigurationError("system.name is required")
        
        # Validate execution section
        if "mode" not in cfg.execution:
            raise ConfigurationError("execution.mode is required")
        
        valid_modes = ["training", "evaluation", "offline_collection"]
        if cfg.execution.mode not in valid_modes:
            raise ConfigurationError(
                f"Invalid execution.mode: {cfg.execution.mode}. Must be one of {valid_modes}"
            )
        
        # Validate numeric values
        if cfg.execution.get("max_episodes", 0) <= 0:
            raise ConfigurationError("execution.max_episodes must be positive")
        
        if cfg.execution.get("max_steps_per_episode", 0) <= 0:
            raise ConfigurationError("execution.max_steps_per_episode must be positive")


class GlobalConfigManager:
    """
    グローバル設定管理シングルトン
    
    アプリケーション全体で設定を共有
    """
    
    _instance: Optional['GlobalConfigManager'] = None
    _config_manager: Optional[ConfigManager] = None
    
    def __new__(cls) -> 'GlobalConfigManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def initialize(self, config_dir: Union[str, Path] = None, 
                  config_name: str = "config", overrides: list = None) -> DictConfig:
        """
        グローバル設定を初期化
        
        Args:
            config_dir: 設定ディレクトリパス
            config_name: メイン設定ファイル名
            overrides: 設定オーバーライドリスト
            
        Returns:
            初期化された設定
        """
        self._config_manager = ConfigManager(config_dir)
        return self._config_manager.initialize(config_name, overrides)
    
    def get_manager(self) -> ConfigManager:
        """
        設定管理器を取得
        
        Returns:
            設定管理器インスタンス
        """
        if self._config_manager is None:
            raise ConfigurationError("Global configuration not initialized")
        return self._config_manager
    
    def get_config(self) -> DictConfig:
        """
        グローバル設定を取得
        
        Returns:
            設定オブジェクト
        """
        return self.get_manager().get_config()
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        グローバル設定値を取得
        
        Args:
            key: 設定キー
            default: デフォルト値
            
        Returns:
            設定値
        """
        return self.get_manager().get(key, default)


# Global configuration instance
global_config = GlobalConfigManager()


def get_config() -> DictConfig:
    """グローバル設定を取得する便利関数"""
    return global_config.get_config()


def get_config_value(key: str, default: Any = None) -> Any:
    """グローバル設定値を取得する便利関数"""
    return global_config.get(key, default)