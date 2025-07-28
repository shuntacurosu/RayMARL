# Project Structure

## Root Directory Organization
```
ray_ma_ddqn/
├── .claude/                    # Claude Code framework
│   └── commands/               # カスタムスラッシュコマンド
├── .kiro/                      # Kiro spec-driven development
│   ├── steering/               # プロジェクト全体のガイドライン
│   └── specs/                  # 機能仕様書
├── src/                        # メインソースコード
├── configs/                    # 設定ファイル
├── scripts/                    # 実行スクリプト
├── tests/                      # テストコード
├── experiments/                # 実験記録
├── docs/                       # ドキュメント
├── requirements.txt            # Python依存関係
├── setup.py                    # パッケージ設定
└── CLAUDE.md                   # プロジェクト管理設定
```

## Subdirectory Structures

### Source Code (`src/`)
```
src/
├── agents/                     # エージェント実装
│   ├── __init__.py
│   ├── base_agent.py          # ベースエージェントクラス
│   ├── dqn_agent.py           # DQN エージェント
│   └── multi_agent.py         # Multi-Agent システム
├── networks/                   # ニューラルネットワーク
│   ├── __init__.py
│   ├── dqn_network.py         # DQN ネットワーク
│   └── target_network.py      # ターゲットネットワーク
├── environments/               # 環境ラッパー
│   ├── __init__.py
│   ├── gym_wrapper.py         # Gymnasium ラッパー
│   └── pettingzoo_wrapper.py  # PettingZoo ラッパー
├── replay/                     # Experience Replay
│   ├── __init__.py
│   ├── replay_buffer.py       # リプレイバッファ
│   └── prioritized_replay.py  # 優先度付きリプレイ
├── distributed/                # 分散実行
│   ├── __init__.py
│   ├── ray_workers.py         # Ray ワーカー
│   └── parameter_server.py    # パラメータサーバー
├── utils/                      # ユーティリティ
│   ├── __init__.py
│   ├── config.py              # 設定管理
│   ├── logging.py             # ログ機能
│   └── metrics.py             # 評価指標
└── __init__.py
```

### Configuration (`configs/`)
```
configs/
├── default.yaml               # デフォルト設定
├── environments/              # 環境固有設定
│   ├── atari.yaml
│   └── continuous.yaml
├── algorithms/                # アルゴリズム設定
│   ├── dqn.yaml
│   └── double_dqn.yaml
└── distributed/               # 分散設定
    └── ray_cluster.yaml
```

## Code Organization Patterns

### Agent Architecture
- **Composition over Inheritance**: エージェントは複数のコンポーネントを組み合わせて構築
- **Strategy Pattern**: アルゴリズム（DQN variants）を戦略として実装
- **Factory Pattern**: 環境とエージェントの生成に使用

### Ray Integration
- **Remote Classes**: `@ray.remote` デコレータでワーカークラスを定義
- **Remote Functions**: 並列実行する関数に `@ray.remote` を適用
- **Object Store**: 大きなデータ（Experience Buffer）は Ray Object Store で共有

## File Naming Conventions
- **Python Files**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions/Variables**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`
- **Config Files**: `kebab-case.yaml`
- **Test Files**: `test_*.py`

## Import Organization
```python
# 標準ライブラリ
import os
import sys
from typing import Dict, List, Optional

# サードパーティライブラリ
import numpy as np
import torch
import ray

# プロジェクト内インポート
from src.agents.base_agent import BaseAgent
from src.utils.config import Config
```

## Key Architectural Principles

### Separation of Concerns
- **Agent Logic**: 意思決定とポリシー更新
- **Environment Interaction**: 環境との通信とデータ収集
- **Network Management**: モデルの構築と更新
- **Data Management**: Experience の保存と管理

### Scalability Design
- **Horizontal Scaling**: ワーカー数に比例したスケーリング
- **Resource Management**: Ray による効率的なリソース配分
- **Memory Efficiency**: 大きなバッファの共有とガベージコレクション

### Configuration Management
- **YAML-based**: 階層的で読みやすい設定ファイル
- **Environment Overrides**: 環境変数での設定上書き
- **Validation**: Pydantic 等による設定値検証

### Error Handling
- **Graceful Degradation**: 部分的な失敗でもシステム継続
- **Logging**: 構造化ログによる問題追跡
- **Monitoring**: Ray Dashboard での実行状況監視

### Testing Strategy
- **Unit Tests**: 各コンポーネントの独立テスト
- **Integration Tests**: Ray 分散環境でのテスト
- **End-to-End Tests**: 完全な学習パイプラインのテスト

## Kiro Integration
- **Specifications**: 各機能の仕様は `.kiro/specs/` で管理
- **Approval Workflow**: 要求仕様 → 設計 → タスク → 実装の順序
- **Japanese Documentation**: プロジェクト内文書は日本語で記述