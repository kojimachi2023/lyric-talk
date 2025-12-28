"""
歌詞コーパス収集パイプライン

Spotify APIを使用して日本のヒット曲を検索し、
LyricsGeniusを使用して歌詞を取得・保存します。
"""

import json
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import lyricsgenius
import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyClientCredentials

# .envファイルを読み込み
ENV_PATH = Path(__file__).parent / ".env"
load_dotenv(ENV_PATH)


@dataclass
class TrackInfo:
    """曲情報を保持するデータクラス"""

    artist: str
    title: str
    album: str
    release_date: str
    spotify_id: str
    year: int


class SpotifyJapanHitsFetcher:
    """Spotify APIを使用して日本のヒット曲を取得するクラス"""

    # 日本の人気プレイリストID (Spotify公式の日本TOP50など)
    JAPAN_TOP_PLAYLISTS = {
        "japan_top_50": "37i9dQZEVXbKXQ4mDTEBXq",  # Top 50 - Japan
    }

    def __init__(self):
        client_id = os.getenv("EVAL_SPOTIFY_CLIENT_ID")
        client_secret = os.getenv("EVAL_SPOTIFY_CLIENT_SECRET")
        self.market = os.getenv("EVAL_SPOTIFY_MARKET", "JP")

        if not client_id or not client_secret:
            raise ValueError(
                "Spotify credentials not found. "
                "Please set EVAL_SPOTIFY_CLIENT_ID and EVAL_SPOTIFY_CLIENT_SECRET in .env"
            )

        auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
        self.sp = spotipy.Spotify(auth_manager=auth_manager)

    def search_japanese_hits_by_year(self, year: int, limit: int = 50) -> list[TrackInfo]:
        """
        指定年の日本語ヒット曲を検索

        Args:
            year: 検索対象の年
            limit: 取得する曲数の上限

        Returns:
            TrackInfo のリスト
        """
        tracks: list[TrackInfo] = []
        seen_tracks: set[str] = set()  # 重複排除用

        # 検索クエリ: 日本語の曲を年で絞り込み
        queries = [
            f"year:{year} tag:jpop",
            f"year:{year} tag:j-pop",
            f"year:{year} genre:j-pop",
            f"year:{year} genre:japanese",
        ]

        for query in queries:
            if len(tracks) >= limit:
                break

            try:
                results = self.sp.search(
                    q=query,
                    type="track",
                    market=self.market,
                    limit=min(50, limit - len(tracks)),
                )

                for item in results["tracks"]["items"]:
                    track_key = f"{item['artists'][0]['name']}:{item['name']}"

                    if track_key in seen_tracks:
                        continue

                    seen_tracks.add(track_key)

                    # リリース日から年を抽出
                    release_date = item["album"]["release_date"]
                    release_year = int(release_date[:4]) if release_date else year

                    track_info = TrackInfo(
                        artist=item["artists"][0]["name"],
                        title=item["name"],
                        album=item["album"]["name"],
                        release_date=release_date,
                        spotify_id=item["id"],
                        year=release_year,
                    )
                    tracks.append(track_info)

                    if len(tracks) >= limit:
                        break

                # API レート制限対策
                time.sleep(0.1)

            except Exception as e:
                print(f"Error searching for {query}: {e}")
                continue

        return tracks

    def get_playlist_tracks(self, playlist_id: str) -> list[TrackInfo]:
        """
        プレイリストから曲情報を取得

        Args:
            playlist_id: SpotifyプレイリストID

        Returns:
            TrackInfo のリスト
        """
        tracks: list[TrackInfo] = []

        try:
            results = self.sp.playlist_tracks(playlist_id, market=self.market)

            for item in results["items"]:
                if item["track"] is None:
                    continue

                track = item["track"]
                release_date = track["album"]["release_date"]
                release_year = int(release_date[:4]) if release_date else 0

                track_info = TrackInfo(
                    artist=track["artists"][0]["name"],
                    title=track["name"],
                    album=track["album"]["name"],
                    release_date=release_date,
                    spotify_id=track["id"],
                    year=release_year,
                )
                tracks.append(track_info)

        except Exception as e:
            print(f"Error fetching playlist {playlist_id}: {e}")

        return tracks

    def fetch_hits_last_n_years(
        self, n_years: int = 5, tracks_per_year: int = 20
    ) -> dict[int, list[TrackInfo]]:
        """
        過去N年間の各年のヒット曲を取得
        Spotifyの公式TOP50プレイリストを使用します

        Args:
            n_years: 取得する年数 (注: プレイリストは現在のTOP曲を返すため、年数パラメータは参考値)
            tracks_per_year: 各年の取得曲数

        Returns:
            年をキー、TrackInfoリストを値とする辞書
        """
        hits_by_year: dict[int, list[TrackInfo]] = {}

        # Spotify公式のJapan TOP 50プレイリストから現在のヒット曲を取得
        playlist_id = self.JAPAN_TOP_PLAYLISTS["japan_top_50"]
        print("Fetching from Spotify Japan TOP 50 playlist...")
        tracks = self.get_playlist_tracks(playlist_id)

        if tracks:
            # プレイリストから得た曲を年ごとにグループ化
            current_year = datetime.now().year
            for year in range(current_year - n_years + 1, current_year + 1):
                year_tracks = [t for t in tracks if t.year == year]
                hits_by_year[year] = year_tracks[:tracks_per_year]
                if year_tracks:
                    print(f"  {year}: Found {len(year_tracks)} tracks")

        # 結果が不足している場合は、補足データとして検索を使用
        current_year = datetime.now().year
        for year in range(current_year - n_years + 1, current_year + 1):
            if year not in hits_by_year or len(hits_by_year[year]) < tracks_per_year:
                needed = tracks_per_year - len(hits_by_year.get(year, []))
                supplement_tracks = self.search_japanese_hits_by_year(year, limit=needed)
                if year not in hits_by_year:
                    hits_by_year[year] = supplement_tracks
                else:
                    hits_by_year[year].extend(supplement_tracks)
                if supplement_tracks:
                    msg = f"  {year}: Supplemented with {len(supplement_tracks)} tracks from search"
                    print(msg)
            time.sleep(0.5)  # API レート制限対策

        return hits_by_year


class LyricsCollector:
    """LyricsGeniusを使用して歌詞を収集するクラス"""

    def __init__(self, output_dir: Path | None = None):
        access_token = os.getenv("EVAL_GENIUS_ACCESS_TOKEN")

        if not access_token:
            raise ValueError(
                "Genius access token not found. Please set EVAL_GENIUS_ACCESS_TOKEN in .env"
            )

        self.genius = lyricsgenius.Genius(access_token)
        # 設定: 不要な情報をスキップ
        self.genius.verbose = False
        self.genius.remove_section_headers = True
        self.genius.skip_non_songs = True
        self.genius.timeout = 15

        # 出力ディレクトリ
        self.output_dir = output_dir or Path(__file__).parent / "lyrics"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _sanitize_filename(self, name: str) -> str:
        """ファイル名に使用できない文字を除去"""
        # 使用できない文字を除去/置換
        sanitized = re.sub(r'[<>:"/\\|?*]', "_", name)
        # 空白を整理
        sanitized = re.sub(r"\s+", " ", sanitized).strip()
        # 長さ制限
        return sanitized[:100]

    def fetch_lyrics(self, track: TrackInfo) -> str | None:
        """
        曲の歌詞を取得

        Args:
            track: 曲情報

        Returns:
            歌詞テキスト、取得失敗時はNone
        """
        try:
            song = self.genius.search_song(track.title, track.artist)

            if song and song.lyrics:
                return song.lyrics

        except Exception as e:
            print(f"  Error fetching lyrics for {track.artist} - {track.title}: {e}")

        return None

    def save_lyrics(self, track: TrackInfo, lyrics: str) -> Path:
        """
        歌詞をファイルに保存

        Args:
            track: 曲情報
            lyrics: 歌詞テキスト

        Returns:
            保存先のパス
        """
        # 年ごとのサブディレクトリを作成
        year_dir = self.output_dir / str(track.year)
        year_dir.mkdir(parents=True, exist_ok=True)

        # ファイル名: アーティスト名_曲名.txt
        artist_name = self._sanitize_filename(track.artist)
        title_name = self._sanitize_filename(track.title)
        filename = f"{artist_name}_{title_name}.json"
        filepath = year_dir / filename

        payload = {
            "artist": track.artist,
            "title": track.title,
            "album": track.album,
            "release_date": track.release_date,
            "spotify_id": track.spotify_id,
            "lyrics": lyrics,
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        return filepath

    def collect_lyrics_for_tracks(
        self, tracks: list[TrackInfo], delay: float = 1.0
    ) -> dict[str, Path]:
        """
        複数の曲の歌詞を収集・保存

        Args:
            tracks: 曲情報のリスト
            delay: API呼び出し間の待機時間（秒）

        Returns:
            Spotify ID をキー、保存先パスを値とする辞書
        """
        saved_files: dict[str, Path] = {}

        for i, track in enumerate(tracks, 1):
            print(f"  [{i}/{len(tracks)}] {track.artist} - {track.title}...")

            lyrics = self.fetch_lyrics(track)

            if lyrics:
                filepath = self.save_lyrics(track, lyrics)
                saved_files[track.spotify_id] = filepath
                print(f"    ✓ Saved to {filepath.name}")
            else:
                print("    ✗ Lyrics not found")

            # API レート制限対策
            time.sleep(delay)

        return saved_files


def main():
    """メイン処理"""
    print("=" * 60)
    print("歌詞コーパス収集パイプライン")
    print("=" * 60)

    # 設定
    N_YEARS = 3  # 過去何年分を取得するか
    TRACKS_PER_YEAR = 20  # 各年の取得曲数

    # 1. Spotify から日本のヒット曲を取得
    print("\n[Step 1] Fetching Japanese hits from Spotify...")
    spotify_fetcher = SpotifyJapanHitsFetcher()
    hits_by_year = spotify_fetcher.fetch_hits_last_n_years(
        n_years=N_YEARS, tracks_per_year=TRACKS_PER_YEAR
    )

    # 結果サマリーを表示
    total_tracks = sum(len(tracks) for tracks in hits_by_year.values())
    print(f"\nTotal tracks found: {total_tracks}")
    for year, tracks in sorted(hits_by_year.items()):
        print(f"  {year}: {len(tracks)} tracks")

    # 2. LyricsGenius で歌詞を取得・保存
    print("\n[Step 2] Collecting lyrics from Genius...")
    lyrics_collector = LyricsCollector()

    all_saved_files: dict[str, Path] = {}
    for year, tracks in sorted(hits_by_year.items()):
        print(f"\n--- {year} ---")
        saved = lyrics_collector.collect_lyrics_for_tracks(tracks, delay=1.5)
        all_saved_files.update(saved)

    # 最終結果
    print("\n" + "=" * 60)
    print("収集完了!")
    print("=" * 60)
    print(f"Total tracks processed: {total_tracks}")
    print(f"Lyrics successfully saved: {len(all_saved_files)}")
    print(f"Output directory: {lyrics_collector.output_dir}")

    # 年ごとの統計
    print("\nBy year:")
    for year in sorted(hits_by_year.keys()):
        year_tracks = hits_by_year[year]
        year_saved = sum(1 for t in year_tracks if t.spotify_id in all_saved_files)
        print(f"  {year}: {year_saved}/{len(year_tracks)} lyrics saved")


if __name__ == "__main__":
    main()
