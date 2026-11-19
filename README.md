# dataset-for-music-app — Musical Key Detection Dataset

## Set up the environment (Windows PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python create_dataset.py
```

If PowerShell blocks activation, call the environment's Python directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe create_dataset.py
```

On macOS/Linux, replace the activation command with `source .venv/bin/activate`.

## Add songs

Keep source MP3/WAV recordings in `original_songs/`. Add one row per recording to `songs.csv` with columns `filename,key`, using a verified key (for example `C_major`, `F#_major`, or `A_minor`). The pipeline accepts all 12 sharp-spelled pitch classes in both major and minor. See `KEY_SOURCES.md` for the source references used for the songs currently listed.

`key_estimates.csv` contains raw one-time Librosa STFT/chroma key estimates and scores for the usable recordings originally in `Music/`. These are an aid for checking labels, not guaranteed key detections. The `songs.csv` keys are the selected reference labels, cross-checked against published key references in `KEY_SOURCES.md`; differences from Librosa's estimates remain visible in `key_estimates.csv`.

Run `python create_dataset.py` to replace `dataset.csv`. It uses Librosa to read each original recording's duration and writes exactly `filename,start,end,key`. Segments default to 30 seconds; configure another length with `python create_dataset.py --segment-seconds 20`. Any final partial segment is dropped. Original recordings are not modified or split. Missing, unsupported, or unreadable audio files are reported and skipped.

For model evaluation, keep all rows for a given filename together in the same train/test split.