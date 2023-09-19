import os, re, datetime, time, argparse
import imageio as io
from pathlib import Path

def create_folders() -> None:
    Path("./outputs/gifs").mkdir(parents=True, exist_ok=True)

def load_images(dir: str, start_time: int, end_time: int) -> list:
    images = []
    for file_name in sorted(os.listdir(dir)):
        time = int(re.search("\d+", file_name).group(0))
        if time > start_time and time < end_time:
            path = os.path.join(dir, file_name)
            images.append(io.v2.imread(path))

    return images

def generate_gif(images: list, start_time: int, end_time: int, duration: int) -> None:
    io.v2.mimwrite('./outputs/gifs/output.gif', images, duration=duration)

if __name__ == "__main__":
    utc_now = datetime.datetime.utcnow()
    week_ago = utc_now - datetime.timedelta(days=7)
    unix_now, unix_week_ago = int(time.mktime(utc_now.timetuple())), int(time.mktime(week_ago.timetuple()))

    parser = argparse.ArgumentParser()
    parser.add_argument("--begin", help="Beginning of the time interval for images generated", type=int, default=unix_week_ago)
    parser.add_argument("--end", help="End of the time interval for images generated", type=int, default=unix_now)
    parser.add_argument("--fps", help="Frames per second for a gif", type=int, default=10)
    args = parser.parse_args()
    from_time, to_time = args.begin, args.end
    duration = 1000 * (1/args.fps)

    create_folders()

    print("Loading images...")
    images = load_images("./outputs/images", from_time, to_time)
    print("Images loaded, creating the gif...")
    generate_gif(images, from_time, to_time, duration)

        