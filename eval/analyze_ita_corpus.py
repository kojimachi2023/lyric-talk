"""
ITAコーパス分析パイプライン

ITAコーパスの全文を、DBに登録された歌詞コーパスと照合し、
マッチング精度（編集距離）を評価します。

入力: ITAコーパスファイル（例: EMOTION100_001:えっ嘘でしょ。,エッウソデショ。）
出力: eval/results/{corpus_id}.json
"""

import json
import sys
from dataclasses import dataclass
from pathlib import Path

from tqdm import tqdm

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from rapidfuzz.distance.Levenshtein import normalized_distance
from rapidfuzz.process import extract

from src.application.use_cases.list_lyrics_corpora import ListLyricsCorporaUseCase
from src.application.use_cases.match_text import MatchTextUseCase
from src.application.use_cases.query_results import QueryResultsUseCase
from src.infrastructure.config.settings import Settings
from src.infrastructure.database.duckdb_unit_of_work import DuckDBUnitOfWork
from src.infrastructure.nlp.spacy_nlp_service import SpacyNlpService


@dataclass
class ItaSentence:
    """ITAコーパスの1文を表すデータクラス"""

    sentence_id: str
    text: str
    reading: str


def load_ita_corpus(file_path: Path) -> list[ItaSentence]:
    """ITAコーパスファイルを読み込む

    フォーマット: SENTENCE_ID:テキスト,カタカナ読み

    Args:
        file_path: ITAコーパスファイルのパス

    Returns:
        ItaSentenceのリスト
    """
    sentences: list[ItaSentence] = []

    with open(file_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # SENTENCE_ID:テキスト,カタカナ読み の形式をパース
            if ":" not in line:
                continue

            sentence_id, rest = line.split(":", 1)
            if "," not in rest:
                continue

            text, reading = rest.rsplit(",", 1)
            sentences.append(
                ItaSentence(
                    sentence_id=sentence_id.strip(),
                    text=text.strip(),
                    reading=reading.strip(),
                )
            )

    return sentences


def process_single_ita(
    ita: ItaSentence,
    corpus_id: str,
    db_path: str,
    max_mora_length: int,
    nlp_model: str,
) -> dict | None:
    """単一のITA文を処理する（並列処理用）

    Args:
        ita: ITA文
        corpus_id: 歌詞コーパスID
        db_path: DuckDBデータベースのパス
        max_mora_length: 最大モーラ長
        nlp_model: NLPモデル名

    Returns:
        編集距離情報の辞書、またはNone
    """
    nlp_service = SpacyNlpService(model_name=nlp_model)
    unit_of_work = DuckDBUnitOfWork(db_path=db_path)

    with unit_of_work:
        match_use_case = MatchTextUseCase(
            nlp_service=nlp_service,
            unit_of_work=unit_of_work,
            max_mora_length=max_mora_length,
        )
        query_use_case = QueryResultsUseCase(
            unit_of_work=unit_of_work,
        )

        # マッチング実行
        run_id = match_use_case.execute(ita.text, corpus_id)

        # 結果取得・保存
        query_result = query_use_case.execute(run_id)
        if query_result is None:
            return None

        # 編集距離を計算して集計
        dist = extract(
            query=ita.reading,
            choices=[query_result.summary.reconstructed_reading],
            scorer=normalized_distance,
        )

        return {
            "ita_text": ita.text,
            "ita_reading": ita.reading,
            "matched_reading": query_result.summary.reconstructed_reading,
            "norm_distance": float(dist[0][1]),
            "similarity": 1.0 - float(dist[0][1]),
        }


def analyze_corpus(ita_corpus_path, db_path) -> dict:
    """1曲分のコーパスに対してITA文全体のマッチング分析を実行

    Args:
        ita_corpus_path: ITAコーパスファイルのパス
        db_path: DuckDBデータベースのパス

    Returns:
        分析結果の辞書
    """

    # 設定を読み込み
    settings = Settings(db_path=db_path)
    nlp_service = SpacyNlpService(model_name=settings.nlp_model)

    # Unit of Workを初期化
    unit_of_work = DuckDBUnitOfWork(db_path=db_path)

    with unit_of_work:
        corpora_use_case = ListLyricsCorporaUseCase(
            unit_of_work=unit_of_work,
        )

        # 現在DBに入っている歌詞コーパスのID一覧を取得
        corpora = corpora_use_case.execute(limit=1000)

        # ITAコーパスを取得・配列に分離
        ita_corpus_texts = load_ita_corpus(Path(ita_corpus_path))

        # 曲毎にITAコーパスの各文への編集距離を計算
        result = []

        for corpus in corpora:
            # Use caseを初期化
            match_use_case = MatchTextUseCase(
                nlp_service=nlp_service,
                unit_of_work=unit_of_work,
                max_mora_length=settings.max_mora_length,
            )
            query_use_case = QueryResultsUseCase(
                unit_of_work=unit_of_work,
            )
            corpus_id = corpus.lyrics_corpus_id
            title = corpus.title
            artist = corpus.artist

            distances = []

            for ita in tqdm(ita_corpus_texts):
                # マッチング実行
                run_id = match_use_case.execute(ita.text, corpus_id)

                # 結果取得・保存
                query_result = query_use_case.execute(run_id)
                if query_result is None:
                    continue

                # 編集距離を計算して集計
                dist = extract(
                    query=ita.reading,
                    choices=[query_result.summary.reconstructed_reading],
                    scorer=normalized_distance,
                )
                distances.append(
                    {
                        "ita_text": ita.text,
                        "ita_reading": ita.reading,
                        "matched_reading": query_result.summary.reconstructed_reading,
                        "norm_distance": float(dist[0][1]),
                        "similarity": 1.0 - float(dist[0][1]),
                    }
                )
            result.append(
                {
                    "lyrics_corpus_id": corpus_id,
                    "title": title,
                    "artist": artist,
                    "distances": distances,
                }
            )

        return result


if __name__ == "__main__":
    ita_corpus_file = Path("eval/ita_corpus.txt")
    db_file = "lyric_talk.duckdb"
    output_file = Path("eval/results/ita_corpus_analysis.json")

    analysis_result = analyze_corpus(ita_corpus_file, db_file)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(analysis_result, f, ensure_ascii=False, indent=2)

    print(f"Analysis results saved to {output_file}")
