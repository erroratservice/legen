import argparse
import os
import subprocess
import time
from inspect import currentframe, getframeinfo
from pathlib import Path

import ffmpeg_utils
import file_utils
from utils import time_task, audio_extensions, video_extensions, check_other_extensions

version = "v0.18.1"

# Terminal colors
default = "\033[1;0m"
gray = "\033[1;37m"
wblue = "\033[1;36m"
blue = "\033[1;34m"
yellow = "\033[1;33m"
green = "\033[1;32m"
red = "\033[1;31m"

print(f"""
{blue}888              {gray} .d8888b.                   
{blue}888              {gray}d88P  Y88b                  
{blue}888              {gray}888    888                  
{blue}888      .d88b.  {gray}888         .d88b.  88888b. 
{blue}888     d8P  Y8b {gray}888  88888 d8P  Y8b 888 "88b
{blue}888     88888888 {gray}888    888 88888888 888  888
{blue}888     Y8b.     {gray}Y88b  d88P Y8b.     888  888
{blue}88888888 "Y8888  {gray} "Y8888P88  "Y8888  888  888

legen {version} - github.com/matheusbach/legen{default}
python {__import__('sys').version}
""")
time.sleep(1.5)

# Define parameters and configurations
parser = argparse.ArgumentParser(prog="LeGen", description="Batch video/audio encoder using ffmpeg.",
                                 argument_default=True, allow_abbrev=True, add_help=True,
                                 usage='LeGen -i INPUT_PATH [other options]')
parser.add_argument("-i", "--input_path",
                    help="Path to media files. Can be a folder containing files or an individual file", required=True, type=Path)
parser.add_argument("-c:v", "--codec_video", type=str, default="h264", metavar="VIDEO_CODEC",
                    help="Target video codec. Ex: h264, libx264, h264_vaapi, h264_nvenc, hevc, etc.")
parser.add_argument("-c:a", "--codec_audio", type=str, default="aac", metavar="AUDIO_CODEC",
                    help="Target audio codec. (default: aac). Ex: aac, libopus, mp3, vorbis")
parser.add_argument("-o", "--output_dir", default=None, type=Path,
                    help="Output folder for encoded files. (default: encoded_ + input_path)")
parser.add_argument("--overwrite", default=False, action="store_true",
                    help="Overwrite existing files in output directory")
parser.add_argument("--copy_files", default=False, action="store_true",
                    help="Copy other (non-video/audio) files present in input directory to output directory")
args = parser.parse_args()

if not args.output_dir and not args.input_path.is_file():
    args.output_dir = Path(args.input_path.parent, "encoded_" + args.input_path.name)
elif not args.output_dir and args.input_path.is_file():
    args.output_dir = args.input_path.parent

with time_task(message="⌛ Processing files for"):
    path: Path
    for path in (item for item in sorted(sorted(Path(args.input_path).rglob('*'), key=lambda x: x.stat().st_mtime), key=lambda x: len(x.parts)) if item.is_file()):
        rel_path = path.relative_to(args.input_path)
        with time_task(message_start=f"\nProcessing {yellow}{rel_path.as_posix()}{default}", end="\n", message="⌚ Done in"):
            try:
                if path.suffix.lower() in video_extensions or path.suffix.lower() in audio_extensions:
                    file_type = "video" if path.suffix.lower() in video_extensions else "audio"
                    origin_media_path = path
                    dupe_filename = len(check_other_extensions(path, list(video_extensions | audio_extensions))) > 1
                    posfix_extension = path.suffix.lower().replace('.', '_') if dupe_filename else ''

                    output_dir = Path(args.output_dir, rel_path.parent)
                    output_dir.mkdir(parents=True, exist_ok=True)
                    # output extension will be .mp4 for video, .m4a for audio (.mp3 optional)
                    if file_type == "video":
                        output_path = Path(output_dir, rel_path.stem + posfix_extension + ".mp4")
                    else:
                        output_path = Path(output_dir, rel_path.stem + posfix_extension + ".m4a")

                    if output_path.exists() and not args.overwrite:
                        print(f"Existing file {gray}{output_path}{default}. Skipping encoding.")
                    else:
                        print(f"{wblue}Encoding{default} with {gray}FFmpeg{default}")
                        ffmpeg_utils.encode_media(
                            input_media_path=origin_media_path,
                            output_media_path=output_path,
                            codec_video=args.codec_video if file_type == "video" else None,
                            codec_audio=args.codec_audio
                        )
                else:
                    print("Not a video or audio file")
                    if args.copy_files:
                        output_file_path = Path(args.output_dir, rel_path)
                        output_file_path.parent.mkdir(parents=True, exist_ok=True)
                        file_utils.copy_file_if_different(path, output_file_path)
            except Exception as e:
                file = path.as_posix()
                print(f"{red}ERROR !!!{default} {file}")
                print(f"{yellow}check legen-errors.txt for details{default}")
                current_time = time.strftime("%y/%m/%d %H:%M:%S", time.localtime())
                error_message = f"[{current_time}] {file}: {type(e).__name__}: {str(e)}"
                with open(Path(Path(getframeinfo(currentframe()).filename).resolve().parent, "legen-errors.txt"), "a") as f:
                    f.write(error_message + "\n")
                    f.close()

    print(f"{green}Tasks done!{default}")
