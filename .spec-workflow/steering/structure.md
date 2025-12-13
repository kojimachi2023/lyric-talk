# Project Structure

## Directory Organization

このリポジトリは現状 **技術検証（PoC）段階**の実装が中心で、将来的に **DDD + Onion Architecture** へ移行する方針です。

### Current (PoC)

```
lyric-talk/
├── src/                     # アプリ本体（Python パッケージ）
│   ├── __init__.py
│   ├── main.py              # CLI エントリポイント
│   ├── config.py            # 設定（pydantic-settings）
│   ├── lyric_index.py       # 歌詞インデックス生成
│   ├── matcher.py           # マッチングロジック
│   └── mora.py              # 読み正規化/モーラ分割
├── .spec-workflow/          # spec/steering 運用（開発支援）
│   ├── steering/
│   └── templates/
├── pyproject.toml           # 依存/ビルド/テスト/ruff 設定
├── uv.lock                  # uv ロック
├── README.md
├── output.json              # 実行例の出力（成果物）
└── test_lyrics.txt          # 動作確認用の歌詞テキスト例
```

補足:

- Node.js（`package.json`, `pnpm-lock.yaml`, `node_modules/`）は主に **spec-workflow ダッシュボード等の開発支援**用途です。
- テストは `pyproject.toml` の設定上 `tests/` 配下（`test_*.py`）を想定します。

### Planned (DDD + Onion Architecture)

将来的には依存方向を明確化し、ドメインを外部技術から隔離する構成へ段階的に移行します。

```
lyric-talk/
└── src/
    ├── domain/              # エンティティ/値オブジェクト/ドメインサービス
    ├── application/         # ユースケース、DTO、ポート（インターフェース）
    ├── infrastructure/      # NLP/永続化など外部実装
    └── interface/           # CLI /（将来の）API など入力アダプタ
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

- `src/` は Python パッケージとして扱い、同一パッケージ内では **明示的な相対 import**（例: `from .config import settings`）を許容します。
- DDD + Onion 移行後は、**Domain は外部技術（NLP/永続化）に依存しない**ことを原則とします。

## Code Organization Principles

1. **Single Responsibility**: 1ファイル1責務を保つ
2. **Testability**: ロジックを分離し、ユニットテスト可能な形にする
3. **Consistency**: `ruff` による整形・lint と、既存の記述スタイルに揃える

## Module Boundaries

- **Domain**: 純粋なビジネスルール（外部I/Oに依存しない）
- **Application**: ユースケース境界（入力→処理→出力の流れ、DTO/ポート）
- **Infrastructure**: 外部ライブラリ、永続化、I/O 実装
- **Interface**: CLI や（将来の）API

依存方向は原則として「外側 → 内側」で、内側は外側を参照しません。

## Documentation Standards

- 公開関数/クラスには docstring を付ける
- アルゴリズムや前提が複雑な箇所はコメントで補足する
- 大きなモジュールには README（もしくは docstring での概要）を用意する
