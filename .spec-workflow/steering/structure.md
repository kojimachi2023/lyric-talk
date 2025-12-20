# Project Structure

## Directory Organization

**DDD + Onion Architecture** を採用した階層構造：

```
lyric-talk/
├── src/                              # アプリ本体（Python パッケージ）
│   ├── domain/                       # Domain 層（ビジネスロジック）
│   │   ├── models/                   # エンティティ・値オブジェクト
│   │   │   ├── lyric_token.py        # 歌詞トークン（エンティティ）
│   │   │   ├── lyrics_corpus.py     # 歌詞コーパス（エンティティ）
│   │   │   ├── match_run.py         # マッチング実行（エンティティ）
│   │   │   ├── match_result.py      # マッチング結果（値オブジェクト）
│   │   │   ├── reading.py           # 読み（値オブジェクト）
│   │   │   └── mora.py              # モーラ（値オブジェクト）
│   │   ├── repositories/             # リポジトリインターフェース
│   │   │   ├── lyrics_repository.py
│   │   │   ├── lyric_token_repository.py
│   │   │   └── match_repository.py
│   │   └── services/                 # ドメインサービス
│   │       ├── matching_strategy.py  # マッチング戦略
│   │       └── nlp_service.py        # NLPサービス（抽象）
│   ├── application/                  # Application 層（ユースケース）
│   │   ├── dtos/                     # データ転送オブジェクト
│   │   │   └── token_data.py
│   │   └── use_cases/                # ユースケース
│   │       ├── register_lyrics.py    # 歌詞登録
│   │       ├── match_text.py         # テキストマッチング
│   │       └── query_results.py      # 結果照会
│   ├── infrastructure/               # Infrastructure 層（外部実装）
│   │   ├── config/
│   │   │   └── settings.py           # 設定管理
│   │   ├── database/                 # 永続化実装
│   │   │   ├── schema.py             # DB スキーマ
│   │   │   ├── duckdb_lyrics_repository.py
│   │   │   ├── duckdb_lyric_token_repository.py
│   │   │   └── duckdb_match_repository.py
│   │   └── nlp/                      # NLP 実装
│   │       └── spacy_nlp_service.py
│   └── interface/                    # Interface 層（入力アダプタ）
│       └── cli/
│           └── main.py               # CLI エントリポイント
├── tests/                            # テストコード
│   ├── unit/                         # ユニットテスト
│   │   ├── domain/
│   │   ├── application/
│   │   ├── infrastructure/
│   │   └── interface/
│   └── integration/                  # 統合テスト
│       └── test_full_pipeline.py
├── .spec-workflow/                   # spec/steering 運用
├── pyproject.toml                    # 依存/ビルド/テスト設定
├── uv.lock                           # uv ロック
└── README.md
```

## Naming Conventions

### Files

- **Python modules/packages**: `snake_case.py`
- **Packages**: `lower_snake_case/`（例: `domain/`, `application/`）
- **Tests**: `tests/test_*.py`

### Code

- **Classes/Types**: `PascalCase`
- **Functions/Methods**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`
- **Variables**: `snake_case`

## Import Patterns

### Import Order

1. Python 標準ライブラリ
2. 外部依存（例: `spacy`, `pydantic_settings`）
3. 自プロジェクト内（パッケージ）

### Module/Package Organization

- `src/` は Python パッケージとして扱う
- 同一パッケージ内では明示的な相対 import を使用（例: `from .config import settings`）
- **Domain 層は外部技術（NLP/永続化）に依存しない**
  - リポジトリは抽象インターフェースのみを定義
  - 具体実装は Infrastructure 層に配置

## Code Organization Principles

1. **Single Responsibility**: 1ファイル1責務
2. **Testability**: ユニットテスト可能な構造
3. **Dependency Rule**: 依存は外側から内側へ（Domain は最も内側）
4. **Consistency**: `ruff` による整形・lint

## Module Boundaries

### Domain 層

- エンティティ、値オブジェクト、ドメインサービス
- 純粋なビジネスロジック（外部I/Oに依存しない）
- リポジトリインターフェースを定義（実装は持たない）

### Application 層

- ユースケースの実装
- DTO（Data Transfer Object）
- トランザクション境界

### Infrastructure 層

- リポジトリの具体実装（DuckDB）
- NLP サービスの実装（spaCy + GiNZA）
- 設定管理（pydantic-settings）

### Interface 層

- CLI アダプタ
- 依存性注入の組み立て

**依存方向**: Interface → Application → Domain ← Infrastructure

## Documentation Standards

- 公開関数/クラスには docstring を記述
- エンティティ・値オブジェクトの不変性を `model_config` で明示
- 複雑なアルゴリズム（モーラ分割、マッチング戦略）にはコメントで補足

## Test Structure

- ユニットテスト: 各層ごとに分離（`tests/unit/domain/`, `tests/unit/application/` など）
- 統合テスト: `tests/integration/` 配下
- uv環境に導入されたpytest の並列実行（`-n 8`）とカバレッジ測定を有効化
- マーカー: `@pytest.mark.slow`, `@pytest.mark.integration`
