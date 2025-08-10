import subprocess
from pathlib import Path
from ffmpeg_progress_yield import FfmpegProgress
from tqdm import tqdm

def encode_media(input_media_path: Path, output_media_path: Path):
    cmd = [
    "ffmpeg", "-y", "-i", str(input_media_path),
    "-c:v", "hevc_nvenc",
    "-preset", "p7",
    "-rc", "vbr",
    "-b:v", "3000k",  # or your desired bitrate
    "-maxrate", "4000k",
    "-profile:v", "main10",
    "-pix_fmt", "p010le",
    "-c:a", "aac",
    "-b:a", "128k",
    "-movflags", "+faststart",
    str(output_media_path)
]
    print("Running:", " ".join(cmd))
    try:
        ff = FfmpegProgress(cmd)
        with tqdm(total=100, position=0, ascii="░▒█", desc="Encoding", unit="%", unit_scale=True, leave=True, bar_format="{desc} [{bar}] {percentage:3.0f}% | ETA: {remaining} | ⏱: {elapsed}") as pbar:
            for progress in ff.run_command_with_progress():
                pbar.update(progress - pbar.n)
    except Exception as e:
        print("Progress bar unavailable, running ffmpeg directly.")
        subprocess.run(cmd, check=True)
