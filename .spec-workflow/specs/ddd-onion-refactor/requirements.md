# 要件定義書（Requirements Document）

## Introduction

本ドキュメントは、`lyric-talk`（日本語歌詞を素材として入力文を“歌詞断片の組み合わせ”で再現するCLIツール）を、**DDD（Domain-Driven Design） + Onion Architecture** に沿った構造へ**ゼロベースで再構築**するための要件を定義します。

現状は PoC 的な「CLI → 解析/インデックス化 → マッチング → 出力」の直列パイプラインで実装されており、外部技術（spaCy/GiNZA、ファイルI/O、設定）とドメインロジックが近接しています。現行の `src/` 配下のPythonコードは実験用であるため、本改良では**現行実装に引きずられず**、アーキテクチャに沿って再設計・再実装します。

また、マッチング結果の出力は JSON ファイルではなく **DB（ローカルDB）へ永続化**することを前提とします。

- 依存方向（外側 → 内側）を明確化し、**ドメインを外部技術から隔離**する
- ユースケース境界を明確化し、**テスト容易性**を高める
- 将来的拡張（例: 意味的類似、言い換え、永続化）を「差し替え可能なアダプタ」として実装できる土台を作る

ことです。

### 対象範囲（In Scope）

- `src/` 配下を Onion のレイヤに沿って再編（例: `domain/`, `application/`, `infrastructure/`, `interface/`）
- 既存のユーザー価値（歌詞インデックス化、優先度付きマッチング、説明可能な根拠提示）を維持
- マッチング結果（実行メタデータ/一致根拠/集計）を DB に保存し、参照・再利用できるようにする
- テスト基盤（pytest）を追加し、主要ロジックをユニットテスト可能にする

### 非対象（Out of Scope）

- マッチング精度の大幅な改善や新アルゴリズム導入（本件は「構造改善」が主）
- Web UI / サーバ化
- 外部サービス（ネットワーク）連携を前提とした機能

## Alignment with Product Vision

本改良は `.spec-workflow/steering/product.md` の原則に整合します。

- **Explainability First**: 一致根拠（どの歌詞トークン/行から採ったか、モーラ内訳）を、構造変更後も出力できるようにする
- **Japanese-aware Matching**: 表層形・読み・モーラという日本語特有の手がかりを、ドメインの概念として明示し扱いやすくする
- **Reproducibility & Configurability**: 結果に影響する設定値はユースケース境界で統制し、同一入力で同一結果が得られる設計を保つ

## Requirements

### Requirement 1 — Onionレイヤ構造の導入

**User Story:** As a 開発者, I want Onion Architecture に沿ったディレクトリ/依存関係を導入したい, so that 変更容易性とテスト容易性を高められる

#### Acceptance Criteria

1. WHEN ソースコードを `src/domain`, `src/application`, `src/infrastructure`, `src/interface` に再編する THEN 依存方向は外側→内側に限定され、内側（domain/application）は外側（infrastructure/interface）を import しない SHALL
2. WHEN `src/domain` を単独で import する THEN `spacy`, `pydantic_settings`, `argparse`, ファイルI/O 等の外部技術に依存しない SHALL
3. WHEN ゼロベース再構築を行う THEN 既存のエントリポイントや `src/main.py` に互換性を持たせる必要はなく、CLI のエントリポイントは新アーキテクチャに合わせて再設計される SHALL
4. IF 新しいCLIエントリポイントを提供するために `pyproject.toml` の `[project.scripts]` を変更する必要がある THEN システムはそれを許容し、更新後のエントリポイントで実行できる SHALL

### Requirement 2 — ドメインモデルの明確化（値オブジェクト/エンティティ）

**User Story:** As a 開発者, I want 歌詞・トークン・読み・モーラ・マッチ結果をドメイン概念として定義したい, so that ビジネスルールが外部技術から独立して理解できる

#### Acceptance Criteria

1. WHEN 「読み」「モーラ」「トークン」「歌詞コーパス」「マッチ結果」などの概念を定義する THEN それらは `src/domain` に配置され、I/O やNLP実装詳細を含まない SHALL
2. WHEN ドメインロジック（例: 読み正規化、モーラ分割、マッチ結果の表現）を実装する THEN その入出力は純粋データ（primitive/ dataclass 等）で表現され、外部ライブラリ型（例: spaCy Token）を露出しない SHALL

### Requirement 3 — ユースケース（Application層）の導入

**User Story:** As a 開発者, I want 「歌詞インデックス構築」「入力文マッチング」「結果生成」をユースケースとして分離したい, so that 仕様変更とテストが局所化できる

#### Acceptance Criteria

1. WHEN 歌詞インデックス構築を行う THEN Application層のユースケース（例: `BuildLyricIndex`）が Domain モデルを生成する SHALL
2. WHEN 入力文マッチングを行う THEN Application層のユースケース（例: `MatchTextToLyrics`）が Domain のポリシー（優先度: 表層形→読み→モーラ）に従って結果を生成する SHALL
3. IF NLP トークナイズ/読み取得の実装を差し替える必要がある THEN Application層は Port（インターフェース）経由で利用し、具体実装は Infrastructure に置く SHALL

### Requirement 4 — Port/Adapter（依存性逆転）の導入

**User Story:** As a 開発者, I want spaCy/GiNZA やファイルI/Oをアダプタとして差し替え可能にしたい, so that 将来の拡張やテスト用の代替実装が容易になる

#### Acceptance Criteria

1. WHEN Application層が「形態素解析・読み取得」を必要とする THEN `NlpPort`（名称は任意）を介して呼び出す SHALL
2. WHEN Application層が「歌詞入力」を必要とする THEN `LyricsSourcePort`（名称は任意）を介して呼び出す SHALL
3. WHEN Application層が「マッチング結果の永続化/参照」を必要とする THEN `MatchingResultRepositoryPort`（名称は任意）を介して呼び出す SHALL
4. IF テストで外部依存を排除したい THEN fake/stub 実装を用いてユースケースが実行できる SHALL

### Requirement 5 — CLI互換の維持（Interface層）

**User Story:** As a ユーザー, I want 既存CLIの使い方を変えずに利用したい, so that 破壊的変更なくアップデートできる

#### Acceptance Criteria

1. WHEN ユーザーが `--lyrics` または `--lyrics-text` と `--text` を指定して実行する THEN マッチングが実行され、結果がDBに保存される SHALL
2. IF 引数のバリデーションエラーが発生する THEN CLI はユーザーに理解可能なメッセージを表示し、異常終了する SHALL

### Requirement 6 — 結果のDB永続化と説明可能な参照

**User Story:** As a ユーザー, I want マッチング結果がJSONではなくDBに保存され、後から参照できてほしい, so that 結果の根拠確認や比較ができる

#### Acceptance Criteria

1. WHEN マッチングが完了する THEN システムは実行（run）と結果をローカルDBへ永続化する SHALL
2. WHEN 永続化を行う THEN システムは少なくとも以下を保存できる SHALL
   - 実行メタデータ（timestamp, input_text, 使用した設定値 等）
   - 歌詞Token（表層/読み/歌詞内の位置など、歌詞素材を表すレコード）
   - マッチング結果（入力Tokenごとの match_type と根拠参照）
3. WHEN マッチング結果を保存する THEN 「歌詞のどのTokenを取ってきたか」を**歌詞Tokenテーブルへのリレーション（参照）**として保持し、マッチング結果自体は歌詞Tokenの表層/読み/位置などの情報を直接保持しない SHALL
4. WHEN ユーザー向けに結果を返却する THEN Application層/DomainService層はリレーションを辿って必要な歌詞Token情報を解決し、説明可能な形で返却できる SHALL
5. WHEN DBとCRUDする必要がある THEN Application層はリポジトリ（Port）経由で操作し、具体DB実装はInfrastructure層に置く SHALL
6. IF DB製品を指定する必要がある THEN 既存依存関係に合わせ、ローカル永続化には DuckDB を採用する SHALL

### Requirement 7 — ゼロベース再構築（既存実験コードの撤去）

**User Story:** As a 開発者, I want 既存の実験用コードを前提にせずゼロから設計・実装したい, so that アーキテクチャの整合性を最優先にできる

#### Acceptance Criteria

1. WHEN 実装フェーズを開始する THEN `src/` 配下の既存Python実装（実験コード）は削除/置換され、新アーキテクチャに沿ったコードで再構成される SHALL
2. WHEN 再構築後にCLIを実行する THEN `--lyrics`/`--lyrics-text` と `--text` の入力に対してマッチングが行え、結果がDBに保存される SHALL

### Requirement 8 — テストと静的解析の前提化

**User Story:** As a 開発者, I want リファクタ中に挙動退行を検知したい, so that 安心して構造変更を進められる

#### Acceptance Criteria

1. WHEN ユニットテストを実行する THEN `uv run pytest` でテストが実行できる SHALL
2. WHEN リント/フォーマットを実行する THEN `uv run ruff check .` / `uv run ruff check . --fix` で問題が検出・修正できる SHALL
3. IF ドメイン/ユースケースを変更する THEN 対応するテストが追加/更新される SHALL

## Non-Functional Requirements

### Code Architecture and Modularity

- **依存方向の一貫性**: 内側（Domain/Application）は外側（Infrastructure/Interface）に依存しない
- **単一責務**: 1モジュール1責務（例: モーラ処理、インデックス構築、マッチング、I/O）
- **明確な契約**: Port（インターフェース）/DTO を介し、レイヤ間のデータ形式を明示する
- **置換可能性**: NLP や入出力を差し替え可能にし、将来の拡張（埋め込み/永続化）に備える

### Performance

- spaCy + GiNZA のロードを必要以上に繰り返さない（プロセス内での再利用を前提）
- 構造変更により、典型的入力（数百〜数千トークン）での体感性能を著しく悪化させない

### Security

- デフォルトでネットワーク送信を行わない（ローカル処理を維持）
- 入力テキストは任意文字列であるため、パス取り扱い・ファイル出力は安全なデフォルトを維持する

### Reliability

- 同一入力（歌詞・設定・入力文）に対して同一結果を返す（再現性）
- エラー時の例外は握りつぶさず、CLI として適切に通知する

### Usability

- CLIヘルプ（`-h/--help`）で引数の意味が理解できる
- DBに保存された結果を、ユーザーが後処理しやすい形で参照・取得できる（機械可読、説明可能）
