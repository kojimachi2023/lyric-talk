# タスクドキュメント（Tasks Document - TDD版）

## Overview

本ドキュメントは、spec `cli-usability-improvements`（要件: `requirements.md` / 設計: `design.md`）を実装するためのタスク分解です。

目的:

- `match` / `query` の **ID省略時** に、一覧表示→対話選択で実行できる
- 一覧/参照/（必要なら削除）のロジックを **Application UseCase** に集約する
- CLI を **Typer + Rich** に移行し、ヘルプ/入力バリデーション/表示UX/非対話安全性を改善する
- UseCase の入出力を **DTO（pydantic）** で定義し、型安全性と保守性を上げる

### TDD方式の実装フロー

各タスクは以下の順に進めます。

1. **テスト作成（Red）**: 期待する動作を定義したテストを先に作成
2. **失敗確認**: `uv run pytest ...` を実行して失敗することを確認
3. **実装（Green）**: 最小限の実装でテストを通す
4. **成功確認**: `uv run pytest ...` を実行して成功することを確認
5. **リファクタ（Refactor）**: 必要に応じて整理

---

## Phase 1: Application層 - DTO / 一覧UseCase / Query DTO化（TDD）

### Task 1.1: CLI向けサマリーDTOを追加

- [ ] 1.1. Add summary DTOs for CLI (Corpus / Run)
  - File: `src/application/dtos/cli_summaries.py`
  - `LyricsCorpusSummaryDto` / `MatchRunSummaryDto` を pydantic DTO として定義する
  - DTO は CLI 表示に必要な概要情報（ID、title/artist、created_at、token_count、preview_text、timestamp、results_count、input_text(全文) 等）を保持する
  - _Requirements: Requirement 1, Requirement 2, Requirement 3, Requirement 6_
  - _Prompt:
    Implement the task for spec cli-usability-improvements, first run spec-workflow-guide to get the workflow guide then implement the task:
    Role: Python Developer specializing in application-layer DTO design (pydantic) | Task: Create `src/application/dtos/cli_summaries.py` and define immutable pydantic DTOs `LyricsCorpusSummaryDto` and `MatchRunSummaryDto` per design.md Data Models section. Ensure fields match CLI needs (IDs, timestamps, counts, preview). Use `model_config = {"frozen": True}`. | Restrictions: Do not change domain models. Do not return dicts from use cases introduced in later tasks. Keep DTOs independent of infrastructure. | Leverage: `src/application/dtos/token_data.py` patterns | Success: DTO module imports cleanly; types are explicit; no tests required for pure DTO definitions.
    Instructions:
    - Mark this task as in-progress [-] in tasks.md before starting
    - Run `uv run ruff check .` and confirm no lint errors
    - Log with log-implementation tool
    - Mark this task as completed [x] in tasks.md after logging

### Task 1.2: ListLyricsCorporaUseCase（一覧取得）を追加（Red→Green）

- [ ] 1.2. Implement `ListLyricsCorporaUseCase` with tests
  - Files:
    - `src/application/use_cases/list_lyrics_corpora.py`
    - `tests/unit/application/test_list_lyrics_corpora.py`
  - コーパス一覧（新しい順、limitあり）を DTO で返す
  - 0件/1件/複数件の振る舞いをテストする
  - token_count / preview_text は LyricTokenRepository 経由で算出する（Repository直呼び禁止）
  - _Requirements: Requirement 1, Requirement 3, Requirement 6_
  - _Prompt:
    Implement the task for spec cli-usability-improvements, first run spec-workflow-guide to get the workflow guide then implement the task:
    Role: QA Engineer + Python Developer (TDD) | Task: Add unit tests first for `ListLyricsCorporaUseCase` then implement it. Use mocks for `LyricsRepository` and `LyricTokenRepository`. Ensure sorting/limit behavior is deterministic. Return `list[LyricsCorpusSummaryDto]` (not domain models, not dicts). | Restrictions: TDD: write tests first and confirm failure. Do not access infrastructure repositories in unit tests. | Leverage: existing use case tests (`tests/unit/application/*`), DTOs from `src/application/dtos/cli_summaries.py` | Success: `uv run pytest tests/unit/application/test_list_lyrics_corpora.py -v` passes.
    Instructions:
    - Mark this task as in-progress [-] in tasks.md before starting
    - Run the test file once to confirm failure (Red)
    - Implement until it passes (Green)
    - Log with log-implementation tool
    - Mark as completed [x]

### Task 1.3: ListMatchRunsUseCase（実行履歴一覧）を追加（Red→Green）

- [ ] 1.3. Implement `ListMatchRunsUseCase` with tests
  - Files:
    - `src/application/use_cases/list_match_runs.py`
    - `tests/unit/application/test_list_match_runs.py`
  - run一覧（新しい順、limitあり）を DTO で返す
  - results_count は Repository 経由で算出する（もしくはサマリー取得で同時に返す）
  - _Requirements: Requirement 2, Requirement 3, Requirement 6_
  - _Prompt:
    Implement the task for spec cli-usability-improvements, first run spec-workflow-guide to get the workflow guide then implement the task:
    Role: QA Engineer + Python Developer (TDD) | Task: Add tests first, then implement `ListMatchRunsUseCase` returning `list[MatchRunSummaryDto]`. Use mock `MatchRepository`. Verify empty/non-empty, stable ordering, and limit behavior. | Restrictions: TDD (tests first). Do not return dicts. | Leverage: `src/application/use_cases/query_results.py` for repository usage patterns | Success: `uv run pytest tests/unit/application/test_list_match_runs.py -v` passes.
    Instructions:
    - Mark in-progress [-]
    - Confirm Red then Green
    - Log
    - Mark completed [x]

### Task 1.4: QueryResultsUseCase を DTO 化 + 再構成サマリーを実装（Red→Green）

- [ ] 1.4. Refactor `QueryResultsUseCase` to return `QueryResultsDto`
  - Files:
    - `src/application/dtos/query_results_dto.py`
    - `src/application/use_cases/query_results.py`
    - `tests/unit/application/test_query_results_dto.py`
  - `execute(run_id)` の返り値を `Optional[QueryResultsDto]` に変更
  - `exact_*` / `mora_combination` の両方で「判読可能な表示用構造」を DTO に落とす
  - サマリーとして `reconstructed_surface` / `reconstructed_reading`（設計の考え方に沿う）を生成する
  - _Requirements: Requirement 2(5-7), Requirement 6_
  - _Prompt:
    Implement the task for spec cli-usability-improvements, first run spec-workflow-guide to get the workflow guide then implement the task:
    Role: Python Developer specializing in DTO modeling + TDD | Task: Introduce `QueryResultsDto` (and nested DTOs) in `src/application/dtos/query_results_dto.py`, then refactor `QueryResultsUseCase.execute()` to return it. Write tests that cover: (a) not found returns None, (b) exact_surface/exact_reading resolves chosen tokens, (c) mora_combination includes mora trace info, (d) reconstructed summary strings are generated deterministically. Use mocks for repositories. | Restrictions: Do not leak domain models to CLI layer; DTOs should carry only what CLI needs. Keep existing domain models unchanged. | Leverage: `src/domain/models/match_result.py` fields (`mora_details`, `matched_token_ids`), existing `tests/unit/application/test_query_results.py` | Success: `uv run pytest tests/unit/application/test_query_results_dto.py -v` passes and existing tests remain green (or are updated within this task if strictly necessary).
    Instructions:
    - Mark in-progress [-]
    - Confirm Red then Green
    - Run `uv run pytest` (full suite) before completing
    - Log
    - Mark completed [x]

---

## Phase 2: Domain層 - Repository Port 拡張（一覧/件数）（設計反映）

### Task 2.1: Repositoryインターフェースに「一覧/件数」APIを追加

- [ ] 2.1. Extend repository interfaces for listing / counting
  - Files:
    - `src/domain/repositories/lyrics_repository.py`
    - `src/domain/repositories/lyric_token_repository.py`
    - `src/domain/repositories/match_repository.py`
  - 追加する抽象メソッド（命名は実装側と一貫すること）例:
    - `LyricsRepository.list_recent(limit: int) -> list[LyricsCorpus]`
    - `LyricTokenRepository.count_by_lyrics_corpus_id(lyrics_corpus_id: str) -> int`
    - `LyricTokenRepository.list_by_lyrics_corpus_id(lyrics_corpus_id: str, limit: int) -> list[LyricToken]`
    - `MatchRepository.list_recent(limit: int) -> list[MatchRun]`（必要なら results_count 用の別メソッドも）
  - _Requirements: Requirement 3(8)_
  - _Prompt:
    Implement the task for spec cli-usability-improvements, first run spec-workflow-guide to get the workflow guide then implement the task:
    Role: Software Architect specializing in DDD repository ports | Task: Extend repository ABCs to support list/count operations required by List* use cases and CLI. Add only minimal abstract methods needed by design.md. Ensure typing is precise and backward compatibility is preserved (existing methods unchanged). | Restrictions: Do not import infrastructure. Do not change existing method signatures. | Leverage: existing repository interfaces in `src/domain/repositories/*.py` | Success: Code type-checks, all existing tests pass.
    Instructions:
    - Mark in-progress [-]
    - Run `uv run pytest tests/unit/domain -v` (or full suite) to confirm green
    - Log
    - Mark completed [x]

---

## Phase 3: Infrastructure層 - DuckDB repository 実装（TDD）

### Task 3.1: DuckDBLyricsRepository にコーパス一覧取得を追加（Red→Green）

- [ ] 3.1. Add `list_recent()` to DuckDBLyricsRepository with tests
  - Files:
    - `src/infrastructure/database/duckdb_lyrics_repository.py`
    - `tests/unit/infrastructure/test_duckdb_lyrics_repository.py`
  - created_at 降順で limit 件を返す（順序が決定論的）
  - _Requirements: Requirement 1, Requirement 3_
  - _Prompt:
    Implement the task for spec cli-usability-improvements, first run spec-workflow-guide to get the workflow guide then implement the task:
    Role: Database Engineer + Python Developer (TDD) | Task: Write a failing test for `DuckDBLyricsRepository.list_recent()` then implement it. Ensure schema compatibility and deterministic ordering. | Restrictions: Use temp DB fixtures; do not load all tokens. | Leverage: existing tests and schema init helpers in `tests/unit/infrastructure/conftest.py` | Success: new tests pass.
    Instructions:
    - Mark in-progress [-]
    - Confirm Red then Green
    - Log
    - Mark completed [x]

### Task 3.2: DuckDBLyricTokenRepository に token_count / preview 用 API を追加（Red→Green）

- [ ] 3.2. Add `count_by_lyrics_corpus_id()` and `list_by_lyrics_corpus_id()` with tests
  - Files:
    - `src/infrastructure/database/duckdb_lyric_token_repository.py`
    - `tests/unit/infrastructure/test_duckdb_lyric_token_repository.py`
  - token_count と preview（先頭N token）生成に必要な最小SQLを実装
  - _Requirements: Requirement 1, Requirement 3, Non-Functional(Performance)_
  - _Prompt:
    Implement the task for spec cli-usability-improvements, first run spec-workflow-guide to get the workflow guide then implement the task:
    Role: Database Engineer (TDD) | Task: Add tests first then implement two methods in DuckDBLyricTokenRepository: (1) count tokens by corpus id, (2) list first N tokens (stable order by line_index/token_index). | Restrictions: Deterministic ordering; avoid full table scans when possible; keep method signatures aligned with Domain ports. | Leverage: existing repository patterns in this file, schema columns | Success: tests pass and existing suite remains green.
    Instructions:
    - Mark in-progress [-]
    - Confirm Red then Green
    - Log
    - Mark completed [x]

### Task 3.3: DuckDBMatchRepository に実行履歴一覧取得（+ results_count）を追加（Red→Green）

- [ ] 3.3. Add `list_recent()` (and results_count support) with tests
  - Files:
    - `src/infrastructure/database/duckdb_match_repository.py`
    - `tests/unit/infrastructure/test_duckdb_match_repository.py`
  - run の created/timestamp 降順で limit 件を返す
  - results_count を安価に取得できるようにする（JOIN/集計 or 専用メソッド）
  - _Requirements: Requirement 2, Requirement 3_
  - _Prompt:
    Implement the task for spec cli-usability-improvements, first run spec-workflow-guide to get the workflow guide then implement the task:
    Role: Database Engineer + Python Developer (TDD) | Task: Add a failing test for listing match runs and results_count, then implement SQL in DuckDBMatchRepository accordingly. Ensure it works with existing save/find behavior. | Restrictions: Keep existing CRUD behavior unchanged. Deterministic ordering. | Leverage: existing DuckDBMatchRepository tests and schema | Success: tests pass.
    Instructions:
    - Mark in-progress [-]
    - Confirm Red then Green
    - Log
    - Mark completed [x]

---

## Phase 4: Interface層 - Typer + Rich CLI（TDD / 互換維持）

### Task 4.1: Typer + Rich を依存関係に追加

- [ ] 4.1. Add CLI dependencies (typer, rich)
  - File: `pyproject.toml`
  - `typer` と `rich` を `project.dependencies` に追加（uvで解決できる形）
  - _Requirements: Requirement 4, Requirement 5_
  - _Prompt:
    Implement the task for spec cli-usability-improvements, first run spec-workflow-guide to get the workflow guide then implement the task:
    Role: Python Packaging Engineer | Task: Add `typer` and `rich` dependencies to pyproject.toml. Keep existing tooling (uv/pytest/ruff) intact. | Restrictions: Do not remove existing deps. Ensure lockfile update is handled per project conventions. | Leverage: current pyproject.toml and uv.lock | Success: `uv run python -c "import typer, rich"` works and tests still run.
    Instructions:
    - Mark in-progress [-]
    - Run unit tests and ruff
    - Log
    - Mark completed [x]

### Task 4.2: CLI を Typer アプリに移行（骨格 + 既存互換）

- [ ] 4.2. Migrate CLI entry to Typer while keeping entrypoint
  - Files:
    - `src/interface/cli/main.py`
    - `tests/unit/interface/test_cli_main.py`
  - `main()` は維持しつつ内部で Typer アプリを起動
  - `register/match/query` の基本フロー（ID明示指定時）は既存互換を維持
  - _Requirements: Requirement 4, Requirement 5_
  - _Prompt:
    Implement the task for spec cli-usability-improvements, first run spec-workflow-guide to get the workflow guide then implement the task:
    Role: Python CLI Developer (Typer) + QA Engineer | Task: Refactor `src/interface/cli/main.py` to Typer-based CLI while preserving the `main()` entrypoint used by packaging. Update `tests/unit/interface/test_cli_main.py` to use Typer testing patterns (or invoke main similarly) and keep existing non-interactive flows passing (explicit corpus_id/run_id). | Restrictions: Do not change application wiring helpers unless needed. Keep exit codes meaningful. | Leverage: existing create_*_use_case functions, Typer docs patterns | Success: `uv run pytest tests/unit/interface/test_cli_main.py -v` passes.
    Instructions:
    - Mark in-progress [-]
    - Confirm tests fail before refactor completion (if applicable)
    - Run full suite before completing
    - Log
    - Mark completed [x]

### Task 4.3: `corpus list` / `run list` コマンド追加（非対話対応の基盤）

- [ ] 4.3. Add list commands with Rich tables
  - Files:
    - `src/interface/cli/main.py`
    - `tests/unit/interface/test_cli_main.py`
  - `ListLyricsCorporaUseCase` / `ListMatchRunsUseCase` を呼び出し、Rich Table で表示
  - 非対話でも実行可能（一覧表示のみ）
  - _Requirements: Requirement 1, Requirement 2, Requirement 4, Requirement 5_
  - _Prompt:
    Implement the task for spec cli-usability-improvements, first run spec-workflow-guide to get the workflow guide then implement the task:
    Role: Python CLI Developer (Rich UI) | Task: Add new Typer subcommands: `corpus list` and `run list`. Use Rich Table to render summaries from DTOs. Add/adjust unit tests to assert key fields appear in output. | Restrictions: Avoid querying heavy details; use list use cases only. | Leverage: List* use cases and DTOs | Success: tests pass and output is human-readable.
    Instructions:
    - Mark in-progress [-]
    - Run targeted tests
    - Log
    - Mark completed [x]

### Task 4.4: `match` の corpus_id 省略時に一覧→選択（TTYのみ）

- [ ] 4.4. Add interactive selection for `match` when corpus_id omitted
  - Files:
    - `src/interface/cli/main.py`
    - `tests/unit/interface/test_cli_main.py`
  - corpus_id が未指定:
    - 0件: 「先に register が必要」を表示して非ゼロ終了
    - 1件: それをデフォルト選択（選択された旨を表示）
    - 複数: Rich/Typer で選択プロンプト
  - 非TTYの場合は対話せず、「--corpus-id を指定」または `corpus list` を案内して非ゼロ終了
  - _Requirements: Requirement 1, Requirement 4(5), Requirement 5_
  - _Prompt:
    Implement the task for spec cli-usability-improvements, first run spec-workflow-guide to get the workflow guide then implement the task:
    Role: Python CLI Developer (Typer prompts) + QA Engineer | Task: Implement match command behavior per requirements: corpus_id optional; if omitted, call ListLyricsCorporaUseCase and drive selection logic; enforce non-interactive safety (TTY check). Update tests to cover 0/1/many and explicit corpus_id path. | Restrictions: Do not require DB access in unit tests; mock use cases. Ensure deterministic behavior. | Leverage: Typer prompt APIs, Rich rendering, existing test patterns | Success: unit tests pass and behavior matches acceptance criteria.
    Instructions:
    - Mark in-progress [-]
    - Confirm tests cover branches
    - Log
    - Mark completed [x]

### Task 4.5: `query` の run_id 省略時に一覧→選択 + Rich表示（Tree）

- [ ] 4.5. Add interactive selection + rich display for `query`
  - Files:
    - `src/interface/cli/main.py`
    - `tests/unit/interface/test_cli_main.py`
  - run_id が未指定:
    - 0件: 「先に match が必要」で非ゼロ
    - 複数: 選択
  - 表示は Rich Tree で「入力トークン→match_type→採用トークン/モーラ根拠」を追える形式にする
  - DTO（`QueryResultsDto`）を前提とし、サマリー（再構成テキスト）も表示する
  - 非TTYで run_id 省略はエラー
  - _Requirements: Requirement 2, Requirement 4(5), Requirement 6_
  - _Prompt:
    Implement the task for spec cli-usability-improvements, first run spec-workflow-guide to get the workflow guide then implement the task:
    Role: Python CLI Developer (Rich Tree) + QA Engineer | Task: Implement query command behavior per requirements: run_id optional with selection; render QueryResultsDto using Rich Tree and also print summary reconstructed text/readings. Update tests to verify key parts of output and non-interactive error handling. | Restrictions: Keep output stable enough for tests (assert substrings). Do not leak domain models. | Leverage: QueryResultsUseCase (DTO), Rich Tree patterns | Success: tests pass.
    Instructions:
    - Mark in-progress [-]
    - Run tests
    - Log
    - Mark completed [x]

---

## Phase 5: 統合テスト / ドキュメント更新

### Task 5.1: 統合テストに list / DTO 化の影響を反映

- [ ] 5.1. Update integration test(s) for pipeline stability
  - File: `tests/integration/test_full_pipeline.py`
  - `register → match(corpus_id指定) → query(run_id指定)` の既存フローが維持されることを確認
  - DTO 化に伴う表示/戻り値の変更があっても、統合フローが壊れないことを担保
  - _Requirements: Requirement 5_
  - _Prompt:
    Implement the task for spec cli-usability-improvements, first run spec-workflow-guide to get the workflow guide then implement the task:
    Role: Integration Test Engineer | Task: Adjust integration tests so the end-to-end pipeline remains green after DTO and CLI improvements. Focus on non-interactive paths (explicit IDs) to keep CI stable. | Restrictions: Avoid interactive prompts in integration tests. | Leverage: existing integration test and repositories | Success: `uv run pytest tests/integration/test_full_pipeline.py -v` passes.
    Instructions:
    - Mark in-progress [-]
    - Run integration tests
    - Log
    - Mark completed [x]

### Task 5.2: README の CLI 使い方を更新

- [ ] 5.2. Update documentation for new CLI UX
  - File: `README.md`
  - `corpus list` / `run list`、`match/query` の省略時挙動、非TTY時の注意を追記
  - _Requirements: Requirement 4, Requirement 5_
  - _Prompt:
    Implement the task for spec cli-usability-improvements, first run spec-workflow-guide to get the workflow guide then implement the task:
    Role: Technical Writer + Developer Advocate | Task: Update README.md with examples of new commands and interactive behavior. Include non-interactive guidance (explicit IDs, list commands). Keep examples accurate to implemented CLI. | Restrictions: Do not invent flags that are not implemented. | Leverage: Typer --help output, requirements.md | Success: README matches actual CLI behavior.
    Instructions:
    - Mark in-progress [-]
    - Log
    - Mark completed [x]
