# Requirements Document

## Introduction

本specは、`lyric-talk` CLI のユーザービリティを改善し、ユーザーが **ID（`lyrics_corpus_id` / `run_id`）を事前にDBから調べないと操作できない** 現状を解消する。

具体的には、

- `match` 実行時に `corpus_id` が省略された場合、利用可能な歌詞コーパスを一覧表示し、ユーザーに選択させる
- `query` 実行時に `run_id` が省略された場合、利用可能なマッチ実行履歴を一覧表示し、ユーザーに選択させる
- そのために必要な「一覧/参照/削除」などのCRUDを、Domain Repository を利用する **Application UseCase** として追加する
- CLI の実装を **Typer**（型安全・補完/ヘルプ・入力バリデーション）と **Rich**（一覧表示/プロンプト/整形）で刷新し、保守性と可読性を上げる

を達成する。

## Alignment with Product Vision

`lyric-talk` のプロダクト原則（steering `product.md`）に対して、以下の点で整合する。

- **Explainability First**: 選択候補（コーパス/実行履歴）の概要を可視化し、「何を選んだか」「なぜそのデータを使ったか」を追える
- **Reproducibility & Configurability**: 明示的な `corpus_id` / `run_id` 指定も可能にしたうえで、省略時の選択を決定論的（ソート順やデフォルト選択ルール）にする
- **CLI中心のワークフロー**: 利用者がDBを直接開かずに、CLIだけで完結して操作できる

## Requirements

### Requirement 1: `match` の `corpus_id` 省略時に一覧表示→選択

**User Story:** CLIユーザーとして、`match` 実行時に `corpus_id` を知らなくても、登録済みコーパス情報の一覧から選択してマッチングできるようにしたい。そうすれば、毎回DBを開いてIDを確認する手間がなくなる。

#### Acceptance Criteria

1. WHEN ユーザーが `lyric-talk match` を `corpus_id` なしで実行した場合 THEN システム SHALL 登録済み歌詞コーパスの一覧（lyric_corpusのフィールド、および同集約内のlyric_tokensから読みだした歌詞の一部）を表示する
2. WHEN 一覧が表示された後 THEN システム SHALL ユーザーにコーパス選択を促し、選択されたコーパスIDを `MatchTextUseCase.execute(input_text, lyrics_corpus_id)` に渡して実行する
3. IF 登録済み歌詞コーパスが0件 THEN システム SHALL 「先に `register` が必要」であることを明確に表示し、非ゼロ終了コードで終了する
4. IF 登録済み歌詞コーパスが1件 THEN システム SHALL そのコーパスをデフォルト選択して続行できる（ただしユーザーに選択されたことが分かる表示を行う）
5. WHEN ユーザーが明示的に `corpus_id`（または同等のオプション）を指定して `match` を実行した場合 THEN システム SHALL 一覧表示/選択をスキップして直接マッチングを実行する

**Notes (Scope):** 一覧表示に含める概要情報は、少なくとも `corpus_id` とユーザーが識別しやすい識別子（例: title、登録日時、トークン数等）のいずれかを含むこと。

### Requirement 2: `query` の `run_id` 省略時に一覧表示→選択

**User Story:** CLIユーザーとして、`query` 実行時に `run_id` を知らなくても、過去の実行履歴の一覧から選択して結果を参照できるようにしたい。そうすれば、IDを控えていなくても結果に辿り着ける。

#### Acceptance Criteria

1. WHEN ユーザーが `lyric-talk query` を `run_id` なしで実行した場合 THEN システム SHALL 登録済みマッチ実行履歴（`run_id` の一覧）を概要つきで表示する
2. WHEN 一覧が表示された後 THEN システム SHALL ユーザーに実行履歴の選択を促し、選択された `run_id` を `QueryResultsUseCase.execute(run_id)` に渡して実行する
3. IF 実行履歴が0件 THEN システム SHALL 「先に `match` が必要」であることを明確に表示し、非ゼロ終了コードで終了する
4. WHEN ユーザーが明示的に `run_id`（または同等のオプション）を指定して `query` を実行した場合 THEN システム SHALL 一覧表示/選択をスキップして直接照会を実行する
5. WHEN `query` の結果を表示する場合 THEN システム SHALL 「入力トークンが何とマッチしたか」をトークン単位で判読可能に表示する（例: 入力表層/読み、`match_type`、採用された歌詞トークン、根拠情報）
6. IF `match_type` が `mora_combination` の場合 THEN システム SHALL マッチに使われたモーラ列（少なくとも `MatchResult.mora_details` 相当の情報）を表示し、どのモーラがどのトークン由来かが追える
7. WHEN `query` の結果を表示する場合 THEN システム SHALL 「採用されたトークン/モーラを連結したサマリー（再構成テキスト）」を表示する

**Notes (Scope):** 一覧表示に含める概要情報は、少なくとも `run_id` と `timestamp`、および識別しやすい付随情報（例: `lyrics_corpus_id`、入力文の先頭N文字、マッチ件数、設定など）のいずれかを含むこと。

### Requirement 3: CLIから利用できる「一覧/参照/削除」用UseCase（CRUDの一部）を追加

**User Story:** 開発者として、CLIのためのDB操作ロジックがCLI層に散らばらず、Application層のUseCaseとして整理されてほしい。そうすれば、テストしやすく拡張しやすい。

#### Acceptance Criteria

1. WHEN CLIがコーパス一覧を表示する必要がある場合 THEN システム SHALL Application層に追加されたUseCase経由で取得する（Domain Repository へ直接アクセスしない）
2. WHEN CLIが実行履歴一覧を表示する必要がある場合 THEN システム SHALL Application層に追加されたUseCase経由で取得する（Domain Repository へ直接アクセスしない）
3. WHEN Requirement 1 を満たすためにコーパス一覧が必要な場合 THEN システム SHALL それを提供するUseCaseを必ず実装する（例: `ListLyricsCorporaUseCase`）
4. WHEN Requirement 2 を満たすために実行履歴一覧が必要な場合 THEN システム SHALL それを提供するUseCaseを必ず実装する（例: `ListMatchRunsUseCase`）
5. WHEN CLIがコーパス/実行履歴の参照を行う場合 THEN システム SHALL 対応するUseCaseを提供する（例: `GetLyricsCorpusUseCase`, `GetMatchRunUseCase`。ただし `query` は既存 `QueryResultsUseCase` を拡張/置換してよい）
6. IF CLIが削除機能を提供する場合 THEN システム SHALL 対応するUseCaseを提供する（例: `DeleteLyricsCorpusUseCase`, `DeleteMatchRunUseCase`）。削除の提供有無はDesignで決めるが、一覧/参照は必須とする
7. WHEN UseCaseが一覧/概要を返す場合 THEN システム SHALL CLI表示に必要な「概要情報」を返せる（例: `lyrics_corpus_id`, `title/artist`, `created_at`、および `run_id`, `timestamp`, `lyrics_corpus_id`, `results_count` 等）
8. WHEN 一覧表示が必要な場合 THEN システム SHALL Domain Repository 契約（または同等の抽象）として「一覧取得」をサポートする（例: コーパス一覧、マッチ実行一覧）。具体的なメソッド名・ページングはDesignで定義する

### Requirement 4: Typer + Rich によるCLI刷新（型安全性・可読性・UX）

**User Story:** CLIユーザーとして、ヘルプやエラーメッセージが分かりやすく、候補一覧が見やすく、入力ミスが減るCLIを使いたい。

#### Acceptance Criteria

1. WHEN ユーザーが `--help` を実行した場合 THEN システム SHALL コマンド/オプション/引数の説明を分かりやすく提示する
2. WHEN ユーザーが不正な値（例: 存在しない `corpus_id` / `run_id`）を指定した場合 THEN システム SHALL 何が不正か・どう直すかを示すエラーメッセージを表示する
3. WHEN 一覧表示（コーパス/実行履歴）を行う場合 THEN システム SHALL Richのテーブル等で視認性高く表示する
4. WHEN ユーザー選択が必要な場合 THEN システム SHALL Rich/Typerのプロンプト等で、選択肢が明確な対話的入力を提供する
5. WHEN CLIをスクリプト/CI等の非対話環境で実行する場合 THEN システム SHALL 対話入力が不要になる経路（ID明示指定）を提供し、対話が必要な状況では明確なエラーを返せる

### Requirement 6: UseCaseの入出力DTOを整備し型安全性を上げる

**User Story:** 開発者として、UseCaseの返り値が `dict`（JSON想定）で曖昧な状態ではなく、DTOで厳密に定義されていてほしい。そうすれば、CLI表示や将来のUI/API拡張で「何が返ってくるか」が安定し、変更に強くなる。

#### Acceptance Criteria

1. WHEN Application層のUseCaseが結果を返す場合 THEN システム SHALL `dict[str, Any]` ではなくDTO（例: `pydantic.BaseModel` / `dataclass`）を返す
2. WHEN `QueryResultsUseCase`（または後継UseCase）が結果を返す場合 THEN システム SHALL `MatchRun` と「解決済み結果（入力トークン・マッチタイプ・採用トークン・モーラ詳細・サマリー等）」をDTOとして提供する
3. WHEN CLIが一覧表示に使用するデータを取得する場合 THEN システム SHALL Domainモデルそのものではなく、表示目的に最適化されたDTO（サマリー/概要）を受け取れる
4. WHEN DTOを導入する場合 THEN システム SHALL テストでDTOのフィールド・型・代表ケース（0件/1件/複数件、mora_combination含む）の振る舞いを検証する

### Requirement 5: 既存利用との互換性・移行容易性

**User Story:** 既存ユーザー/既存テストとして、これまでのコマンド利用方法が大きく壊れずに改善を取り込めてほしい。

#### Acceptance Criteria

1. WHEN ユーザーが従来通り `match` に `corpus_id` を与えて実行する場合 THEN システム SHALL 既存の機能要件（マッチング実行と `run_id` 出力）を維持する
2. WHEN ユーザーが従来通り `query` に `run_id` を与えて実行する場合 THEN システム SHALL 既存の機能要件（結果の表示/出力）を維持する
3. WHEN CLI実装を刷新する場合 THEN システム SHALL 既存のテスト戦略（pytest + ruff、Onion/DDDの依存方向）に従い、テストが追加/更新される

## Non-Functional Requirements

### Code Architecture and Modularity

- **Onion Architectureの依存方向を維持**: Interface → Application → Domain、InfrastructureはDomainへ依存しない
- **Single Responsibility**: 一覧取得/削除などのI/OはUseCaseに寄せ、CLIは入出力整形と呼び出しに集中する
- **Clear Interfaces**: CLI表示用のDTO（概要）を導入する場合、Domainモデルの漏洩を避ける/最小化する
- **Testability**: 新規UseCaseとCLIの主要分岐（省略時一覧/選択、0件、1件、明示指定）をテスト可能にする

### Performance

- 一覧表示は「概要情報」の取得を基本とし、不要な詳細ロード（例: 全トークン展開）を避ける
- 表示件数が多い場合に備え、ソート（例: 新しい順）や件数制限（例: 直近N件）を検討可能にする

### Security

- すべてローカル完結（外部送信なし）を維持する
- ファイル入力の扱いは既存と同等の安全性（パス存在チェック、例外処理）を維持する

### Reliability

- 省略時の候補提示・ソート・デフォルト選択ルールは明確で、再現性がある
- 例外時は非ゼロ終了コードで終了し、原因をユーザーに示す

### Usability

- 一覧表示は識別しやすい列（ID・タイトル/日時など）を持つ
- 対話選択は「番号選択」「ID入力」など誤入力しにくい形式を採用する
- 非対話環境向けに、対話を回避する明示指定ルートを必ず提供する
