"""
歌詞DB登録パイプライン

collect_lyrics.py で収集した歌詞JSONファイルを読み込んで、
RegisterLyricsUseCase を使用してDB に登録します。
"""

import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.application.use_cases.register_lyrics import RegisterLyricsUseCase
from src.domain.repositories.lyric_token_repository import LyricTokenRepository
from src.domain.repositories.lyrics_repository import LyricsRepository
from src.domain.services.nlp_service import NlpService
from src.infrastructure.config.settings import Settings
from src.infrastructure.database.duckdb_lyric_token_repository import (
    DuckDBLyricTokenRepository,
)
from src.infrastructure.database.duckdb_lyrics_repository import (
    DuckDBLyricsRepository,
)
from src.infrastructure.database.schema import initialize_database
from src.infrastructure.nlp.spacy_nlp_service import SpacyNlpService


class LyricsRegistrator:
    """DB に歌詞を登録するクラス"""

    def __init__(
        self,
        settings: Settings,
    ):
        """Initialize registrator with dependencies.

        Args:
            settings: Application settings
        """
        self.settings = settings

        # Initialize dependencies
        self.nlp_service: NlpService = SpacyNlpService(model_name=settings.nlp_model)
        self.lyrics_repository: LyricsRepository = DuckDBLyricsRepository(db_path=settings.db_path)
        self.lyric_token_repository: LyricTokenRepository = DuckDBLyricTokenRepository(
            db_path=settings.db_path
        )

        # Initialize use case
        self.use_case = RegisterLyricsUseCase(
            nlp_service=self.nlp_service,
            lyrics_repository=self.lyrics_repository,
            lyric_token_repository=self.lyric_token_repository,
        )

    def register_lyrics_from_json(self, json_path: Path) -> str | None:
        """
        JSONファイルから歌詞を読み込んで DB に登録

        Args:
            json_path: JSONファイルのパス

        Returns:
            登録された corpus_id、失敗時は None
        """
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            lyrics_text = data.get("lyrics", "").strip()
            artist = data.get("artist", "").strip()
            title = data.get("title", "").strip()

            if not lyrics_text:
                print(f"⚠️  スキップ: {json_path.name} (歌詞が空)")
                return None

            # Register to DB
            corpus_id = self.use_case.execute(lyrics_text, artist=artist, title=title)
            return corpus_id

        except json.JSONDecodeError as e:
            print(f"❌ JSON解析エラー: {json_path.name} - {e}")
            return None
        except Exception as e:
            print(f"❌ 登録エラー: {json_path.name} - {e}")
            return None

    def register_all_lyrics(
        self, lyrics_dir: Path, years: list[int] | None = None
    ) -> dict[int, dict[str, int]]:
        """
        指定ディレクトリ配下の全JSONファイルから歌詞を登録

        Args:
            lyrics_dir: 歌詞JSONファイルのディレクトリ (eval/lyrics)
            years: 登録対象の年リスト (None の場合は全年)

        Returns:
            年ごとの登録統計
        """
        if not lyrics_dir.exists():
            raise ValueError(f"Lyrics directory not found: {lyrics_dir}")

        # 登録対象の年ディレクトリを取得
        year_dirs = sorted([d for d in lyrics_dir.iterdir() if d.is_dir() and d.name.isdigit()])

        if years:
            year_dirs = [d for d in year_dirs if int(d.name) in years]

        stats: dict[int, dict[str, int]] = {}

        for year_dir in year_dirs:
            year = int(year_dir.name)
            print(f"\n{'=' * 60}")
            print(f"処理中: {year}")
            print(f"{'=' * 60}")

            json_files = sorted(year_dir.glob("*.json"))
            success_count = 0
            skip_count = 0
            error_count = 0

            for i, json_file in enumerate(json_files, 1):
                try:
                    corpus_id = self.register_lyrics_from_json(json_file)

                    if corpus_id:
                        success_count += 1
                        print(f"✅ {i}/{len(json_files)}: {json_file.name}")
                        print(f"   Corpus ID: {corpus_id}")
                    else:
                        skip_count += 1

                except KeyboardInterrupt:
                    print("\n⚠️  ユーザーによる中断")
                    raise

            stats[year] = {
                "total": len(json_files),
                "success": success_count,
                "skip": skip_count,
                "error": error_count,
            }

            print(f"\n{year} の統計:")
            print(f"  総数: {len(json_files)}")
            print(f"  登録: {success_count}")
            print(f"  スキップ: {skip_count}")
            print(f"  エラー: {error_count}")

        return stats


def main():
    """メイン処理"""
    print("=" * 60)
    print("歌詞DB登録パイプライン")
    print("=" * 60)

    # 設定を読み込み
    settings = Settings()
    print("\n設定:")
    print(f"  DB パス: {settings.db_path}")
    print(f"  NLP モデル: {settings.nlp_model}")

    # DB 初期化
    initialize_database(settings.db_path)

    # 登録処理を実行
    try:
        registrator = LyricsRegistrator(settings=settings)

        # eval/lyrics ディレクトリを指定
        lyrics_dir = Path(__file__).parent / "lyrics"

        # 全年度のデータを登録
        stats = registrator.register_all_lyrics(lyrics_dir)

        # 最終結果を表示
        print("\n" + "=" * 60)
        print("登録完了!")
        print("=" * 60)

        total_lyrics = sum(stat["total"] for stat in stats.values())
        total_success = sum(stat["success"] for stat in stats.values())
        total_skip = sum(stat["skip"] for stat in stats.values())
        total_error = sum(stat["error"] for stat in stats.values())

        print("\n総計:")
        print(f"  処理済み: {total_success} / {total_lyrics}")
        print(f"  スキップ: {total_skip}")
        print(f"  エラー: {total_error}")

        print("\n年ごとの統計:")
        for year in sorted(stats.keys()):
            stat = stats[year]
            print(
                f"  {year}: {stat['success']}/{stat['total']} "
                f"(スキップ: {stat['skip']}, エラー: {stat['error']})"
            )

    except ValueError as e:
        print(f"❌ エラー: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  処理を中断しました")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
