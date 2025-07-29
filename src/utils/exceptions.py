"""
Custom Exception Hierarchy

AdaptiveMA システム用カスタム例外定義
"""


class AdaptiveMAException(Exception):
    """
    AdaptiveMA システムの基底例外クラス
    
    全てのシステム固有例外はこのクラスを継承する
    """
    
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "ADAPTIVE_MA_ERROR"
        self.details = details or {}
    
    def __str__(self) -> str:
        base_msg = f"[{self.error_code}] {self.message}"
        if self.details:
            base_msg += f" | Details: {self.details}"
        return base_msg
    
    def to_dict(self) -> dict:
        """例外情報を辞書形式で返す"""
        return {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details
        }


class AgentManagementError(AdaptiveMAException):
    """
    エージェント管理関連エラー
    
    エージェントの追加、削除、スケーリング等で発生する例外
    """
    
    def __init__(self, message: str, agent_id: str = None, **kwargs):
        super().__init__(message, error_code="AGENT_MANAGEMENT_ERROR", **kwargs)
        if agent_id:
            self.details["agent_id"] = agent_id


class EnvironmentAdapterError(AdaptiveMAException):
    """
    環境アダプタ関連エラー
    
    環境の初期化、リセット、ステップ実行等で発生する例外
    """
    
    def __init__(self, message: str, env_name: str = None, **kwargs):
        super().__init__(message, error_code="ENVIRONMENT_ADAPTER_ERROR", **kwargs)
        if env_name:
            self.details["env_name"] = env_name


class DataValidationError(AdaptiveMAException):
    """
    データ検証関連エラー
    
    学習データの検証、異常値検出、整合性チェック等で発生する例外
    """
    
    def __init__(self, message: str, validation_type: str = None, **kwargs):
        super().__init__(message, error_code="DATA_VALIDATION_ERROR", **kwargs)
        if validation_type:
            self.details["validation_type"] = validation_type


class DistributedCoordinationError(AdaptiveMAException):
    """
    分散協調関連エラー
    
    Ray cluster の管理、ワーカー障害、負荷分散等で発生する例外
    """
    
    def __init__(self, message: str, worker_id: str = None, **kwargs):
        super().__init__(message, error_code="DISTRIBUTED_COORDINATION_ERROR", **kwargs)
        if worker_id:
            self.details["worker_id"] = worker_id


class NetworkError(AdaptiveMAException):
    """
    ニューラルネットワーク関連エラー
    
    DQN の初期化、学習、推論等で発生する例外
    """
    
    def __init__(self, message: str, network_type: str = None, **kwargs):
        super().__init__(message, error_code="NETWORK_ERROR", **kwargs)
        if network_type:
            self.details["network_type"] = network_type


class ConfigurationError(AdaptiveMAException):
    """
    設定関連エラー
    
    Hydra 設定の読み込み、設定値の検証等で発生する例外
    """
    
    def __init__(self, message: str, config_key: str = None, **kwargs):
        super().__init__(message, error_code="CONFIGURATION_ERROR", **kwargs)
        if config_key:
            self.details["config_key"] = config_key


class ExperienceBufferError(AdaptiveMAException):
    """
    Experience Buffer 関連エラー
    
    経験データの保存、取得、サンプリング等で発生する例外
    """
    
    def __init__(self, message: str, buffer_type: str = None, **kwargs):
        super().__init__(message, error_code="EXPERIENCE_BUFFER_ERROR", **kwargs)
        if buffer_type:
            self.details["buffer_type"] = buffer_type


class MetricsError(AdaptiveMAException):
    """
    メトリクス関連エラー
    
    性能監視、メトリクス収集、レポート生成等で発生する例外
    """
    
    def __init__(self, message: str, metric_name: str = None, **kwargs):
        super().__init__(message, error_code="METRICS_ERROR", **kwargs)
        if metric_name:
            self.details["metric_name"] = metric_name


class OfflineDataError(AdaptiveMAException):
    """
    オフラインデータ関連エラー
    
    オフライン学習データの収集、処理、保存等で発生する例外
    """
    
    def __init__(self, message: str, data_source: str = None, **kwargs):
        super().__init__(message, error_code="OFFLINE_DATA_ERROR", **kwargs)
        if data_source:
            self.details["data_source"] = data_source


# Convenience functions for common error patterns

def raise_agent_not_found(agent_id: str) -> None:
    """エージェントが見つからない場合の例外を発生"""
    raise AgentManagementError(
        f"Agent with ID '{agent_id}' not found",
        agent_id=agent_id,
        details={"error_type": "NOT_FOUND"}
    )


def raise_environment_not_registered(env_name: str) -> None:
    """環境が登録されていない場合の例外を発生"""
    raise EnvironmentAdapterError(
        f"Environment '{env_name}' is not registered",
        env_name=env_name,
        details={"error_type": "NOT_REGISTERED"}
    )


def raise_invalid_configuration(config_key: str, expected_type: str, actual_value: any) -> None:
    """無効な設定値の場合の例外を発生"""
    raise ConfigurationError(
        f"Invalid configuration for '{config_key}': expected {expected_type}, got {type(actual_value).__name__}",
        config_key=config_key,
        details={
            "expected_type": expected_type,
            "actual_type": type(actual_value).__name__,
            "actual_value": str(actual_value)
        }
    )