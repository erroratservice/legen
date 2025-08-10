import subprocess
from pathlib import Path

from ffmpeg_progress_yield import FfmpegProgress
from tqdm import tqdm

def encode_media(input_media_path: Path, output_media_path: Path, codec_video=None, codec_audio=None, video_hardware_api="auto"):
    cmd = ["ffmpeg", "-y", "-i", str(input_media_path)]

    # Video codec (with hardware API if required)
    if codec_video:
        if video_hardware_api and video_hardware_api != "auto" and video_hardware_api != "none":
            # Example: h264_nvenc, h264_vaapi, etc.
            codec = f"{codec_video}_{video_hardware_api}"
        else:
            codec = codec_video
        cmd += ["-c:v", codec]
    else:
        cmd += ["-vn"]  # No video stream

    # Audio codec
    if codec_audio:
        cmd += ["-c:a", codec_audio]
    else:
        cmd += ["-an"]  # No audio stream

    # Container/format: Use .mp4 for video, .m4a for audio
    # Always set pixel format for mp4
    if (output_media_path.suffix.lower() == ".mp4") and codec_video:
        cmd += ["-pix_fmt", "yuv420p", "-movflags", "+faststart"]

    cmd += [str(output_media_path)]
    print("Running:", " ".join(cmd))

    # Progress bar if possible
    try:
        ff = FfmpegProgress(cmd)
        with tqdm(total=100, position=0, ascii="░▒█", desc="Encoding", unit="%", unit_scale=True, leave=True, bar_format="{desc} [{bar}] {percentage:3.0f}% | ETA: {remaining} | ⏱: {elapsed}") as pbar:
            for progress in ff.run_command_with_progress():
                pbar.update(progress - pbar.n)
    except Exception as e:
        # fallback to normal subprocess if ffmpeg_progress_yield fails
        print("Progress bar unavailable, running ffmpeg directly.")
        subprocess.run(cmd, check=True)
