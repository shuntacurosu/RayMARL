# Technology Stack

## Architecture
分散強化学習アーキテクチャで、Ray Cluster 上で複数の学習ワーカーが並列実行される設計。Parameter Server パターンと Actor-Learner 分散アーキテクチャを組み合わせ、効率的な学習を実現します。

## Core Dependencies
- **Ray**: 分散計算フレームワーク（推奨バージョン >= 2.0）
- **PyTorch**: ディープラーニングフレームワーク
- **NumPy**: 数値計算ライブラリ
- **Gymnasium/OpenAI Gym**: 強化学習環境インターフェース
- **PettingZoo**: Multi-Agent 環境フレームワーク

## Development Environment
- **Python**: 3.8+ (Ray 2.0+ 対応)
- **CUDA**: GPU 加速用（オプション）
- **Docker**: 環境標準化用（オプション）
- **Jupyter**: 実験とプロトタイピング用

## Machine Learning Stack
- **DQN Variants**: Double DQN, Dueling DQN, Rainbow DQN 対応
- **Experience Replay**: Prioritized Experience Replay 実装
- **Neural Networks**: CNN + FC layers for state representation
- **Optimizers**: Adam, RMSprop 等の最適化アルゴリズム

## Common Commands
```bash
# 環境セットアップ
pip install -r requirements.txt

# Ray Cluster 起動
ray start --head --port=10001

# 学習実行
python scripts/train_ma_dqn.py --config configs/default.yaml

# 評価実行
python scripts/evaluate.py --checkpoint checkpoints/latest.pkl

# TensorBoard 起動
tensorboard --logdir logs/

# Ray Dashboard
# ブラウザで http://localhost:8265 にアクセス
```

## Environment Variables
- `RAY_ADDRESS`: Ray クラスタのアドレス（デフォルト: auto）
- `CUDA_VISIBLE_DEVICES`: 使用する GPU の指定
- `PYTHONPATH`: プロジェクトルートパスの設定
- `EXPERIMENT_NAME`: 実験名の指定
- `LOG_LEVEL`: ログレベル設定（DEBUG, INFO, WARNING, ERROR）

## Port Configuration
- **8265**: Ray Dashboard（Web UI）
- **10001**: Ray GCS Server（デフォルト）
- **6379**: Redis（Ray Backend）
- **6006**: TensorBoard（ログ監視）
- **8888**: Jupyter Notebook（開発用）

## Performance Considerations
- **Memory Management**: Experience Buffer のサイズ最適化
- **Parallel Workers**: CPU コア数に応じたワーカー数調整
- **GPU Utilization**: バッチサイズと GPU メモリのバランス
- **Network Bandwidth**: 分散環境でのデータ転送効率

## Testing Framework
- **pytest**: ユニットテスト
- **Ray Test Utils**: 分散テスト用ユーティリティ
- **Hypothesis**: プロパティベースドテスト
- **Coverage**: テストカバレッジ測定

## Deployment Options
- **Local**: 単一マシンでの開発・デバッグ
- **Ray Cluster**: 複数マシンでの分散実行
- **Kubernetes**: コンテナ化された本番環境
- **Cloud**: AWS/GCP での大規模実行