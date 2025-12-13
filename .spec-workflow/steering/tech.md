# Technology Stack

## Project Type

- **Python 製 CLI ツール**（日本語歌詞を素材に、入力文を再現するためのテキストマッチング）
- 実行形態: コマンドライン実行 → JSON 出力（`output.json` など）
- 将来的な拡張候補: LLM による言い換え・候補生成（※現状のコア機能には未統合）
- 補足: **現状のリポジトリ内コードは技術検証（PoC）段階**であり、将来的に設計・構造を見直す予定があります（後述）。

## Core Technologies

### Primary Language(s)

- **Language**: Python >= 3.12
- **Runtime/Compiler**: CPython
- **Language-specific tools**:
  - 依存管理/実行: `uv`（プロジェクト方針）
  - パッケージング: `hatchling`
  - エントリポイント: `lyric-talk = "src.main:main"`（`pyproject.toml`）

### Key Dependencies/Libraries

（`pyproject.toml` の依存関係を中心に、「現状で使っているもの」と「将来拡張のために同梱しているもの」を分けて記載）

#### 現状のコア依存（実装に直接登場）

- **spaCy (>=3.7.0)**: 日本語形態素解析の基盤
- **GiNZA (>=5.2.0), ja-ginza (>=5.2.0)**: spaCy 上で日本語解析（読み情報 `Reading` 取得など）
- **pydantic (>=2.0.0), pydantic-settings (>=2.0.0)**: 設定管理（環境変数/`.env`）
- **fugashi / unidic-lite / ipadic**: 日本語トークナイザ・辞書（環境により利用）

#### 将来拡張向け依存（現状は主に拡張準備）

- **ollama**: ローカルLLM連携（将来的な言い換え・候補生成用途）

補足: リポジトリには Node.js 依存（`@pimzino/spec-workflow-mcp`, `@upstash/context7-mcp`）もありますが、これは開発ワークフロー支援（spec/steering）用途で、アプリ本体の実行には必須ではありません。

### Application Architecture

#### 現状（技術検証 / PoC）

- **シンプルな「CLI → 解析/インデックス化 → マッチング → JSON 出力」パイプライン型**
- 現状の主要モジュール:
  - `src/main.py`: CLI エントリポイント
  - `src/lyric_index.py`: 歌詞テキストを解析してインデックス構築（表層形/読み/モーラ）
  - `src/matcher.py`: 入力トークンのマッチング（優先度付きルール）
  - `src/mora.py`: 読み正規化・モーラ分割
  - `src/config.py`: 実行時設定（例: `max_mora_length`）

補足:

- 設定は `pydantic-settings` により読み込み、環境変数接頭辞は `LYRIC_TALK_`（例: `LYRIC_TALK_MAX_MORA_LENGTH`）です。
- CLI は `--lyrics`/`--lyrics-text` と `--text` を受け取り、結果を JSON ファイルへ書き出します。

#### 将来の方針（計画）

- **DDD + Onion Architecture** へ段階的に書き換える予定です。
- 目的: ドメイン知識の分離、依存方向の明確化、テスト容易性の向上。
- 想定レイヤ（例）:
  - **Domain**: エンティティ/値オブジェクト/ドメインサービス（純粋なビジネスロジック）
  - **Application**: ユースケース、入出力 DTO、トランザクション境界
  - **Infrastructure**: NLP/LLM 等の外部技術、永続化、外部I/O 実装
  - **Interface**: CLI/（将来の）API などのアダプタ

※この `tech.md` では「現状（PoC）」と「将来（計画）」を分けて記載し、混同しないようにします。

### Data Storage (if applicable)

- **Primary storage**: なし（現状はメモリ上で処理）
- **Output**: JSON ファイル（例: `output.json`）
- **Future option**: 必要になった場合に永続化層（DB/ファイル）を導入

### External Integrations (if applicable)

- 現状は基本的に **ローカル完結**（ネットワーク必須の外部 API 連携なし）
- 将来的に（必要になった場合）:
  - **LLM**: `ollama`（ローカルLLMサーバ）

### Monitoring & Dashboard Technologies (if applicable)

- **Dashboard Framework**: なし（CLI ログ出力が中心）
- **Real-time Communication**: なし
- **State Management**: ファイル出力（JSON）

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

- 形態素解析（spaCy + GiNZA）がボトルネックになり得るため、入力サイズ（歌詞行数/トークン数）に応じた実用的な処理時間を維持する
- マッチングは説明可能性を優先しつつ、将来的に候補探索の最適化（キャッシュ/探索戦略）を検討

### Compatibility Requirements

- **Platform Support**: クロスプラットフォーム（ただし日本語モデル/辞書周りは環境依存が出やすい）
- **Dependency Versions**: `pyproject.toml` の範囲を維持

### Security & Compliance

- デフォルトはローカル処理であり、外部送信は行わない
- 入力ファイルは任意テキストのため、取り扱いはユーザー責任（権利/機密/個人情報など）

### Scalability & Reliability

- 現状は単一プロセス/メモリ内処理
- 将来的に:
  - キャッシュ
  - 永続化層（必要になった場合）

## Technical Decisions & Rationale

### Decision Log

1. **spaCy + GiNZA 採用**: 日本語の形態素解析と読み（`Reading`）取得を安定して行えるため
2. **表層形→読み→モーラの優先度付きルール**: 説明可能で、エラー原因を追いやすい構造にするため
3. **設定を pydantic-settings で管理**: 実験的パラメータ（例: `max_mora_length`）を環境変数/`.env` で安全に切り替えるため

## Known Limitations

- `ja_ginza` のロード時間が初回実行の体感を左右する
- 現状のマッチングは「最初に見つかった候補を採用」する場面があり、最適解探索（全体最適）は未実装
- 言い換え（LLM）などの拡張は現状未統合（今後の拡張領域）
