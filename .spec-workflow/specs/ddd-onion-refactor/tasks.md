# タスクドキュメント（Tasks Document - TDD版）

## Overview

本ドキュメントは、`lyric-talk` を **DDD + Onion Architecture** に沿って再構築するための実装タスクを定義します。設計書（design.md）で示された構造に従い、**テスト駆動開発（TDD）** のアプローチで実装を進めます。

### TDD方式の実装フロー

各機能について以下の順序で実装：

1. **テスト作成（Red）**: 期待する動作を定義したテストを先に作成
2. **テスト失敗確認**: `uv run pytest` を実行して失敗することを確認
3. **実装（Green）**: テストが通るように最小限の実装を行う
4. **テスト成功確認**: `uv run pytest` を実行して成功することを確認
5. **リファクタリング（Refactor）**: 必要に応じてコードを改善

### フェーズ構成

各レイヤごとに「テスト作成 → 実装」のサイクルを回します：

1. **Domain層**: 値オブジェクト、エンティティ、Portインターフェース
2. **Infrastructure層**: Repository実装、NLP実装、DB Schema
3. **Application層**: ユースケース
4. **Interface層**: CLI
5. **統合テスト**: エンドツーエンドのテスト
6. **クリーンアップ**: 既存コード削除、ドキュメント更新

---

## Phase 1: Domain層 - 値オブジェクト（TDD）

### Task 1.1: Moraテスト作成（Red）

- [x] 1.1. Write tests for Mora value object (Red phase)
  - File: [tests/unit/domain/test_mora.py](tests/unit/domain/test_mora.py)
  - Mora値オブジェクトのテストを作成（実装前）
  - テスト内容: `Mora.split(katakana)` による拗音・促音・長音の正しい分割
  - **テスト失敗確認**: `uv run pytest tests/unit/domain/test_mora.py -v` で失敗することを確認
  - _Requirements: Requirement 2, Requirement 8 (TDD)_
  - _Prompt:
    Implement the task for spec ddd-onion-refactor, first run spec-workflow-guide to get the workflow guide then implement the task:
    Role: QA Engineer specializing in TDD and pytest | Task: Write comprehensive unit tests for Mora value object in tests/unit/domain/test_mora.py BEFORE implementing the actual code (TDD Red phase). Test: Mora(value="ト"), Mora.split("トウキョウ") -> [Mora("ト"), Mora("ウ"), Mora("キョ"), Mora("ウ")], Mora.split("ガッコウ") with 促音, Mora.split("キャー") with 長音, edge cases (empty string). Use pytest. Import: `from src.domain.models.mora import Mora` (will fail initially). | Restrictions: Write tests only, do not implement Mora yet, tests MUST fail initially | Leverage: src/mora.py for expected behavior | Success: Tests fail with ImportError or AttributeError (Red phase confirmed)
    Instructions:
    - Mark this task as in-progress [-] in tasks.md before starting
    - After test creation, run `uv run pytest tests/unit/domain/test_mora.py -v` and CONFIRM tests fail
    - Log with log-implementation tool (include: test file created, test failure confirmed)
    - Mark this task as completed [x] in tasks.md after logging

### Task 1.2: Mora実装（Green）

- [x] 1.2. Implement Mora value object (Green phase)
  - File: [src/domain/models/mora.py](src/domain/models/mora.py)
  - Mora値オブジェクトを実装（テストを通すため）
  - `Mora.split(katakana: str) -> List[Mora]` でカタカナをモーラに分割
  - pydantic BaseModel、immutable設定
  - **テスト成功確認**: `uv run pytest tests/unit/domain/test_mora.py -v` で成功することを確認
  - _Leverage: src/mora.py（既存ロジック）_
  - _Requirements: Requirement 2_
  - _Prompt:
    Implement the task for spec ddd-onion-refactor, first run spec-workflow-guide to get the workflow guide then implement the task:
    Role: Python Developer specializing in DDD and TDD | Task: Implement Mora value object in src/domain/models/mora.py to make tests pass (TDD Green phase). Use pydantic BaseModel with `value: str` field (frozen=True for immutability). Implement static method `split(katakana: str) -> List[Mora]` using regex from existing src/mora.py (拗音・促音・長音の処理). | Restrictions: Implement minimal code to pass tests, immutable (frozen=True), no external dependencies beyond pydantic | Leverage: src/mora.py (existing regex logic), tests/unit/domain/test_mora.py (requirements) | Success: All tests pass (`uv run pytest tests/unit/domain/test_mora.py -v`)
    Instructions:
    - Mark this task as in-progress [-] in tasks.md before starting
    - After implementation, run `uv run pytest tests/unit/domain/test_mora.py -v` and CONFIRM tests pass
    - Log with log-implementation tool (include artifacts: classes with methods, test success confirmation)
    - Mark this task as completed [x] in tasks.md after logging

### Task 1.3: Readingテスト作成（Red）

- [x] 1.3. Write tests for Reading value object (Red phase)
  - File: [tests/unit/domain/test_reading.py](tests/unit/domain/test_reading.py)
  - Reading値オブジェクトのテストを作成（実装前）
  - テスト内容: `normalized` プロパティ（ひらがな→カタカナ正規化）、`to_moras()` メソッド
  - **テスト失敗確認**: `uv run pytest tests/unit/domain/test_reading.py -v` で失敗することを確認
  - _Requirements: Requirement 2, Requirement 8 (TDD)_
  - _Prompt:
    Implement the task for spec ddd-onion-refactor, first run spec-workflow-guide to get the workflow guide then implement the task:
    Role: QA Engineer specializing in TDD | Task: Write unit tests for Reading value object in tests/unit/domain/test_reading.py BEFORE implementation (Red phase). Test: Reading(raw="とうきょう").normalized == "トウキョウ", Reading("トウキョウ").to_moras() returns List[Mora], edge cases (empty, mixed kana). Import: `from src.domain.models.reading import Reading`. Tests MUST fail initially. | Restrictions: Write tests only, tests must fail initially | Leverage: src/mora.py (normalize_reading logic) | Success: Tests fail (Red phase confirmed)
    Instructions:
    - Mark this task as in-progress [-] in tasks.md before starting
    - Run `uv run pytest tests/unit/domain/test_reading.py -v` and CONFIRM failure
    - Log with log-implementation tool
    - Mark as completed [x] after logging

### Task 1.4: Reading実装（Green）

- [x] 1.4. Implement Reading value object (Green phase)
  - File: [src/domain/models/reading.py](src/domain/models/reading.py)
  - Reading値オブジェクトを実装
  - `normalized` プロパティ、`to_moras()` メソッド
  - pydantic BaseModel、immutable設定
  - **テスト成功確認**: `uv run pytest tests/unit/domain/test_reading.py -v` で成功することを確認
  - _Leverage: src/mora.py（normalize_reading）、Mora_
  - _Requirements: Requirement 2_
  - _Prompt:
    Implement the task for spec ddd-onion-refactor, first run spec-workflow-guide to get the workflow guide then implement the task:
    Role: Python Developer specializing in DDD | Task: Implement Reading value object in src/domain/models/reading.py to pass tests (Green phase). pydantic BaseModel with `raw: str`, computed property `normalized` (hiragana->katakana using logic from src/mora.py), method `to_moras() -> List[Mora]` delegates to Mora.split(). frozen=True. | Restrictions: Minimal implementation to pass tests, immutable | Leverage: src/mora.py (normalize_reading), src/domain/models/mora.py, tests | Success: Tests pass
    Instructions:
    - Mark as in-progress [-]
    - Run `uv run pytest tests/unit/domain/test_reading.py -v` and CONFIRM pass
    - Log with log-implementation tool
    - Mark as completed [x]

---

## Phase 2: Domain層 - エンティティ（TDD）

### Task 2.1: LyricTokenテスト作成（Red）

- [x] 2.1. Write tests for LyricToken entity (Red phase)
  - File: [tests/unit/domain/test_lyric_token.py](tests/unit/domain/test_lyric_token.py)
  - LyricTokenエンティティのテストを作成（実装前）
  - テスト内容: `token_id` プロパティ、`moras` プロパティ
  - **テスト失敗確認**: pytest実行で失敗を確認
  - _Requirements: Requirement 2, Requirement 8 (TDD)_
  - _Prompt:
    Implement the task for spec ddd-onion-refactor, first run spec-workflow-guide to get the workflow guide then implement the task:
    Role: QA Engineer specializing in TDD | Task: Write tests for LyricToken entity in tests/unit/domain/test_lyric_token.py BEFORE implementation (Red phase). Test: token_id format {lyrics_corpus_id}_{line_index}_{token_index}, moras property returns List[Mora], entity mutability. Import: `from src.domain.models.lyric_token import LyricToken`. Tests MUST fail. | Restrictions: Tests only | Leverage: Reading, Mora | Success: Tests fail (Red)
    Instructions:
    - Mark as in-progress [-]
    - Run pytest and CONFIRM failure
    - Log
    - Mark as completed [x]

### Task 2.2: LyricToken実装（Green）

- [x] 2.2. Implement LyricToken entity (Green phase)
  - File: [src/domain/models/lyric_token.py](src/domain/models/lyric_token.py)
  - LyricTokenエンティティを実装
  - computed properties: `token_id`, `moras`
  - pydantic BaseModel（mutable）
  - **テスト成功確認**: pytest実行で成功を確認
  - _Leverage: Reading, Mora_
  - _Requirements: Requirement 2_
  - _Prompt:
    Implement the task for spec ddd-onion-refactor, first run spec-workflow-guide to get the workflow guide then implement the task:
    Role: Python Developer specializing in DDD | Task: Implement LyricToken entity in src/domain/models/lyric_token.py to pass tests (Green phase). pydantic BaseModel (frozen=False, mutable entity) with fields: lyrics_corpus_id, surface, reading (Reading), lemma, pos, line_index, token_index. Computed properties: token_id, moras. | Restrictions: Pass tests | Leverage: Reading, Mora, tests | Success: Tests pass
    Instructions:
    - Mark as in-progress [-]
    - Run pytest and CONFIRM pass
    - Log
    - Mark as completed [x]

### Task 2.3: その他エンティティ（LyricsCorpus, MatchRun, MatchResult）テスト作成（Red）

- [x] 2.3. Write tests for other entities (Red phase)
  - Files: [tests/unit/domain/test_lyrics_corpus.py](tests/unit/domain/test_lyrics_corpus.py), [tests/unit/domain/test_match_run.py](tests/unit/domain/test_match_run.py), [tests/unit/domain/test_match_result.py](tests/unit/domain/test_match_result.py)
  - LyricsCorpus、MatchRun、MatchResultのテストを作成
  - **テスト失敗確認**: pytest実行で失敗を確認
  - _Requirements: Requirement 2, Requirement 6, Requirement 8 (TDD)_
  - _Prompt:
    Implement the task for spec ddd-onion-refactor, first run spec-workflow-guide to get the workflow guide then implement the task:
    Role: QA Engineer specializing in TDD | Task: Write tests for LyricsCorpus, MatchRun, MatchResult in tests/unit/domain/ BEFORE implementation (Red phase). Test entity/value object construction, field validation, MatchType enum values. Tests MUST fail. | Restrictions: Tests only | Success: Tests fail (Red)
    Instructions:
    - Mark as in-progress [-]
    - Run pytest and CONFIRM failure
    - Log
    - Mark as completed [x]

### Task 2.4: その他エンティティ実装（Green）

- [x] 2.4. Implement other entities (Green phase)
  - Files: [src/domain/models/lyrics_corpus.py](src/domain/models/lyrics_corpus.py), [src/domain/models/match_run.py](src/domain/models/match_run.py), [src/domain/models/match_result.py](src/domain/models/match_result.py)
  - LyricsCorpus、MatchRun、MatchResultを実装
  - **テスト成功確認**: pytest実行で成功を確認
  - _Requirements: Requirement 2, Requirement 6_
  - _Prompt:
    Implement the task for spec ddd-onion-refactor, first run spec-workflow-guide to get the workflow guide then implement the task:
    Role: Python Developer specializing in DDD | Task: Implement LyricsCorpus, MatchRun (entities - mutable), MatchResult, MoraMatchDetail, MatchType enum (value objects - immutable) to pass tests (Green phase). Use pydantic BaseModel. | Restrictions: Pass tests | Leverage: tests | Success: Tests pass
    Instructions:
    - Mark as in-progress [-]
    - Run pytest and CONFIRM pass
    - Log
    - Mark as completed [x]

---

## Phase 3: Domain層 - Port/Service（TDD）

### Task 3.1: Repositoryインターフェース定義

- [x] 3.1. Define Repository Port interfaces
  - Files: [src/domain/repositories/*.py](src/domain/repositories/*.py)
  - Repository Portインターフェース定義（ABC）
  - LyricTokenRepository, LyricsRepository, MatchRepository
  - **注**: インターフェースなのでテストは不要（実装時にテスト）
  - _Requirements: Requirement 4 (Port/Adapter)_
  - _Prompt:
    Implement the task for spec ddd-onion-refactor, first run spec-workflow-guide to get the workflow guide then implement the task:
    Role: Python Developer specializing in DDD repository patterns | Task: Define Repository Port interfaces (ABC) in src/domain/repositories/. LyricTokenRepository, LyricsRepository, MatchRepository with @abstractmethod. No tests needed at this stage (interfaces only). | Restrictions: Interfaces only | Leverage: domain models | Success: Interfaces defined correctly
    Instructions:
    - Mark as in-progress [-]
    - No test execution needed (interfaces)
    - Log
    - Mark as completed [x]

### Task 3.2: NlpServiceインターフェース定義

- [x] 3.2. Define NlpService Port interface and TokenData DTO
  - Files: [src/domain/services/nlp_service.py](src/domain/services/nlp_service.py), [src/application/dtos/token_data.py](src/application/dtos/token_data.py)
  - NlpService Port、TokenData DTO定義
  - **注**: インターフェース/DTOなのでテストは不要
  - _Requirements: Requirement 4_
  - _Prompt:
    Implement the task for spec ddd-onion-refactor, first run spec-workflow-guide to get the workflow guide then implement the task:
    Role: Python Developer specializing in DDD | Task: Define NlpService Port (ABC) and TokenData DTO (pydantic). No tests needed (interfaces/DTOs). | Restrictions: Interfaces/DTOs only | Success: Defined correctly
    Instructions:
    - Mark as in-progress [-]
    - No test execution
    - Log
    - Mark as completed [x]

### Task 3.3: MatchingStrategyテスト作成（Red）

- [x] 3.3. Write tests for MatchingStrategy service (Red phase)
  - File: [tests/unit/domain/test_matching_strategy.py](tests/unit/domain/test_matching_strategy.py)
  - MatchingStrategyドメインサービスのテストを作成
  - モックRepository使用、3段階マッチング戦略を検証
  - **テスト失敗確認**: pytest実行で失敗を確認
  - _Requirements: Requirement 2, Requirement 3, Requirement 8 (TDD)_
  - _Prompt:
    Implement the task for spec ddd-onion-refactor, first run spec-workflow-guide to get the workflow guide then implement the task:
    Role: QA Engineer specializing in TDD and mocking | Task: Write tests for MatchingStrategy in tests/unit/domain/test_matching_strategy.py BEFORE implementation (Red phase). Mock LyricTokenRepository, test 3-stage matching: exact surface, exact reading, mora combination, no match. Use pytest + unittest.mock. Tests MUST fail. | Restrictions: Tests with mocks | Leverage: src/matcher.py (logic reference) | Success: Tests fail (Red)
    Instructions:
    - Mark as in-progress [-]
    - Run pytest and CONFIRM failure
    - Log
    - Mark as completed [x]

### Task 3.4: MatchingStrategy実装（Green）

- [x] 3.4. Implement MatchingStrategy service (Green phase)
  - File: [src/domain/services/matching_strategy.py](src/domain/services/matching_strategy.py)
  - MatchingStrategyドメインサービスを実装
  - **テスト成功確認**: pytest実行で成功を確認
  - _Leverage: LyricTokenRepository, domain models, src/matcher.py_
  - _Requirements: Requirement 2, Requirement 3_
  - _Prompt:
    Implement the task for spec ddd-onion-refactor, first run spec-workflow-guide to get the workflow guide then implement the task:
    Role: Python Developer specializing in DDD | Task: Implement MatchingStrategy in src/domain/services/matching_strategy.py to pass tests (Green phase). Implement match_token() with 3-stage strategy using Repository. | Restrictions: Pass tests | Leverage: src/matcher.py (logic), Repository Port, tests | Success: Tests pass
    Instructions:
    - Mark as in-progress [-]
    - Run pytest and CONFIRM pass
    - Log
    - Mark as completed [x]

---

## Phase 4: Infrastructure層 - Repository実装（TDD）

### Task 4.1: DB Schemaテスト作成（Red）

- [x] 4.1. Write tests for DB schema (Red phase)
  - File: [tests/unit/infrastructure/test_schema.py](tests/unit/infrastructure/test_schema.py)
  - DB Schema初期化のテストを作成
  - テーブル作成、インデックス作成を検証
  - **テスト失敗確認**: pytest実行で失敗を確認
  - _Requirements: Requirement 6, Requirement 8 (TDD)_
  - _Prompt:
    Implement the task for spec ddd-onion-refactor, first run spec-workflow-guide to get the workflow guide then implement the task:
    Role: QA Engineer specializing in TDD and database testing | Task: Write tests for DB schema in tests/unit/infrastructure/test_schema.py BEFORE implementation (Red phase). Test initialize_database() creates tables (lyrics_corpus, lyric_tokens, match_runs, match_results) with proper structure. Use temporary DuckDB file. Tests MUST fail. | Restrictions: Tests only, use tempfile | Success: Tests fail (Red)
    Instructions:
    - Mark as in-progress [-]
    - Run pytest and CONFIRM failure
    - Log
    - Mark as completed [x]

### Task 4.2: DB Schema実装（Green）

- [x] 4.2. Implement DB schema (Green phase)
  - File: [src/infrastructure/database/schema.py](src/infrastructure/database/schema.py)
  - DuckDB Schemaを実装
  - **テスト成功確認**: pytest実行で成功を確認
  - _Requirements: Requirement 6_
  - _Prompt:
    Implement the task for spec ddd-onion-refactor, first run spec-workflow-guide to get the workflow guide then implement the task:
    Role: Database Engineer | Task: Implement DB schema in src/infrastructure/database/schema.py to pass tests (Green phase). Create 4 tables with indexes, implement initialize_database(). | Restrictions: Pass tests | Leverage: tests | Success: Tests pass
    Instructions:
    - Mark as in-progress [-]
    - Run pytest and CONFIRM pass
    - Log
    - Mark as completed [x]

### Task 4.3: DuckDB Repositoriesテスト作成（Red）

- [x] 4.3. Write tests for DuckDB repositories (Red phase)
  - File: [tests/unit/infrastructure/test_duckdb_repositories.py](tests/unit/infrastructure/test_duckdb_repositories.py)
  - DuckDBRepository実装のテストを作成
  - CRUD操作を検証
  - **テスト失敗確認**: pytest実行で失敗を確認
  - _Requirements: Requirement 4, Requirement 6, Requirement 8 (TDD)_
  - _Prompt:
    Implement the task for spec ddd-onion-refactor, first run spec-workflow-guide to get the workflow guide then implement the task:
    Role: QA Engineer specializing in TDD and repository testing | Task: Write tests for DuckDB repositories in tests/unit/infrastructure/test_duckdb_repositories.py BEFORE implementation (Red phase). Test all Repository interfaces (LyricTokenRepository, LyricsRepository, MatchRepository) CRUD operations with temp DB. Tests MUST fail. | Restrictions: Tests only | Success: Tests fail (Red)
    Instructions:
    - Mark as in-progress [-]
    - Run pytest and CONFIRM failure
    - Log
    - Mark as completed [x]

### Task 4.4: DuckDB Repositories実装（Green）

- [x] 4.4. Implement DuckDB repositories (Green phase)
  - Files: [src/infrastructure/database/duckdb_*.py](src/infrastructure/database/duckdb_*.py)
  - DuckDB Repository実装
  - **テスト成功確認**: pytest実行で成功（すべてのリポジトリテストがパス）
  - _Leverage: Repository Ports, schema.py_
  - _Requirements: Requirement 4, Requirement 6_
  - _Notes: 実装済み (DuckDBLyricTokenRepository, DuckDBLyricsRepository, DuckDBMatchRepository)。テストを分割し、`conftest.py` に fixture を追加。
  - _Prompt:
    Implement the task for spec ddd-onion-refactor, first run spec-workflow-guide to get the workflow guide then implement the task:
    Role: Python Developer specializing in repository pattern | Task: Implement DuckDB repositories (DuckDBLyricTokenRepository, DuckDBLyricsRepository, DuckDBMatchRepository) to pass tests (Green phase). Implement all Repository Port methods. | Restrictions: Pass tests | Leverage: Repository Ports, schema, tests | Success: Tests pass
    Instructions:
    - Run pytest and CONFIRM pass
    - Log (implementation logged)
    - Mark as completed [x]

### Task 4.5: SpaCy NlpServiceテスト作成（Red）

- [x] 4.5. Write tests for SpaCy NlpService (Red phase)
  - File: [tests/unit/infrastructure/test_spacy_nlp_service.py](tests/unit/infrastructure/test_spacy_nlp_service.py)
  - SpaCyNlpService実装のテストを作成
  - **テスト失敗確認**: pytest実行で失敗を確認（Redフェーズ確認済み）
  - _Requirements: Requirement 4, Requirement 8 (TDD)_
  - _Notes: テスト作成後、実装 (Task 4.6) を行い、すべてのテストがパスしています。 (ログ記録済み)
  - _Prompt:
    Implement the task for spec ddd-onion-refactor, first run spec-workflow-guide to get the workflow guide then implement the task:
    Role: QA Engineer specializing in TDD | Task: Write tests for SpaCyNlpService in tests/unit/infrastructure/test_spacy_nlp_service.py BEFORE implementation (Red phase). Test tokenize() method with simple Japanese text. Mark as @pytest.mark.slow. Tests MUST fail. | Restrictions: Tests only | Success: Tests fail (Red)
    Instructions:
    - Run pytest and CONFIRM failure (Red確認)
    - Log
    - Mark as completed [x]

### Task 4.6: SpaCy NlpService実装（Green）

- [x] 4.6. Implement SpaCy NlpService (Green phase)
  - File: [src/infrastructure/nlp/spacy_nlp_service.py](src/infrastructure/nlp/spacy_nlp_service.py)
  - SpaCyNlpService実装
  - **テスト成功確認**: pytest実行で成功を確認
  - _Leverage: NlpService Port_
  - _Requirements: Requirement 4_
  - _Prompt:
    Implement the task for spec ddd-onion-refactor, first run spec-workflow-guide to get the workflow guide then implement the task:
    Role: Python Developer specializing in NLP | Task: Implement SpaCyNlpService to pass tests (Green phase). Implement tokenize() using spaCy + GiNZA. | Restrictions: Pass tests | Leverage: NlpService Port, tests | Success: Tests pass
    Instructions:
    - Mark as in-progress [-]
    - Run pytest and CONFIRM pass
    - Log
    - Mark as completed [x]

### Task 4.7: Settings実装

- [x] 4.7. Implement Settings configuration
  - File: [src/infrastructure/config/settings.py](src/infrastructure/config/settings.py)
  - pydantic-settings設定管理実装
  - **注**: シンプルな設定クラスなので、テスト省略可（または簡易テスト）
  - _Leverage: src/config.py_
  - _Requirements: tech.md_
  - _Prompt:
    Implement the task for spec ddd-onion-refactor, first run spec-workflow-guide to get the workflow guide then implement the task:
    Role: Python Developer | Task: Implement Settings class using pydantic-settings. Define db_path, nlp_model_name, max_mora_length with defaults. env_prefix="LYRIC_TALK_". | Restrictions: Follow tech.md | Leverage: src/config.py, tech.md | Success: Settings works correctly
    Instructions:
    - Mark as in-progress [-]
    - Log
    - Mark as completed [x]

---

## Phase 5: Application層 - ユースケース（TDD）

### Task 5.1: RegisterLyricsUseCaseテスト作成（Red）

- [x] 5.1. Write tests for RegisterLyricsUseCase (Red phase)
  - File: [tests/unit/application/test_register_lyrics.py](tests/unit/application/test_register_lyrics.py)
  - RegisterLyricsUseCaseのテストを作成（Port/Adapterモック化）
  - **テスト失敗確認**: pytest実行で失敗を確認
  - _Requirements: Requirement 3, Requirement 8 (TDD)_
  - _Prompt:
    Implement the task for spec ddd-onion-refactor, first run spec-workflow-guide to get the workflow guide then implement the task:
    Role: QA Engineer specializing in TDD and use case testing | Task: Write tests for RegisterLyricsUseCase in tests/unit/application/test_register_lyrics.py BEFORE implementation (Red phase). Mock all Ports (NlpService, repositories). Test: new registration, duplicate hash reuse. Tests MUST fail. | Restrictions: Tests with mocks | Success: Tests fail (Red)
    Instructions:
    - Mark as in-progress [-]
    - Run pytest and CONFIRM failure
    - Log
    - Mark as completed [x]

### Task 5.2: RegisterLyricsUseCase実装（Green）

- [x] 5.2. Implement RegisterLyricsUseCase (Green phase)
  - File: [src/application/use_cases/register_lyrics.py](src/application/use_cases/register_lyrics.py)
  - RegisterLyricsUseCase実装
  - **テスト成功確認**: pytest実行で成功を確認
  - _Leverage: Ports, domain models_
  - _Requirements: Requirement 3_
  - _Prompt:
    Implement the task for spec ddd-onion-refactor, first run spec-workflow-guide to get the workflow guide then implement the task:
    Role: Python Developer specializing in application layer | Task: Implement RegisterLyricsUseCase to pass tests (Green phase). Implement execute() method with hash check, tokenization, entity creation, repository save. | Restrictions: Pass tests | Leverage: Ports, models, tests | Success: Tests pass
    Instructions:
    - Mark as in-progress [-]
    - Run pytest and CONFIRM pass
    - Log
    - Mark as completed [x]

### Task 5.3: MatchTextUseCaseテスト作成（Red）

- [x] 5.3. Write tests for MatchTextUseCase (Red phase)
  - File: [tests/unit/application/test_match_text.py](tests/unit/application/test_match_text.py)
  - MatchTextUseCaseのテストを作成
  - **テスト失敗確認**: pytest実行で失敗を確認
  - _Requirements: Requirement 3, Requirement 8 (TDD)_
  - _Prompt:
    Implement the task for spec ddd-onion-refactor, first run spec-workflow-guide to get the workflow guide then implement the task:
    Role: QA Engineer specializing in TDD | Task: Write tests for MatchTextUseCase BEFORE implementation (Red phase). Mock Ports. Test matching flow, result saving. Tests MUST fail. | Restrictions: Tests with mocks | Success: Tests fail (Red)
    Instructions:
    - Mark as in-progress [-]
    - Run pytest and CONFIRM failure
    - Log
    - Mark as completed [x]

### Task 5.4: MatchTextUseCase実装（Green）

- [x] 5.4. Implement MatchTextUseCase (Green phase)
  - File: [src/application/use_cases/match_text.py](src/application/use_cases/match_text.py)
  - MatchTextUseCase実装
  - **テスト成功確認**: pytest実行で成功を確認
  - _Leverage: Ports, MatchingStrategy_
  - _Requirements: Requirement 3_
  - _Prompt:
    Implement the task for spec ddd-onion-refactor, first run spec-workflow-guide to get the workflow guide then implement the task:
    Role: Python Developer | Task: Implement MatchTextUseCase to pass tests (Green phase). Implement execute() with tokenization, matching, result saving. | Restrictions: Pass tests | Leverage: Ports, MatchingStrategy, tests | Success: Tests pass
    Instructions:
    - Mark as in-progress [-]
    - Run pytest and CONFIRM pass
    - Log
    - Mark as completed [x]

### Task 5.5: QueryResultsUseCaseテスト作成（Red）

- [x] 5.5. Write tests for QueryResultsUseCase (Red phase)
  - File: [tests/unit/application/test_query_results.py](tests/unit/application/test_query_results.py)
  - QueryResultsUseCaseのテストを作成
  - **テスト失敗確認**: pytest実行で失敗を確認
  - _Requirements: Requirement 3, Requirement 6, Requirement 8 (TDD)_
  - _Prompt:
    Implement the task for spec ddd-onion-refactor, first run spec-workflow-guide to get the workflow guide then implement the task:
    Role: QA Engineer specializing in TDD | Task: Write tests for QueryResultsUseCase BEFORE implementation (Red phase). Mock Ports. Test result retrieval, token resolution. Tests MUST fail. | Restrictions: Tests with mocks | Success: Tests fail (Red)
    Instructions:
    - Mark as in-progress [-]
    - Run pytest and CONFIRM failure
    - Log
    - Mark as completed [x]

### Task 5.6: QueryResultsUseCase実装（Green）

- [x] 5.6. Implement QueryResultsUseCase (Green phase)
  - File: [src/application/use_cases/query_results.py](src/application/use_cases/query_results.py)
  - QueryResultsUseCase実装
  - **テスト成功確認**: pytest実行で成功を確認
  - _Leverage: MatchRepository, LyricTokenRepository_
  - _Requirements: Requirement 3, Requirement 6_
  - _Prompt:
    Implement the task for spec ddd-onion-refactor, first run spec-workflow-guide to get the workflow guide then implement the task:
    Role: Python Developer | Task: Implement QueryResultsUseCase to pass tests (Green phase). Implement execute() with result retrieval and token resolution. | Restrictions: Pass tests | Leverage: Repositories, tests | Success: Tests pass
    Instructions:
    - Mark as in-progress [-]
    - Run pytest and CONFIRM pass
    - Log
    - Mark as completed [x]

---

## Phase 6: Interface層 - CLI（TDD）

### Task 6.1: CLI Mainテスト作成（Red）

- [x] 6.1. Write tests for CLI main (Red phase)
  - File: [tests/unit/interface/test_cli_main.py](tests/unit/interface/test_cli_main.py)
  - CLI Mainのテストを作成
  - **テスト失敗確認**: pytest実行で失敗を確認
  - _Requirements: Requirement 5, Requirement 7, Requirement 8 (TDD)_
  - _Prompt:
    Implement the task for spec ddd-onion-refactor, first run spec-workflow-guide to get the workflow guide then implement the task:
    Role: QA Engineer specializing in TDD and CLI testing | Task: Write tests for CLI main in tests/unit/interface/test_cli_main.py BEFORE implementation (Red phase). Test 3 subcommands (register, match, query) with mocked use cases. Tests MUST fail. | Restrictions: Tests with mocks | Success: Tests fail (Red)
    Instructions:
    - Mark as in-progress [-]
    - Run pytest and CONFIRM failure
    - Log
    - Mark as completed [x]

### Task 6.2: CLI Main実装（Green）

- [x] 6.2. Implement CLI main (Green phase)
  - File: [src/interface/cli/main.py](src/interface/cli/main.py)
  - CLI Mainエントリポイント実装
  - **テスト成功確認**: pytest実行で成功を確認
  - _Leverage: すべてのUseCase、Infrastructure実装、Settings_
  - _Requirements: Requirement 5, Requirement 7_
  - _Prompt:
    Implement the task for spec ddd-onion-refactor, first run spec-workflow-guide to get the workflow guide then implement the task:
    Role: Python Developer specializing in CLI | Task: Implement CLI main to pass tests (Green phase). Use argparse, 3 subcommands, DI with concrete implementations, error handling. | Restrictions: Pass tests | Leverage: Use cases, Infrastructure, Settings, tests | Success: Tests pass
    Instructions:
    - Mark as in-progress [-]
    - Run pytest and CONFIRM pass
    - Log
    - Mark as completed [x]

### Task 6.3: pyproject.tomlエントリポイント更新

- [x] 6.3. Update pyproject.toml entry point
  - File: [pyproject.toml](pyproject.toml)
  - `[project.scripts]` を更新: `lyric-talk = "src.interface.cli.main:main"`
  - _Requirements: Requirement 7_
  - _Prompt:
    Implement the task for spec ddd-onion-refactor, first run spec-workflow-guide to get the workflow guide then implement the task:
    Role: Python Developer | Task: Update pyproject.toml entry point. Change [project.scripts] to: lyric-talk = "src.interface.cli.main:main". | Restrictions: Only modify [project.scripts] | Leverage: pyproject.toml | Success: Entry point updated
    Instructions:
    - Mark as in-progress [-]
    - Log
    - Mark as completed [x]

---

## Phase 7: 統合テスト

### Task 7.1: E2E統合テスト作成

- [x] 7.1. Write end-to-end integration tests
  - File: [tests/integration/test_full_pipeline.py](tests/integration/test_full_pipeline.py)
  - register → match → query の一連の流れをテスト（実際のspaCy + DuckDB）
  - `@pytest.mark.integration`
  - _Requirements: Requirement 8_
  - _Prompt:
    Implement the task for spec ddd-onion-refactor, first run spec-workflow-guide to get the workflow guide then implement the task:
    Role: QA Engineer specializing in integration testing | Task: Write E2E integration tests in tests/integration/test_full_pipeline.py. Test full pipeline with real dependencies: register → match → query. Use temp DB. Mark as @pytest.mark.integration. | Restrictions: Real dependencies (no mocks) | Leverage: All components | Success: Integration tests pass
    Instructions:
    - Mark as in-progress [-]
    - Run `uv run pytest -m integration` and verify pass
    - Log
    - Mark as completed [x]

---

## Phase 8: クリーンアップ

### Task 8.1: 既存コードの削除

- [x] 8.1. Remove old experimental code
  - Files to delete: [src/main.py](src/main.py), [src/config.py](src/config.py), [src/lyric_index.py](src/lyric_index.py), [src/matcher.py](src/matcher.py), [src/mora.py](src/mora.py)
  - 既存の実験的コードを削除
  - _Requirements: Requirement 7_
  - _Prompt:
    Implement the task for spec ddd-onion-refactor, first run spec-workflow-guide to get the workflow guide then implement the task:
    Role: Developer | Task: Remove old experimental code. Delete: src/main.py, src/config.py, src/lyric_index.py, src/matcher.py, src/mora.py. Verify no references exist. | Restrictions: Ensure new implementation is complete | Success: Old code removed
    Instructions:
    - Mark as in-progress [-]
    - Log
    - Mark as completed [x]

### Task 8.2: ドキュメント更新

- [x] 8.2. Update README with new architecture
  - File: [README.md](README.md)
  - 新アーキテクチャの説明、使用方法、開発ガイドを追加
  - _Requirements: すべての要件_
  - _Prompt:
    Implement the task for spec ddd-onion-refactor, first run spec-workflow-guide to get the workflow guide then implement the task:
    Role: Technical Writer | Task: Update README.md with new DDD + Onion Architecture documentation. Include: architecture overview, usage examples, development guide. | Restrictions: Concise and user-friendly | Success: README clearly explains new architecture
    Instructions:
    - Mark as in-progress [-]
    - Log
    - Mark as completed [x]

### Task 8.3: 最終動作確認

- [x] 8.3. Final verification and testing
  - すべてのテストを実行: `uv run pytest`
  - Lint: `uv run ruff check .`
  - Format: `uv run ruff format .`
  - CLIマニュアルテスト: `lyric-talk register/match/query`
  - _Requirements: すべての要件_
  - _Prompt:
    Implement the task for spec ddd-onion-refactor, first run spec-workflow-guide to get the workflow guide then implement the task:
    Role: QA Engineer | Task: Final verification. Run: pytest (all tests pass), ruff check (no errors), ruff format (formatted), manual CLI testing. Verify all requirements met. | Restrictions: All checks must pass | Success: All tests pass, no lint errors, CLI works
    Instructions:
    - Mark as in-progress [-]
    - Log verification results
    - Mark as completed [x]

---

## Summary

**Total Tasks**: 44 tasks across 8 phases（TDD方式）

**TDD Implementation Flow**:

各機能について:

1. **Red**: テスト作成 → 失敗確認
2. **Green**: 実装 → 成功確認
3. **Refactor**: 必要に応じてリファクタリング

**Phase Overview**:

1. **Domain層 - 値オブジェクト**（4タスク）: Mora, Reading（各2タスク: テスト+実装）
2. **Domain層 - エンティティ**（4タスク）: LyricToken, その他（各2タスク: テスト+実装）
3. **Domain層 - Port/Service**（4タスク）: Repositoryインターフェース、NlpService、MatchingStrategy
4. **Infrastructure層**（8タスク）: Schema, Repositories, NlpService, Settings（各TDD）
5. **Application層**（6タスク）: 3つのUseCase（各2タスク: テスト+実装）
6. **Interface層**（3タスク）: CLI（TDD）
7. **統合テスト**（1タスク）: E2Eテスト
8. **クリーンアップ**（3タスク）: 既存コード削除、ドキュメント、最終確認

**Key Differences from Original**:

- ✅ **テストファースト**: 各機能でテストを先に作成
- ✅ **失敗確認**: テスト失敗を明示的に確認（Red phase）
- ✅ **成功確認**: 実装後のテスト成功を明示的に確認（Green phase）
- ✅ **TDDサイクル**: Red → Green → Refactor の明確化

**Next Steps**:

1. 本TDD版タスクドキュメントの承認取得
2. Task 1.1（Moraテスト作成）から順次実装開始
3. 各タスクでRed/Green確認、implementation log記録
