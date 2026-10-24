"""Manual, offline environment check using a local video and cached Whisper model."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import cv2
import numpy as np
import torch
import whisper

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.frame_extractor import extract_frames
from src.transcriber import transcribe_video


def main():
    source = Path(sys.argv[1]).resolve()
    cached_model = Path.home() / ".cache/whisper/base.pt"
    assert cached_model.is_file(), "Cache the Whisper base model before this offline check"
    assert "anaconda" not in sys.base_prefix.lower(), sys.base_prefix
    assert shutil.which("ffmpeg"), "FFmpeg is missing from PATH"
    tensor = torch.from_numpy(np.arange(4, dtype=np.float32))
    assert tensor.sum().item() == 6
    with tempfile.TemporaryDirectory(prefix="video-agent-smoke-") as workdir:
        clip = Path(workdir) / "clip.mp4"
        subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-i", str(source), "-t", "12",
             "-c:v", "libx264", "-c:a", "aac", str(clip)],
            check=True,
        )
        frames = extract_frames(str(clip), str(Path(workdir) / "frames"))
        assert frames and all(cv2.imread(frame) is not None for frame in frames)
        transcript = transcribe_video(str(clip))
        assert transcript["text"] and transcript["segments"], transcript
        assert clip.with_suffix(".transcript.json").is_file()
        print(json.dumps({
            "python": sys.version.split()[0], "base_prefix": sys.base_prefix,
            "ffmpeg": shutil.which("ffmpeg"), "torch": torch.__version__,
            "numpy": np.__version__, "opencv": cv2.__version__,
            "whisper": whisper.__version__, "frames": len(frames),
            "transcript": transcript["text"], "conda_prefix": os.getenv("CONDA_PREFIX"),
        }, indent=2))


if __name__ == "__main__":
    main()
