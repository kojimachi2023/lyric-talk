# ITAコーパス分析パイプライン - コンテキスト情報

## 1. eval配下の既存ファイル構成

### ファイル一覧
```
eval/
├── .env.sample              # 環境変数テンプレート
├── .env                     # 環境変数（Spotify/Genius認証）
├── collect_lyrics.py        # 歌詞収集パイプライン
├── register_lyrics_to_db.py # DB登録パイプライン
├── lyrics/                  # 歌詞JSONファイル保存先
│   ├── 2021/
│   ├── 2022/
│   ├── 2023/
│   ├── 2024/
│   └── 2025/
└── results/                 # (現在は空) 分析結果出力先

```

### 各ファイルの役割

**collect_lyrics.py**
- Spotify API + LyricsGenius を使用して日本のヒット曲歌詞を収集
- SpotifyJapanHitsFetcher: 年別のJ-POPヒット曲検索
- LyricsCollector: 歌詞テキスト取得
- 出力: eval/lyrics/{YYYY}/...json形式

**register_lyrics_to_db.py**
- collect_lyrics.py で収集した歌詞JSONをDB登録
- LyricsRegistrator クラスが RegisterLyricsUseCase を使用
- 音声解析（ja_ginza）を行いながら登録
- 出力: lyric_talk.duckdb への保存

**eval/results/**
- 分析パイプラインの結果出力用
- 現在は空のディレクトリ

---

## 2. 各Use Caseの入出力仕様

### ListLyricsCorporaUseCase
**ファイル**: src/application/use_cases/list_lyrics_corpora.py

**入力**:
- `limit: int = 10` - 取得する最大件数
- `max_preview_token: int = 10` - プレビュー用トークン数

**出力**:
- `List[LyricsCorpusSummaryDto]` 
  - lyrics_corpus_id: str
  - title: str
  - artist: str
  - created_at: datetime
  - token_count: int
  - preview_text: str

**用途**: CLI対話選択機能で保存済みコーパス一覧を表示

---

### MatchTextUseCase
**ファイル**: src/application/use_cases/match_text.py

**入力**:
- `input_text: str` - マッチング対象テキスト
- `lyrics_corpus_id: str` - 検索対象コーパスID

**出力**:
- `str` - run_id (マッチング実行ID: "run_{uuid_hex}")

**処理フロー**:
1. 入力テキストをトークン化（NlpService）
2. MatchingStrategy で各トークンを歌詞と照合
3. MatchRun エンティティ + MatchResult を生成・保存
4. run_id を返す

**使用サービス**:
- NlpService: テキスト→トークン化
- MatchingStrategy: トークン照合
- MatchRepository: 結果永続化

---

### QueryResultsUseCase
**ファイル**: src/application/use_cases/query_results.py

**入力**:
- `run_id: str` - マッチング実行ID

**出力**:
- `Optional[QueryResultsDto]`
  - run_id, lyrics_corpus_id, timestamp, input_text
  - items: List[QueryMatchItemDto]
    - input: InputTokenDto (surface, reading)
    - match_type: MatchType (EXACT_SURFACE, EXACT_READING, MORA_COMBINATION, NO_MATCH)
    - chosen_lyrics_tokens: List[LyricTokenDto]
    - mora_trace: MoraTraceDto (モーラマッチング詳細)
  - reconstruction_steps: List[ReconstructionStepDto]
  - stats: MatchStatsDto (マッチ種別別統計)

**用途**: マッチング結果を詳細に取得・表示

---

## 3. ITAコーパスのデータフォーマット詳細

### JSONフォーマット（歌詞ファイル）
```json
{
  "artist": "アーティスト名",
  "title": "曲名",
  "album": "アルバム名",
  "release_date": "YYYY-MM-DD",
  "spotify_id": "Spotify ID",
  "lyrics": "改メ口の中くぐり抜け...\n肌を突き刺す粒子..."
}
```

### DB スキーマ

**lyrics_corpus** テーブル
- corpus_id (PK): VARCHAR
- title: VARCHAR
- artist: VARCHAR
- content_hash: VARCHAR (UNIQUE)
- created_at: TIMESTAMP

**lyric_tokens** テーブル
- token_id (PK): VARCHAR
- lyrics_corpus_id (FK): VARCHAR
- surface: VARCHAR (表層形)
- reading: VARCHAR (読み/カタカナ)
- lemma: VARCHAR (見出し語)
- pos: VARCHAR (品詞)
- line_index: INTEGER
- token_index: INTEGER
- moras_json: VARCHAR (JSON: モーラ配列)
- インデックス: (lyrics_corpus_id, surface), (lyrics_corpus_id, reading)

**match_runs** テーブル
- run_id (PK): VARCHAR
- lyrics_corpus_id (FK): VARCHAR
- input_text: VARCHAR
- timestamp: TIMESTAMP
- config_json: VARCHAR

**match_results** テーブル
- result_id (PK): VARCHAR
- run_id (FK): VARCHAR
- token_id (FK): VARCHAR (nullable)
- input_token: VARCHAR
- input_reading: VARCHAR
- match_type: VARCHAR (EXACT_SURFACE|EXACT_READING|MORA_COMBINATION|NO_MATCH)
- matched_token_ids_json: VARCHAR (JSON)
- mora_details_json: VARCHAR (JSON)
- input_token_index: INTEGER

---

## 4. 編集距離計算に利用可能なライブラリ

### 推奨ライブラリ: **rapidfuzz** (既にインストール済み)

**pyproject.toml での指定**:
```python
"rapidfuzz>=3.0.0",
```

**主要 API**:
- `rapidfuzz.distance.Levenshtein.distance(s1, s2)` - 編集距離
- `rapidfuzz.distance.Levenshtein.normalized_similarity(s1, s2)` - 0-100 の類似度スコア
- `rapidfuzz.fuzz.ratio(s1, s2)` - 高速な類似度計算
- `rapidfuzz.fuzz.partial_ratio(s1, s2)` - 部分マッチ（推奨）

**理由**:
- C 実装による高速処理（複数曲の処理に最適）
- 日本語テキスト対応
- NumPy 統合で配列処理対応

---

## 5. 並列処理方法の推奨（制約: 1曲 = 1CPU）

### 制約分析
- **ボトルネック**: NLP処理（ja_ginza）がCPU集約的
- **単位**: 1 corpus_id = 1曲分 → 1 CPUプロセス

### 推奨アーキテクチャ

**オプション 1: ProcessPoolExecutor (推奨)**
```python
from concurrent.futures import ProcessPoolExecutor
# 各曲を独立プロセスで処理
# 共有メモリ: DuckDB接続（自動的にファイルロック対応）
```

**オプション 2: multiprocessing.Pool**
```python
from multiprocessing import Pool
# 古典的なマップ・リデュース
# 簡潔な API
```

### pyproject.toml の状態
- Python 3.12+ 標準ライブラリに `concurrent.futures`, `multiprocessing` は組込済み
- **追加インストール不要**

### 実装パターン
```python
# 曲単位でタスク化
corpus_ids = ["corpus_1", "corpus_2", ...]

def analyze_corpus(corpus_id: str) -> Dict:
    # 1曲分の分析（1CPUで実行）
    return result

# 並列実行
with ProcessPoolExecutor(max_workers=cpu_count()) as executor:
    results = list(executor.map(analyze_corpus, corpus_ids))
```

### DB アクセス上の注意
- DuckDB は複数プロセスからの読み取り可能
- 書き込みはシリアライズ自動実行（パフォーマンス低下注意）
- 結果保存は単一プロセスで集約を推奨

---

## 6. 既存のインフラストラクチャ層（DB操作）の実装詳細

### DuckDB リポジトリ実装

**DuckDBLyricsRepository** (lyrics_repository.py)
- `save(lyrics_corpus)` → corpus_id を返す
- `find_by_id(corpus_id)` → LyricsCorpus
- `find_by_content_hash(hash)` → LyricsCorpus
- `find_by_title(title)` → List[LyricsCorpus]
- `delete(corpus_id)` → None
- `list_lyrics_corpora(limit)` → List[LyricsCorpus] (新順)
- 接続: 自動オープン/クローズ（メソッド内）

**DuckDBLyricTokenRepository** (lyric_token_repository.py)
- `save(token)` → None
- `save_many(tokens)` → None (バッチ挿入)
- `find_by_surface(surface, corpus_id)` → List[LyricToken]
- `find_by_reading(reading, corpus_id)` → List[LyricToken]
- `find_by_mora(mora, corpus_id)` → List[LyricToken]
- `list_by_lyrics_corpus_id(corpus_id, limit)` → List[LyricToken]
- `count_by_lyrics_corpus_id(corpus_id)` → int
- インデックス利用: 表層形・読み・モーラで高速検索

**DuckDBMatchRepository** (match_repository.py)
- `save(match_run: MatchRun)` → run_id (集約パターン)
  - MatchRun + 子 MatchResults を一括保存
  - トランザクション内で実行
- `find_by_id(run_id)` → Optional[MatchRun]
  - MatchRun と全 MatchResults を復元
- `list_by_lyrics_corpus_id(corpus_id, limit)` → List[MatchRun]

### 接続パターン
```python
# スレッドセーフな実装
def _get_connection(self) -> duckdb.DuckDBPyConnection:
    return duckdb.connect(self.db_path)  # 毎回新規作成
    # メソッド内で finally: conn.close() で必ず閉じる
```

### DB初期化
**schema.py の initialize_database(db_path)**
- テーブル作成（IF NOT EXISTS）
- インデックス作成（IF NOT EXISTS）
- 冪等性あり（複数回実行可）

### パフォーマンス特性
- **読み取り**: インデックス利用で高速 (O(log n))
- **書き込み**: 単一接続でシリアライズ
- **大量書き込み**: save_many() で executemany() 使用

---

## 7. 既存テストとマッチング戦略

### MatchingStrategy の 3段階マッチング
ファイル: src/domain/services/matching_strategy.py

**優先度順**:
1. **EXACT_SURFACE**: 表層形完全一致
2. **EXACT_READING**: 読み完全一致（カタカナ）
3. **MORA_COMBINATION**: モーラ組み合わせ（前方マッチング）
   - 入力の各モーラを歌詞から独立して検索
   - max_mora_length (デフォルト 10) で上限制御
4. **NO_MATCH**: マッチなし

### テスト範囲
- tests/unit/domain/test_matching_strategy.py
- EXACT_SURFACE, EXACT_READING, MORA_COMBINATION をカバー

---

## パイプライン設計メモ

ITAコーパス分析パイプラインの設計で推奨される組み合わせ:

1. **入力**: ListLyricsCorporaUseCase で候補コーパス取得
2. **処理**: ProcessPoolExecutor で並列実行
   - 各プロセス: MatchTextUseCase で 1 曲分分析
   - 出力: run_id リスト
3. **集約**: QueryResultsUseCase で各 run_id から結果取得
4. **分析**: rapidfuzz で類似度計算（オプション）
5. **保存**: eval/results/ に結果出力（JSON/CSV）

制約「1曲 = 1CPU」を満たし、スケーラビリティも確保できます。
