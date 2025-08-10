import argparse
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from inspect import currentframe, getframeinfo
from pathlib import Path

import ffmpeg_utils
import file_utils
from utils import time_task, audio_extensions, video_extensions, check_other_extensions

version = "v0.18.1"

# ... (ASCII art and prints, unchanged) ...

parser = argparse.ArgumentParser(prog="LeGen", description="Batch video/audio encoder using ffmpeg.",
                                 argument_default=True, allow_abbrev=True, add_help=True)
parser.add_argument("-i", "--input_path", required=True, type=Path)
parser.add_argument("-o", "--output_dir", default=None, type=Path)
parser.add_argument("--overwrite", default=False, action="store_true")
parser.add_argument("--copy_files", default=False, action="store_true")
parser.add_argument("--max_workers", default=2, type=int, help="Max parallel encodes (T4 can do 2-3 efficiently)")
args = parser.parse_args()

if not args.output_dir and not args.input_path.is_file():
    args.output_dir = Path(args.input_path.parent, "encoded_" + args.input_path.name)
elif not args.output_dir and args.input_path.is_file():
    args.output_dir = args.input_path.parent

def encode_one(path, rel_path, output_dir, overwrite):
    try:
        file_type = "video" if path.suffix.lower() in video_extensions else "audio"
        origin_media_path = path
        dupe_filename = len(check_other_extensions(path, list(video_extensions | audio_extensions))) > 1
        posfix_extension = path.suffix.lower().replace('.', '_') if dupe_filename else ''
        output_dir = Path(output_dir, rel_path.parent)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = Path(output_dir, rel_path.stem + posfix_extension + (".mp4" if file_type == "video" else ".m4a"))
        if output_path.exists() and not overwrite:
            print(f"Existing file {output_path}. Skipping encoding.")
            return
        ffmpeg_utils.encode_media(origin_media_path, output_path)
    except Exception as e:
        file = path.as_posix()
        print(f"ERROR !!! {file}")
        current_time = time.strftime("%y/%m/%d %H:%M:%S", time.localtime())
        error_message = f"[{current_time}] {file}: {type(e).__name__}: {str(e)}"
        with open(Path(Path(getframeinfo(currentframe()).filename).resolve().parent, "legen-errors.txt"), "a") as f:
            f.write(error_message + "\n")

with time_task(message="⌛ Processing files for"):
    # Collect tasks
    tasks = []
    for path in (item for item in sorted(sorted(Path(args.input_path).rglob('*'), key=lambda x: x.stat().st_mtime), key=lambda x: len(x.parts)) if item.is_file()):
        rel_path = path.relative_to(args.input_path)
        if path.suffix.lower() in video_extensions or path.suffix.lower() in audio_extensions:
            tasks.append((path, rel_path, args.output_dir, args.overwrite))
        elif args.copy_files:
            output_file_path = Path(args.output_dir, rel_path)
            output_file_path.parent.mkdir(parents=True, exist_ok=True)
            file_utils.copy_file_if_different(path, output_file_path)

    # Parallel encode
    with ProcessPoolExecutor(max_workers=args.max_workers) as executor:
        futures = [executor.submit(encode_one, *task) for task in tasks]
        for f in as_completed(futures):
            pass

    print("Tasks done!")
