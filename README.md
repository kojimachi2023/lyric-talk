# lyric-talk

歌詞テキストに対してユーザー入力をマッチングし、読み（モーラ）レベルでの類似判定を行う日本語テキスト処理ツールです。

## 概要

`lyric-talk`は、以下の機能を提供します:

1. **歌詞の登録 (register)**: テキストファイルまたは標準入力から歌詞を登録
2. **テキストマッチング (match)**: 入力テキストを登録済み歌詞とマッチング
3. **結果の照会 (query)**: マッチング結果の詳細表示

DDD (Domain-Driven Design) とOnion Architectureに基づいた設計で、保守性と拡張性を重視しています。

## インストール

```bash
# リポジトリのクローン
git clone <repository-url>
cd lyric-talk

# uvを使用した依存関係のインストール
uv sync
```

## 使い方

### 基本コマンド

#### 1. 歌詞の登録

ファイルから歌詞を登録:

```bash
uv run lyric-talk register /path/to/lyrics.txt
```

標準入力から登録:

```bash
echo "東京の空は青い
桜が咲いている" | uv run lyric-talk register -
```

登録に成功すると、`corpus_id`が出力されます（例: `corpus_abc123...`）。

#### 2. 登録済み歌詞コーパスの一覧表示

```bash
uv run lyric-talk corpus list
```

表示される情報:

- Corpus ID: コーパスの識別子
- Title/Artist: タイトル・アーティスト（登録されている場合）
- Created: 作成日時
- Tokens: トークン数
- Preview: 歌詞の先頭プレビュー

#### 3. テキストマッチング

**対話的に使用（corpus_idを省略）:**

```bash
uv run lyric-talk match --text "東京は青い空です"
```

- 登録済みコーパスが0件の場合: エラーメッセージが表示され、先に`register`が必要であることが案内されます
- 登録済みコーパスが1件の場合: 自動的にそのコーパスが選択されます
- 登録済みコーパスが複数の場合: 一覧が表示され、どのコーパスを使用するか選択できます

**明示的にcorpus_idを指定:**

```bash
uv run lyric-talk match <corpus_id> --text "東京は青い空です"
```

ファイルから入力:

```bash
uv run lyric-talk match <corpus_id> /path/to/input.txt
```

マッチングに成功すると、`run_id`が出力されます（例: `run_xyz789...`）。

#### 4. マッチ実行履歴の一覧表示

```bash
uv run lyric-talk run list
```

表示される情報:

- Run ID: 実行の識別子
- Timestamp: 実行日時
- Corpus ID: 使用したコーパス
- Input: 入力テキスト
- Results: マッチ結果数

#### 5. マッチング結果の照会

**対話的に使用（run_idを省略）:**

```bash
uv run lyric-talk query
```

- 実行履歴が0件の場合: エラーメッセージが表示され、先に`match`が必要であることが案内されます
- 実行履歴が複数ある場合: 一覧が表示され、どの実行結果を表示するか選択できます

**明示的にrun_idを指定:**

```bash
uv run lyric-talk query <run_id>
```

結果表示:

- ツリー形式で「入力トークン → マッチタイプ → 採用された歌詞トークン」を階層表示
- `exact_surface`: 表層形が完全一致
- `exact_reading`: 読みが完全一致
- `mora_combination`: モーラ組み合わせマッチ（モーラ詳細も表示）
- サマリー: 採用されたトークンから再構成されたテキスト・読み

### 非対話環境での使用（スクリプト・CI）

非対話環境（TTYでない環境）で対話的な選択が必要な状況では、明確なエラーメッセージが表示されます。

**推奨される使い方:**

```bash
# 事前にIDを取得
CORPUS_ID=$(uv run lyric-talk register lyrics.txt)
RUN_ID=$(uv run lyric-talk match $CORPUS_ID --text "入力テキスト")
uv run lyric-talk query $RUN_ID
```

または、`corpus list`と`run list`でIDを確認してから明示的に指定:

```bash
# 一覧からIDをコピー
uv run lyric-talk corpus list
uv run lyric-talk run list

# IDを明示的に指定
uv run lyric-talk match corpus_abc123... --text "入力"
uv run lyric-talk query run_xyz789...
```

### ヘルプの表示

各コマンドの詳細なヘルプ:

```bash
uv run lyric-talk --help
uv run lyric-talk register --help
uv run lyric-talk match --help
uv run lyric-talk query --help
```

## 開発

### テストの実行

```bash
# 全テストを実行
uv run pytest

# 特定のテストを実行
uv run pytest tests/unit/application/
uv run pytest tests/integration/

# カバレッジ付きで実行
uv run pytest --cov=src --cov-report=html
```

### コード品質チェック

```bash
# Lintチェック
uv run ruff check .

# 自動修正
uv run ruff check . --fix
```

## アーキテクチャ

本プロジェクトはOnion Architectureに基づいており、以下の層で構成されています:

- **Domain層**: ビジネスロジックとドメインモデル
- **Application層**: ユースケースとDTO
- **Infrastructure層**: データベース・NLP実装
- **Interface層**: CLI

詳細は`src/`ディレクトリ内の各層を参照してください。

## 依存関係

主要な依存ライブラリ:

- **spaCy + GiNZA**: 日本語形態素解析・品詞タグ付け
- **DuckDB**: 軽量で高速な組込みデータベース
- **Typer**: 型安全でユーザーフレンドリーなCLI
- **Rich**: 美しいターミナル出力

## ライセンス

[ライセンス情報を記載]
