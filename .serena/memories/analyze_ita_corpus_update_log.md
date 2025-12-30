# analyze_ita_corpus.py UoWパターン対応 更新ログ

## 修正日時
2025-12-27

## 変更内容

### 1. インポート変更
**変更前:**
```python
from src.infrastructure.database.duckdb_lyric_token_repository import (
    DuckDBLyricTokenRepository,
)
from src.infrastructure.database.duckdb_lyrics_repository import DuckDBLyricsRepository
from src.infrastructure.database.duckdb_match_repository import DuckDBMatchRepository
```

**変更後:**
```python
from src.infrastructure.database.duckdb_unit_of_work import DuckDBUnitOfWork
```

理由: UoWパターン導入により、個別リポジトリではなくDuckDBUnitOfWorkを使用

### 2. analyze_corpus関数の修正

#### 設定・依存関係初期化
- NlpServiceのみを個別初期化（各プロセスで必要）
- Unit of Workを初期化してコンテキストマネージャで使用
- リポジトリ初期化がUnitOfWork内で自動実行

**変更前:**
```python
settings = Settings(db_path=db_path)
nlp_service = SpacyNlpService(model_name=settings.nlp_model)
lyric_token_repository = DuckDBLyricTokenRepository(db_path=db_path)
match_repository = DuckDBMatchRepository(db_path=db_path)
```

**変更後:**
```python
settings = Settings(db_path=db_path)
nlp_service = SpacyNlpService(model_name=settings.nlp_model)
unit_of_work = DuckDBUnitOfWork(db_path=db_path)

with unit_of_work:
    # Use caseはここで初期化
```

#### Use Case初期化の変更

**MatchTextUseCase:**
```python
# 変更前
match_use_case = MatchTextUseCase(
    nlp_service=nlp_service,
    lyric_token_repository=lyric_token_repository,
    match_repository=match_repository,
    max_mora_length=settings.max_mora_length,
)

# 変更後
match_use_case = MatchTextUseCase(
    nlp_service=nlp_service,
    unit_of_work=unit_of_work,
    max_mora_length=settings.max_mora_length,
)
```

**QueryResultsUseCase:**
```python
# 変更前
query_use_case = QueryResultsUseCase(
    match_repository=match_repository,
    lyric_token_repository=lyric_token_repository,
)

# 変更後
query_use_case = QueryResultsUseCase(
    unit_of_work=unit_of_work,
)
```

**ListLyricsCorporaUseCase:**
```python
# 変更前
corpora_use_case = ListLyricsCorporaUseCase(
    lyrics_repository=DuckDBLyricsRepository(db_path=db_path),
    lyric_token_repository=lyric_token_repository,
)

# 変更後
corpora_use_case = ListLyricsCorporaUseCase(
    unit_of_work=unit_of_work,
)
```

## 重要なポイント

1. **UnitOfWorkはコンテキストマネージャ**: `with unit_of_work:` で使用しないとリポジトリにアクセスできない

2. **各プロセス内での初期化**: マルチプロセス実行時も、各プロセス内で独立したUnitOfWorkインスタンスを作成可能

3. **トランザクション管理**: UnitOfWorkの`__exit__`で自動的にコミット/ロールバックが行われる

4. **リポジトリアクセス**: UnitOfWorkが接続を管理するため、個別のリポジトリ初期化が不要になった

## テスト対象
- [x] syntaxエラーなし
- [ ] pytest実行確認
- [ ] ruff linting確認
- [ ] 実行時エラー確認（ITAコーパスファイル必要）
