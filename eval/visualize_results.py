"""Visualize the ITA corpus analysis results."""

import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np


def setup_japanese_font() -> None:
    """Setup Japanese font for matplotlib."""
    # Use Noto Sans CJK JP which is already available
    plt.rcParams["font.sans-serif"] = ["Noto Sans CJK JP", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False


def load_analysis_results(json_path: Path) -> list[dict[str, Any]]:
    """Load analysis results from JSON file.

    Args:
        json_path: Path to the JSON file

    Returns:
        List of song analysis results
    """
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def calculate_average_similarity(song_data: dict[str, Any]) -> float:
    """Calculate average similarity for a song.

    Args:
        song_data: Song analysis data containing distances

    Returns:
        Average similarity value
    """
    distances = song_data["distances"]
    if not distances:
        return 0.0

    similarities = [d["similarity"] for d in distances]
    return np.mean(similarities)


def get_top_songs(analysis_results: list[dict[str, Any]], top_n: int = 5) -> list[dict[str, Any]]:
    """Get top N songs with highest average similarity.

    Args:
        analysis_results: List of song analysis results
        top_n: Number of top songs to return

    Returns:
        List of top songs with their average similarity
    """
    songs_with_avg = []
    for song in analysis_results:
        avg_similarity = calculate_average_similarity(song)
        songs_with_avg.append(
            {
                "title": song["title"],
                "artist": song["artist"],
                "lyrics_corpus_id": song["lyrics_corpus_id"],
                "avg_similarity": avg_similarity,
                "distances": song["distances"],
            }
        )

    # Sort by average similarity in descending order
    songs_with_avg.sort(key=lambda x: x["avg_similarity"], reverse=True)

    return songs_with_avg[:top_n]


def plot_similarity_histograms(top_songs: list[dict[str, Any]], output_path: Path) -> None:
    """Plot histograms of similarity distribution for top songs.

    Args:
        top_songs: List of top songs with their data
        output_path: Path to save the plot
    """
    # Setup Japanese font
    setup_japanese_font()

    n_songs = len(top_songs)
    fig, axes = plt.subplots(n_songs, 1, figsize=(10, 4 * n_songs))

    # Handle single subplot case
    if n_songs == 1:
        axes = [axes]

    for idx, song in enumerate(top_songs):
        similarities = [d["similarity"] for d in song["distances"]]

        axes[idx].hist(similarities, bins=20, edgecolor="black", alpha=0.7)
        axes[idx].set_title(
            f"{song['title']} - {song['artist']}\n平均類似度: {song['avg_similarity']:.4f}",
            fontsize=12,
        )
        axes[idx].set_xlabel("類似度 (Similarity)")
        axes[idx].set_ylabel("度数 (Frequency)")
        axes[idx].set_xlim(0, 1)
        axes[idx].grid(axis="y", alpha=0.3)

        # Add statistics
        mean_sim = np.mean(similarities)
        median_sim = np.median(similarities)
        axes[idx].axvline(
            mean_sim, color="red", linestyle="--", linewidth=2, label=f"平均: {mean_sim:.4f}"
        )
        axes[idx].axvline(
            median_sim,
            color="green",
            linestyle="--",
            linewidth=2,
            label=f"中央値: {median_sim:.4f}",
        )
        axes[idx].legend()

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"ヒストグラムを保存しました: {output_path}")


def main() -> None:
    """Main function to visualize analysis results."""
    # Paths
    base_dir = Path(__file__).parent
    results_dir = base_dir / "results"
    json_path = results_dir / "ita_corpus_analysis.json"
    output_path = results_dir / "top5_similarity_histograms.png"

    # Load results
    print("分析結果を読み込んでいます...")
    analysis_results = load_analysis_results(json_path)
    print(f"総曲数: {len(analysis_results)}")

    # Get top 5 songs
    print("\n平均類似度の高い曲トップ5を計算しています...")
    top_songs = get_top_songs(analysis_results, top_n=10)

    # Print top songs
    print("\n【平均類似度トップ5】")
    for idx, song in enumerate(top_songs, 1):
        print(f"{idx}. {song['title']} - {song['artist']}: {song['avg_similarity']:.4f}")

    # Create histograms
    print("\nヒストグラムを作成しています...")
    plot_similarity_histograms(top_songs, output_path)

    print("\n完了しました!")


if __name__ == "__main__":
    main()
