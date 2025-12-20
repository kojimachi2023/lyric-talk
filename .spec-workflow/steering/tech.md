# Technology Stack

## Project Type

- **Python 製 CLI ツール**（日本語歌詞を素材に、入力文を再現するためのテキストマッチング）
- 実行形態: コマンドライン実行 → DuckDB への永続化
- 将来的な拡張候補: LLM による言い換え・候補生成（※現状のコア機能には未統合）
- アーキテクチャ: **DDD + Onion Architecture** を採用

## Core Technologies

### Primary Language(s)

- **Language**: Python >= 3.12
- **Runtime/Compiler**: CPython
- **Language-specific tools**:
  - 依存管理/実行: `uv`
  - パッケージング: `hatchling`
  - エントリポイント: `lyric-talk = "src.interface.cli.main:main"`

### Key Dependencies/Libraries

#### コア依存

- **spaCy (>=3.7.0)**: 日本語形態素解析の基盤
- **GiNZA (>=5.2.0), ja-ginza (>=5.2.0)**: spaCy 上で日本語解析（読み情報取得）
- **pydantic (>=2.0.0), pydantic-settings (>=2.0.0)**: ドメインモデル定義と設定管理
- **DuckDB (>=1.4.3)**: 歌詞コーパス、トークン、マッチ結果の永続化
- **fugashi / unidic-lite / ipadic**: 日本語トークナイザ・辞書

#### 拡張準備

- **ollama (>=0.6.1)**: ローカルLLM連携（将来的な言い換え・候補生成用途）

### Application Architecture

**DDD + Onion Architecture** を採用した階層構造：

- **Domain 層**: エンティティ/値オブジェクト/ドメインサービス（純粋なビジネスロジック）
  - エンティティ: `LyricToken`, `LyricsCorpus`, `MatchRun`
  - 値オブジェクト: `Reading`, `Mora`, `MatchResult`
  - ドメインサービス: `MatchingStrategy`, `NlpService`（抽象）
  - リポジトリ（インターフェース定義）
  
- **Application 層**: ユースケース、入出力 DTO、トランザクション境界
  - ユースケース: `RegisterLyricsUseCase`, `MatchTextUseCase`, `QueryResultsUseCase`
  - DTO: `TokenData`
  
- **Infrastructure 層**: 外部技術の実装
  - NLP: `SpacyNlpService`（spaCy + GiNZA）
  - データベース: `DuckDBLyricsRepository`, `DuckDBLyricTokenRepository`, `DuckDBMatchRepository`
  - 設定: `Settings`（pydantic-settings、環境変数接頭辞 `LYRIC_TALK_`）
  
- **Interface 層**: CLI アダプタ
  - CLI エントリポイント: `src.interface.cli.main:main`
  - コマンド: `register`, `match`, `query`

### Data Storage

- **Primary storage**: DuckDB（`lyrics_corpus`, `lyric_tokens`, `match_runs`, `match_results` テーブル）
- **Output**: JSON ファイル（`query` コマンドの出力）
- **Schema**: `infrastructure/database/schema.py` で定義・初期化

### External Integrations

- 基本的に **ローカル完結**（ネットワーク必須の外部 API 連携なし）
- 将来的な拡張候補: `ollama`（ローカルLLMサーバ）による言い換え・候補生成

### Monitoring & Dashboard Technologies

- **CLI ログ出力**が中心
- **State Management**: DuckDB + JSON ファイル出力

## Development Environment

### Build & Development Tools

- **Build System**: `hatchling`
- **Package Management**: `uv`（テスト/静的解析の実行手順として `uv run` を採用）
- **Development workflow**:
  - `uv run ...` で実行/テスト/静的解析

### Code Quality Tools

- **Static Analysis / Lint**: `ruff`
- **Formatting**: `ruff`（`ruff check . --fix`）
- **Testing Framework**: `pytest`（`pytest-xdist` により並列実行）
- **Coverage**: `pytest-cov`

### Version Control & Collaboration

- **VCS**: Git
- **Branching Strategy**: 変更提案をブランチで行い、レビュー/マージする運用を想定
- **Code Review Process**: PR ベースでレビュー（推奨）

### Dashboard Development (if applicable)

- 本プロジェクトの steering/spec 運用では `spec-workflow-mcp` ダッシュボード（別プロセス）を利用

## Deployment & Distribution (if applicable)

- **Target Platform(s)**: Python が動く環境（Linux/macOS/Windows 想定）
- **Distribution Method**: Python パッケージ（将来的に `uvx` で環境構築不要の実行も目標）
- **Installation Requirements**:
  - Python >= 3.12
  - spaCy 日本語モデル（`ja_ginza`）が利用可能であること

## Technical Requirements & Constraints

### Performance Requirements

- 形態素解析（spaCy + GiNZA）がボトルネック
- マッチングは説明可能性を優先（全体最適探索は将来課題）
- 典型的な歌詞入力（数百〜数千トークン）で実用的な処理時間を維持

### Compatibility Requirements

- **Platform Support**: クロスプラットフォーム（ただし日本語モデル/辞書周りは環境依存が出やすい）
- **Dependency Versions**: `pyproject.toml` の範囲を維持

### Security & Compliance

- デフォルトはローカル処理であり、外部送信は行わない
- 入力ファイルは任意テキストのため、取り扱いはユーザー責任（権利/機密/個人情報など）

### Scalability & Reliability

- 単一プロセス処理
- DuckDB による永続化で過去のマッチ結果を保持
- 将来的な最適化候補: キャッシュ、並列処理

## Technical Decisions & Rationale

### Decision Log

1. **DDD + Onion Architecture 採用**: ドメイン知識の分離、依存方向の明確化、テスト容易性の向上
2. **spaCy + GiNZA 採用**: 日本語の形態素解析と読み取得を安定して行えるため
3. **表層形→読み→モーラの優先度付きマッチング**: 説明可能性とエラー追跡の容易さを重視
4. **pydantic によるドメインモデル定義**: 型安全性とバリデーション
5. **DuckDB による永続化**: 軽量で組み込み可能、SQL による柔軟なクエリ

## Known Limitations

- `ja_ginza` のロード時間が初回実行時に影響
- マッチングは貪欲法（最初に見つかった候補を採用）で、全体最適探索は未実装
- LLM による言い換え機能は未統合
