# Python environment migration — 2026-10-19

The project now uses Homebrew Python 3.11.15 through `.venv/bin/python`.
Its base interpreter is under `/opt/homebrew/opt/python@3.11`, independent of
Anaconda. Runtime dependency versions were preserved from the original inventory
in `requirements-macos-py311.lock.txt`; pytest was added separately.

## Verification

Checks passed both before and after retiring the Anaconda installation:

- All 72 project tests passed (API calls are mocked in these tests).
- `python -m pip check` reported no broken requirements.
- A 12-second clip of the existing `Me at the zoo.mp4` was processed locally.
  Homebrew FFmpeg encoded the clip, OpenCV extracted six readable JPEG frames,
  and the cached Whisper base model produced a nonempty English transcript and
  timestamped segments. Temporary outputs were cleaned automatically; original
  video and transcript files were preserved.
- NumPy 2.4.6 and PyTorch 2.12.1 passed a NumPy-to-tensor computation.
- OpenCV 4.13.0 and Whisper 20250625 imported and ran successfully.
- A fresh Zsh login shell selected the new project Python after activation,
  resolved FFmpeg from Homebrew, had no `CONDA_PREFIX`, and could not find Conda.

No hosted inference calls or YouTube downloads were made during verification.
This verifies the local media pipeline and mocked application behavior, rather
than current external API access or YouTube availability.

## Anaconda retirement and rollback

Anaconda's installation contents, including its `video-agent` Conda environment,
were moved out of `/opt/anaconda3`. Conda initialization was removed from `.zshrc`
and `.bash_profile`. The Navigator shortcut and Conda user configuration were
also archived. An empty `/opt/anaconda3` directory remains because deleting
that directory requires permission to modify root-owned `/opt`.

Everything retained for rollback is in the ignored project directory:

```text
data/environment-migration-2026-10-19/
  anaconda-installation/       Full former Anaconda installation
  venv-anaconda/               Original project environment
  original-packages.txt        Original package inventory
  original-conda/              Former ~/.conda state
  original-condarc             Former ~/.condarc configuration
  zshrc.before                 Original Zsh configuration
  bash_profile.before         Original Bash configuration
  bash_profile.root-original  Original root-owned Bash profile
  Anaconda-Navigator.app       Former Applications shortcut
```

These backups still occupy disk space (the Anaconda installation was about
6.1 GB and the old project environment about 923 MB). They were not permanently
deleted. Do not run archived Anaconda binaries in place: their original absolute
paths are embedded throughout the installation.

For rollback, first restore the archived installation contents to
`/opt/anaconda3`, preserving symlinks. Preserve the current `.venv` elsewhere,
then return `venv-anaconda` to the project's `.venv` path. Restore the saved shell
profiles and Conda user configuration as needed, and start a new terminal.
The old project environment's scripts require its original `.venv` location.

For normal use, restart existing terminals (they may retain old Conda variables),
then run `source .venv/bin/activate` from the project directory.


## Permanent removal — 2026-10-19

Independent re-verification passed: all 72 tests, pip dependency check, six decoded frames, local Whisper transcription, NumPy/PyTorch computation, and fresh login shell activation with Homebrew Python 3.11.15. No hosted API calls were made. The entire `data/environment-migration-2026-10-19/` rollback archive has now been permanently deleted, including the Anaconda installation and old virtual environment. The rollback instructions above are historical and no longer available. Working `.venv`, source code, input media, and current shell profiles were preserved. `/opt/anaconda3` status: empty directory remains; root permission required.
