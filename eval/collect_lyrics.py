"""
歌詞コーパス収集パイプライン

Billboard Japan のチャート情報をスクレイピングして日本のヒット曲を取得し、
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
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# .envファイルを読み込み
ENV_PATH = Path(__file__).parent / ".env"
load_dotenv(ENV_PATH)


@dataclass
class TrackInfo:
    """曲情報を保持するデータクラス"""

    artist: str
    title: str
    album: str | None
    release_date: str | None
    spotify_id: str | None
    year: int


class BillboardJapanFetcher:
    """Billboard Japan のチャートからヒット曲を取得するクラス"""

    BASE_URL = "https://www.billboard-japan.com/charts/detail"
    HOT_100_YEAR_TYPE = "hot100_year"

    def __init__(self):
        """Billboard Japan フェッチャーを初期化"""
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        )

    def fetch_year_chart(self, year: int) -> list[TrackInfo]:
        """
        指定年の年間チャートを取得

        Args:
            year: 取得対象の年

        Returns:
            TrackInfo のリスト
        """
        tracks: list[TrackInfo] = []
        seen_tracks: set[str] = set()  # 重複排除用

        try:
            # URLを構築
            url = f"{self.BASE_URL}?a={self.HOT_100_YEAR_TYPE}&year={year}"
            print(f"Fetching from: {url}")

            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            # HTMLをパース
            soup = BeautifulSoup(response.content, "html.parser")

            # チャート表から行を抽出
            table = soup.find("table")
            if not table:
                print(f"Warning: No table found on chart for year {year}")
                return tracks

            rows = table.find_all("tr")
            for row in rows:
                cells = row.find_all("td")
                if len(cells) < 2:
                    continue

                # 最初のセルはランキング番号
                rank_cell = cells[0].get_text(strip=True)
                if not rank_cell.isdigit():
                    continue

                rank = int(rank_cell)

                # 2番目のセルが曲情報
                info_cell = cells[1]

                # div.name_detail を探す（本来の構造）
                name_detail = info_cell.find("div", class_="name_detail")

                if name_detail:
                    # 新しいHTMLレイアウト（p タグで構造化）
                    title_p = name_detail.find("p", class_="musuc_title")
                    artist_p = name_detail.find("p", class_="artist_name")

                    if title_p and artist_p:
                        title = title_p.get_text(strip=True)
                        artist = artist_p.get_text(strip=True)
                    else:
                        continue
                else:
                    # フォールバック：古いHTMLレイアウトまたは異なる構造
                    # テキストから解析
                    full_text = info_cell.get_text(strip=True)
                    a_tags = info_cell.find_all("a")

                    if len(a_tags) >= 2:
                        artist = a_tags[-1].get_text(strip=True)
                        # 曲名 = 全テキスト - ランク番号 - アーティスト名 - 「詳細・購入はこちら」
                        title = (
                            full_text.replace(rank_cell, "")
                            .replace(artist, "")
                            .replace("詳細・購入はこちら", "")
                            .strip()
                        )
                    else:
                        continue

                if not title or not artist:
                    continue

                # 重複チェック
                track_key = f"{artist}:{title}"
                if track_key in seen_tracks:
                    continue
                seen_tracks.add(track_key)

                # TrackInfo を作成
                track_info = TrackInfo(
                    artist=artist,
                    title=title,
                    album=None,
                    release_date=None,
                    spotify_id=None,
                    year=year,
                )
                tracks.append(track_info)

            print(f"Found {len(tracks)} unique tracks for year {year}")
            time.sleep(1)  # サーバー負荷対策

        except Exception as e:
            print(f"Error fetching chart for year {year}: {e}")
            import traceback

            traceback.print_exc()

        return tracks

    def fetch_hits_last_n_years(
        self, n_years: int = 5, tracks_per_year: int = 20
    ) -> dict[int, list[TrackInfo]]:
        """
        過去N年間の各年のヒット曲を取得

        Args:
            n_years: 取得する年数
            tracks_per_year: 各年の取得曲数（制限）

        Returns:
            年をキー、TrackInfoリストを値とする辞書
        """
        hits_by_year: dict[int, list[TrackInfo]] = {}

        current_year = datetime.now().year
        for year in range(current_year - n_years + 1, current_year + 1):
            print(f"Fetching year {year}...")
            tracks = self.fetch_year_chart(year)

            # 指定数に制限
            if tracks:
                hits_by_year[year] = tracks[:tracks_per_year]
            else:
                hits_by_year[year] = []

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
            "lyrics": lyrics,
        }

        # オプショナルなフィールドをペイロードに追加
        if track.album:
            payload["album"] = track.album
        if track.release_date:
            payload["release_date"] = track.release_date
        if track.spotify_id:
            payload["spotify_id"] = track.spotify_id

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
            曲情報キー (artist_title) を値、保存先パスを値とする辞書
        """
        saved_files: dict[str, Path] = {}

        for i, track in enumerate(tracks, 1):
            print(f"  [{i}/{len(tracks)}] {track.artist} - {track.title}...")

            lyrics = self.fetch_lyrics(track)

            if lyrics:
                filepath = self.save_lyrics(track, lyrics)
                # Spotify IDではなく、artist_titleをキーにする
                track_key = f"{track.artist}_{track.title}"
                saved_files[track_key] = filepath
                print(f"    ✓ Saved to {filepath.name}")
            else:
                print("    ✗ Lyrics not found")

            # API レート制限対策
            time.sleep(delay)

        return saved_files


def main():
    """メイン処理"""
    print("=" * 60)
    print("歌詞コーパス収集パイプライン (Billboard Japan版)")
    print("=" * 60)

    # 設定
    N_YEARS = 3  # 過去何年分を取得するか
    TRACKS_PER_YEAR = 20  # 各年の取得曲数

    # 1. Billboard Japan から日本のヒット曲を取得
    print("\n[Step 1] Fetching Japanese hits from Billboard Japan...")
    billboard_fetcher = BillboardJapanFetcher()
    hits_by_year = billboard_fetcher.fetch_hits_last_n_years(
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
        # 曲情報をキーとしてカウント（Spotify IDがないため）
        year_saved = sum(
            1 for t in year_tracks if f"{t.artist}_{t.title}" in str(list(all_saved_files.values()))
        )
        print(f"  {year}: {year_saved}/{len(year_tracks)} lyrics saved")


if __name__ == "__main__":
    main()
