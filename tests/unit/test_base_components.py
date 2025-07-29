"""
Unit Tests for Base Components

基底クラスとコアコンポーネントのユニットテスト
"""

import pytest
import numpy as np
from datetime import datetime
from unittest.mock import Mock, patch

from src.utils.exceptions import (
    AdaptiveMAException, 
    AgentManagementError,
    EnvironmentAdapterError,
    DataValidationError
)
from src.utils.validation import Experience, ValidationResult


class TestAdaptiveMAException:
    """AdaptiveMAException のテストクラス"""
    
    def test_basic_exception_creation(self):
        """基本的な例外作成のテスト"""
        exc = AdaptiveMAException("Test message")
        assert exc.message == "Test message"
        assert exc.error_code == "ADAPTIVE_MA_ERROR"
        assert exc.details == {}
    
    def test_exception_with_details(self):
        """詳細情報付き例外のテスト"""
        details = {"component": "test", "value": 42}
        exc = AdaptiveMAException(
            "Test message", 
            error_code="TEST_ERROR", 
            details=details
        )
        assert exc.error_code == "TEST_ERROR"
        assert exc.details == details
    
    def test_exception_to_dict(self):
        """例外の辞書変換テスト"""
        exc = AdaptiveMAException("Test message", error_code="TEST_ERROR")
        result = exc.to_dict()
        
        expected = {
            "error_type": "AdaptiveMAException",
            "error_code": "TEST_ERROR", 
            "message": "Test message",
            "details": {}
        }
        assert result == expected


class TestAgentManagementError:
    """AgentManagementError のテストクラス"""
    
    def test_agent_error_with_agent_id(self):
        """エージェントID付きエラーのテスト"""
        exc = AgentManagementError("Agent failed", agent_id="agent_001")
        assert exc.message == "Agent failed"
        assert exc.error_code == "AGENT_MANAGEMENT_ERROR"
        assert exc.details["agent_id"] == "agent_001"


class TestExperience:
    """Experience データクラスのテストクラス"""
    
    def test_experience_creation(self, sample_experience):
        """Experience作成のテスト"""
        exp = sample_experience
        assert exp.agent_id == "test_agent_001"
        assert exp.action == 1
        assert exp.reward == 1.0
        assert exp.done == False
        assert exp.priority == 1.0
        assert isinstance(exp.timestamp, datetime)
    
    def test_experience_with_arrays(self):
        """配列を含むExperience作成のテスト"""
        state = np.array([1, 2, 3])
        next_state = np.array([2, 3, 4])
        
        exp = Experience(
            state=state,
            action=0,
            reward=0.5,
            next_state=next_state,
            done=True,
            agent_id="test_agent",
            timestamp=None
        )
        
        np.testing.assert_array_equal(exp.state, state)
        np.testing.assert_array_equal(exp.next_state, next_state)


class TestValidationResult:
    """ValidationResult データクラスのテストクラス"""
    
    def test_validation_result_creation(self):
        """ValidationResult作成のテスト"""
        result = ValidationResult(
            is_valid=True,
            quality_score=0.8,
            anomaly_flags=["outlier_detected"],
            constraint_violations=[],
            validated_at=None  # Auto-generated
        )
        
        assert result.is_valid == True
        assert result.quality_score == 0.8
        assert result.anomaly_flags == ["outlier_detected"]
        assert result.constraint_violations == []
        assert isinstance(result.validated_at, datetime)
    
    def test_validation_result_invalid(self):
        """無効なValidationResultのテスト"""
        result = ValidationResult(
            is_valid=False,
            quality_score=0.2,
            anomaly_flags=["quality_low", "consistency_error"],
            constraint_violations=["physics_violation"],
            validated_at=datetime.now()
        )
        
        assert result.is_valid == False
        assert len(result.anomaly_flags) == 2
        assert len(result.constraint_violations) == 1


@pytest.mark.unit
class TestUtilityFunctions:
    """ユーティリティ関数のテストクラス"""
    
    def test_convenience_exception_functions(self):
        """便利関数による例外発生のテスト"""
        from src.utils.exceptions import (
            raise_agent_not_found,
            raise_environment_not_registered,
            raise_invalid_configuration
        )
        
        # Agent not found test
        with pytest.raises(AgentManagementError) as exc_info:
            raise_agent_not_found("missing_agent")
        assert "missing_agent" in str(exc_info.value)
        
        # Environment not registered test
        with pytest.raises(EnvironmentAdapterError) as exc_info:
            raise_environment_not_registered("missing_env")
        assert "missing_env" in str(exc_info.value)
    
    def test_numpy_array_handling(self):
        """NumPy配列処理のテスト"""
        # Test array creation and manipulation
        state = np.random.rand(4)
        assert state.shape == (4,)
        assert state.dtype == np.float64
        
        # Test array operations
        normalized = state / np.linalg.norm(state)
        assert np.isclose(np.linalg.norm(normalized), 1.0)


@pytest.mark.integration  
class TestComponentIntegration:
    """コンポーネント統合テストクラス"""
    
    def test_exception_experience_integration(self, sample_experience):
        """例外とExperienceの統合テスト"""
        try:
            # Simulate validation error with experience
            if sample_experience.reward > 10:  # Unrealistic reward
                raise DataValidationError(
                    "Invalid reward value",
                    validation_type="reward_check",
                    details={"reward": sample_experience.reward}
                )
        except DataValidationError as e:
            # This should not raise since sample reward is 1.0
            pytest.fail("Should not raise exception for valid experience")
    
    def test_multiple_experiences_processing(self, sample_experiences):
        """複数Experience処理のテスト"""
        experiences = list(sample_experiences)
        assert len(experiences) == 10
        
        # Test batch processing simulation
        valid_experiences = []
        for exp in experiences:
            if -10 <= exp.reward <= 10:  # Simple validation
                valid_experiences.append(exp)
        
        assert len(valid_experiences) <= len(experiences)
        assert all(isinstance(exp, Experience) for exp in valid_experiences)