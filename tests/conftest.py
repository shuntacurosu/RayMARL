"""
Pytest Configuration and Fixtures

AdaptiveMA システム用のテスト設定とフィクスチャ定義
"""

import pytest
import ray
import numpy as np
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Generator
import os
import sys

# Add src to Python path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.utils.exceptions import AdaptiveMAException
from src.utils.validation import Experience, ValidationResult


@pytest.fixture(scope="session")
def ray_cluster():
    """
    Ray cluster fixture for distributed testing
    
    セッション全体で共有されるRayクラスターを提供
    """
    # Initialize Ray for testing
    if not ray.is_initialized():
        ray.init(
            num_cpus=2,  # Limit CPUs for testing
            num_gpus=0,  # No GPU by default for tests
            local_mode=False,  # Use actual Ray cluster for testing
            ignore_reinit_error=True,
            include_dashboard=False,  # Disable dashboard for testing
            log_to_driver=False  # Reduce log verbosity
        )
    
    yield ray
    
    # Cleanup after session
    if ray.is_initialized():
        ray.shutdown()


@pytest.fixture(scope="session")
def ray_local_mode():
    """
    Ray local mode fixture for unit testing
    
    単体テスト用のローカルモードRayクラスター
    """
    # Initialize Ray in local mode for unit tests
    if not ray.is_initialized():
        ray.init(
            local_mode=True,  # Local mode for deterministic testing
            ignore_reinit_error=True,
            include_dashboard=False,
            log_to_driver=False
        )
    
    yield ray
    
    if ray.is_initialized():
        ray.shutdown()


@pytest.fixture
def temp_directory():
    """
    Temporary directory fixture
    
    テスト用の一時ディレクトリを提供
    """
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_config() -> Dict[str, Any]:
    """
    Sample configuration fixture
    
    テスト用のサンプル設定を提供
    """
    return {
        "agent": {
            "learning_rate": 0.001,
            "epsilon": 0.1,
            "batch_size": 32,
            "memory_size": 10000
        },
        "environment": {
            "name": "CartPole-v1",
            "max_episode_steps": 500
        },
        "distributed": {
            "num_workers": 2,
            "parameter_server_config": {
                "update_frequency": 10
            }
        },
        "validation": {
            "thresholds": {
                "reward_min": -1000.0,
                "reward_max": 1000.0,
                "quality_threshold": 0.5
            }
        }
    }


@pytest.fixture
def sample_experience() -> Experience:
    """
    Sample experience fixture
    
    テスト用のサンプル経験データを提供
    """
    return Experience(
        state=np.array([0.1, 0.2, 0.3, 0.4]),
        action=1,
        reward=1.0,
        next_state=np.array([0.2, 0.3, 0.4, 0.5]),
        done=False,
        agent_id="test_agent_001",
        timestamp=None,  # Will be auto-generated
        priority=1.0
    )


@pytest.fixture
def sample_experiences(sample_experience) -> Generator[Experience, None, None]:
    """
    Multiple sample experiences fixture
    
    複数のサンプル経験データを提供
    """
    experiences = []
    for i in range(10):
        exp = Experience(
            state=np.random.rand(4),
            action=np.random.randint(0, 2),
            reward=np.random.uniform(-1, 1),
            next_state=np.random.rand(4),
            done=np.random.random() < 0.1,  # 10% chance of terminal
            agent_id=f"test_agent_{i:03d}",
            timestamp=None,
            priority=np.random.uniform(0.5, 2.0)
        )
        experiences.append(exp)
    
    yield experiences


@pytest.fixture
def mock_environment():
    """
    Mock environment fixture
    
    テスト用のモック環境を提供
    """
    class MockEnvironment:
        def __init__(self):
            self.observation_space = type('Space', (), {'shape': (4,), 'low': -1, 'high': 1})()
            self.action_space = type('Space', (), {'n': 2})()
            self.current_step = 0
            
        def reset(self):
            self.current_step = 0
            return np.random.rand(4), {}
        
        def step(self, action):
            self.current_step += 1
            obs = np.random.rand(4)
            reward = np.random.uniform(-1, 1)
            terminated = self.current_step >= 100
            truncated = False
            info = {"step": self.current_step}
            return obs, reward, terminated, truncated, info
        
        def close(self):
            pass
            
        def render(self, mode="human"):
            return None
    
    return MockEnvironment()


@pytest.fixture
def agent_config() -> Dict[str, Any]:
    """
    Agent configuration fixture
    
    エージェント設定用フィクスチャ
    """
    return {
        "agent_id": "test_agent_001",
        "learning_rate": 0.001,
        "epsilon": 0.1,
        "epsilon_decay": 0.995,
        "epsilon_min": 0.01,
        "batch_size": 32,
        "memory_size": 10000,
        "target_update_frequency": 100,
        "network_config": {
            "hidden_layers": [64, 64],
            "activation": "relu",
            "dropout": 0.1
        }
    }


@pytest.fixture
def environment_config() -> Dict[str, Any]:
    """
    Environment configuration fixture
    
    環境設定用フィクスチャ
    """
    return {
        "name": "CartPole-v1",
        "adapter_type": "gymnasium",
        "render_mode": None,
        "max_episode_steps": 500,
        "reward_threshold": 475.0,
        "preprocessing": {
            "normalize_observations": True,
            "clip_rewards": False
        }
    }


# Custom pytest markers
pytest_plugins = []


def pytest_configure(config):
    """Pytest configuration hook"""
    # Register custom markers
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests") 
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "slow: Slow tests")
    config.addinivalue_line("markers", "ray: Tests requiring Ray")
    config.addinivalue_line("markers", "gpu: Tests requiring GPU")


def pytest_collection_modifyitems(config, items):
    """
    Modify test collection to add markers automatically
    
    テスト自動分類とマーカー付与
    """
    for item in items:
        # Add ray marker to tests that use ray fixtures
        if "ray_cluster" in item.fixturenames or "ray_local_mode" in item.fixturenames:
            item.add_marker(pytest.mark.ray)
        
        # Add integration marker to tests in integration directory
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        
        # Add e2e marker to tests in e2e directory
        if "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
        
        # Add unit marker to tests in unit directory
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)