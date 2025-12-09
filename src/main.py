"""
CLI エントリーポイント: 歌詞と文章を入力として受け取り、結果をJSONファイルに出力
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

import spacy

from .config import settings
from .lyric_index import LyricIndex
from .matcher import Matcher


def main() -> None:
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description="歌詞から特定の文章を再現するテキストマッチングプログラム"
    )
    parser.add_argument(
        "--lyrics",
        "-l",
        type=str,
        help="歌詞ファイルのパス（テキストファイル）",
    )
    parser.add_argument(
        "--lyrics-text",
        "-lt",
        type=str,
        help="歌詞テキスト（直接入力）",
    )
    parser.add_argument(
        "--text",
        "-t",
        type=str,
        required=True,
        help="再現したい文章",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="output.json",
        help="出力JSONファイルのパス（デフォルト: output.json）",
    )
    parser.add_argument(
        "--max-mora-length",
        type=int,
        default=None,
        help=f"モーラ組み合わせの最大長（デフォルト: {settings.max_mora_length}）",
    )

    args = parser.parse_args()

    # 設定の上書き
    if args.max_mora_length is not None:
        settings.max_mora_length = args.max_mora_length

    # 歌詞の読み込み
    if args.lyrics:
        lyrics_path = Path(args.lyrics)
        if not lyrics_path.exists():
            print(f"エラー: 歌詞ファイルが見つかりません: {args.lyrics}")
            return
        lyrics = lyrics_path.read_text(encoding="utf-8")
    elif args.lyrics_text:
        lyrics = args.lyrics_text
    else:
        print("エラー: --lyrics または --lyrics-text のいずれかを指定してください")
        return

    print("spaCy + GiNZA モデルをロード中...")
    nlp = spacy.load("ja_ginza")

    print("歌詞をインデックス化中...")
    lyric_index = LyricIndex.from_lyrics(lyrics, nlp=nlp)
    print(f"  トークン数: {len(lyric_index.tokens)}")
    print(f"  ユニーク表層形: {len(lyric_index.get_all_surfaces())}")
    print(f"  ユニーク読み: {len(lyric_index.get_all_readings())}")
    print(f"  ユニークモーラ: {len(lyric_index.mora_set)}")

    print("マッチングエンジンを初期化中...")
    matcher = Matcher(lyric_index, nlp=nlp)

    print(f"マッチング実行中: '{args.text}'")
    results = matcher.match(args.text)

    # 結果をJSONに変換
    metadata = {
        "timestamp": datetime.now().isoformat(),
        "input_text": args.text,
        "tokenized_input": [
            {
                "surface": r.input_token,
                "reading": r.input_reading,
            }
            for r in results
        ],
        "lyrics_source": args.lyrics if args.lyrics else "(direct input)",
        "settings": {
            "max_mora_length": settings.max_mora_length,
        },
    }
    input_stats = {
        "total_tokens": len(lyric_index.tokens),
        "unique_surfaces": len(lyric_index.get_all_surfaces()),
        "unique_readings": len(lyric_index.get_all_readings()),
        "unique_moras": len(lyric_index.mora_set),
    }

    # マッチング結果から最終出力テキストを生成
    matched_text = "".join(r.get_output_text() for r in results)

    # マッチタイプ別の集計
    match_type_counts: dict[str, int] = {}
    for r in results:
        mt = r.match_type.value
        match_type_counts[mt] = match_type_counts.get(mt, 0) + 1

    results_data = {
        "matched_text": matched_text,
        "matched_tokens": [r.to_dict() for r in results],
        "summary": {
            "total_tokens": len(results),
            "matched": sum(1 for r in results if r.match_type.value != "no_match"),
            "match_types": match_type_counts,
        },
    }

    output_data = {
        "metadata": metadata,
        "input_stats": input_stats,
        "results": [results_data],
    }

    # JSONファイルに出力
    output_path = Path(args.output)
    output_path.write_text(
        json.dumps(output_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"結果を出力しました: {output_path}")
    print("\n=== 最終出力テキスト ===")
    print(matched_text)


if __name__ == "__main__":
    main()
