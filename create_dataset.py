"""Create timestamp references for fixed-length song segments.

Add original audio to original_songs/ and record its filename and verified
key in songs.csv, then run: python create_dataset.py
"""

import argparse
import csv
from pathlib import Path

import librosa
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
AUDIO_DIR = BASE_DIR / "original_songs"
SONGS_CSV = BASE_DIR / "songs.csv"
DATASET_CSV = BASE_DIR / "dataset.csv"
SUPPORTED_EXTENSIONS = {".mp3", ".wav"}

# Use spelling consistent with conventional key names. Enharmonic spellings
# such as C# and Db are not both included because there are 24 distinct keys.
KEYS = {
    f"{note}_{mode}"
    for note in ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
    for mode in ("major", "minor")
}
OUTPUT_COLUMNS = ["filename", "start", "end", "key"]


def read_song_labels(path: Path) -> pd.DataFrame:
    """Read and validate the filename/key list."""
    if not path.exists():
        raise FileNotFoundError(f"Song list not found: {path}")

    songs = pd.read_csv(path, dtype=str).fillna("")
    required_columns = {"filename", "key"}
    if not required_columns.issubset(songs.columns):
        raise ValueError("songs.csv must contain 'filename' and 'key' columns")

    songs = songs[["filename", "key"]].copy()
    songs["filename"] = songs["filename"].str.strip()
    songs["key"] = songs["key"].str.strip()

    if (songs["filename"] == "").any():
        raise ValueError("songs.csv contains an empty filename")
    if songs["filename"].duplicated().any():
        duplicates = songs.loc[songs["filename"].duplicated(), "filename"].tolist()
        raise ValueError(f"Duplicate filenames in songs.csv: {duplicates}")

    invalid_keys = sorted(set(songs.loc[~songs["key"].isin(KEYS), "key"]))
    if invalid_keys:
        raise ValueError(
            f"Unsupported keys: {', '.join(invalid_keys)}. Use keys such as C_major or A_minor."
        )
    return songs


def build_dataset(segment_seconds: float = 30.0) -> pd.DataFrame:
    """Build one timestamp row per complete segment, without writing audio."""
    if segment_seconds <= 0:
        raise ValueError("Segment duration must be greater than zero")
    if not AUDIO_DIR.is_dir():
        raise FileNotFoundError(f"Audio folder not found: {AUDIO_DIR}")

    songs = read_song_labels(SONGS_CSV)
    rows = []

    for song in songs.itertuples(index=False):
        filename, key = song.filename, song.key
        # Prevent paths in songs.csv from escaping original_songs/.
        audio_path = (AUDIO_DIR / filename).resolve()
        if audio_path.parent != AUDIO_DIR.resolve() or Path(filename).name != filename:
            print(f"Skipping unsafe filename: {filename}")
            continue
        if audio_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            print(f"Skipping unsupported audio format: {filename}")
            continue
        if not audio_path.is_file():
            print(f"Skipping missing audio file: {filename}")
            continue
        if audio_path.stat().st_size == 0:
            print(f"Skipping empty audio file: {filename}")
            continue

        try:
            duration = float(librosa.get_duration(path=str(audio_path)))
            if duration <= 0:
                print(f"Skipping audio with no usable duration: {filename}")
                continue
        except Exception as error:
            print(f"Skipping unreadable audio file {filename}: {error}")
            continue

        # floor() via integer conversion discards any final partial segment.
        segment_count = int(duration // segment_seconds)
        for index in range(segment_count):
            start = index * segment_seconds
            end = start + segment_seconds
            rows.append({"filename": filename, "start": start, "end": end, "key": key})

    return pd.DataFrame(rows, columns=OUTPUT_COLUMNS)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create timestamp rows for song segments.")
    parser.add_argument(
        "--segment-seconds", type=float, default=30.0,
        help="segment length in seconds (default: 30)",
    )
    args = parser.parse_args()

    dataset = build_dataset(args.segment_seconds)
    dataset.to_csv(DATASET_CSV, index=False)
    print(f"Wrote {len(dataset)} segment rows to {DATASET_CSV}")


if __name__ == "__main__":
    main()
