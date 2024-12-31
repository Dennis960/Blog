import os
from PIL import Image
import subprocess

OPTIMIZED_FILES_PATH = "optimized_files.txt"


def load_optimized_files():
    if os.path.exists(OPTIMIZED_FILES_PATH):
        with open(OPTIMIZED_FILES_PATH, "r") as f:
            return set(f.read().splitlines())
    return set()


def save_optimized_file(file_path):
    with open(OPTIMIZED_FILES_PATH, "a") as f:
        f.write(file_path + "\n")


def optimize_videos(folder_path):
    max_width, max_height = 1920, 1080
    valid_extensions = ["mp4", "mov", "avi", "mkv", "flv", "wmv"]
    optimized_files = load_optimized_files()

    for root, _, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            if file.split(".")[-1].lower() in valid_extensions:
                if file_path in optimized_files:
                    continue
                try:
                    optimized_path = os.path.join(root, f"optimized_{file}")
                    command = [
                        "ffmpeg",
                        "-i", file_path,
                        "-vf", f"scale='if(gt(iw,{max_width}),{max_width},iw):if(gt(ih,{max_height}),{
                            max_height},ih)',setsar=1,pad=ceil(iw/2)*2:ceil(ih/2)*2",
                        "-c:v", "libx264",
                        "-preset", "slow",
                        "-crf", "23",
                        "-c:a", "aac",
                        "-b:a", "128k",
                        "-movflags", "+faststart",
                        optimized_path
                    ]
                    subprocess.run(command, check=True)
                    os.remove(file_path)
                    os.rename(optimized_path, file_path)
                    save_optimized_file(file_path)
                    print(f"Optimized {file_path}")
                except subprocess.CalledProcessError as e:
                    print(f"Error processing {file_path}: {e}")
                except Exception as e:
                    print(f"Unexpected error processing {file_path}: {e}")


def optimize_images(folder_path):
    max_width, max_height = 1920, 1080
    valid_extensions = ["jpeg", "jpg", "png", "webp"]
    optimized_files = load_optimized_files()

    for root, _, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            if file.split(".")[-1].lower() in valid_extensions:
                if file_path in optimized_files:
                    continue
                try:
                    with Image.open(file_path) as img:
                        original_size = img.size
                        img.thumbnail((max_width, max_height))
                        os.remove(file_path)
                        optimized_path = file_path
                        img.save(optimized_path, optimize=True, quality=85)
                        save_optimized_file(file_path)
                        print(f"Optimized {file_path}: {
                              original_size} -> {img.size}")
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")


if __name__ == "__main__":
    folder = "content"
    if os.path.isdir(folder):
        optimize_images(folder)
        print("Image optimization completed.")
        optimize_videos(folder)
        print("Video optimization completed.")
    else:
        print("Invalid folder path.")
