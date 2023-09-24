import os, re, datetime, time, argparse
import imageio as io
from pathlib import Path

from goya import draw_the_book

# Monet knows how to turn a series of images into a GIF

def create_folders() -> None:
    Path("./outputs/gifs").mkdir(parents=True, exist_ok=True)

def load_csvs(path: str) -> list:
    pass

def generate_images(csvs: list, start_time: int, end_time: int) -> None:
    pass

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

# In some situations we don't want to load all images into RAM at once
def memory_optimised_gif(dir: str, start_time: int, end_time: int, duration: int) -> None:
    with io.v2.get_writer('./outputs/gifs/output.gif', mode='I', duration=duration) as writer:
        for file_name in sorted(os.listdir(dir)):
            time = int(re.search("\d+", file_name).group(0))
            if time > start_time and time < end_time:
                path = os.path.join(dir, file_name)
                image = io.v2.imread(path)
                writer.append_data(image)
    writer.close()

if __name__ == "__main__":
    utc_now = datetime.datetime.utcnow()
    week_ago = utc_now - datetime.timedelta(days=7)
    unix_now, unix_week_ago = int(time.mktime(utc_now.timetuple())), int(time.mktime(week_ago.timetuple()))

    parser = argparse.ArgumentParser()
    parser.add_argument("--begin", help="Beginning of the time interval for images generated", type=int, default=unix_week_ago)
    parser.add_argument("--end", help="End of the time interval for images generated", type=int, default=unix_now)
    parser.add_argument("--days", help="Number of days to look back, overrides --begin and --end", type=int, default=None)
    parser.add_argument("--fps", help="Frames per second for a gif", type=int, default=10)
    parser.add_argument("--ram", help="Optimise the memory usage", action="store_true")
    parser.add_argument("--redraw", help="Regenerate images from csv files", action="store_true")
    args = parser.parse_args()

    from_time, to_time, days = args.begin, args.end, args.days
    ram_optimized = args.ram
    duration = 1000 * (1/args.fps)

    if days != None:
        to_time = int(time.mktime(utc_now.timetuple()))
        from_time = to_time - 86_400 * days

    create_folders()

    if ram_optimized:
        print("Running in memory optimised mode")
        memory_optimised_gif("./outputs/images", from_time, to_time, duration)
    else:
        print("Loading images...")
        images = load_images("./outputs/images", from_time, to_time)
        print("Images loaded, creating the gif...")
        generate_gif(images, from_time, to_time, duration)

        