import datetime, argparse, time
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Goya knows how to turn a Liquidity Book snapshot into a png
def draw_the_book(df: pd.DataFrame, timestamp: int, active_bin: int, symbolX: str, symbolY: str, height: int = 21) -> None:
    tick_gap = 10

    dt = datetime.datetime.utcfromtimestamp(timestamp)
    label = f"{symbolX}-{symbolY} pair on {dt:%Y-%m-%d %H:%M:%S}"

    xticks = df.bin_id[::tick_gap]
    xtick_lables = df.bin_price[::tick_gap]
    yticks = [i*10_000 for i in range(0, height)]

    fig, ax = plt.subplots()

    ax.bar(list(df.bin_id), list(df.reserveY), label=symbolY, color='b', edgecolor="none")
    ax.bar(list(df.bin_id), list(df.reserveX_in_Y), bottom=np.array(df.reserveY, dtype=float), label=symbolX, color='r', edgecolor="none")

    ax.set_ylabel('Reserves ($)')
    ax.set_xlabel('Price ($)')
    ax.set_title(label)
    ax.legend()

    ax.ticklabel_format(style='plain', useOffset=False)
    fig.set_size_inches(18.5, 10.5, forward=True)
    ax.set_xticks(xticks)
    ax.set_xticklabels(np.round(xtick_lables, 4), rotation=90)
    ax.set_yticks(yticks)
    ax.axvline(x=active_bin, color='red', linestyle='--', label='Current Price')

    plt.savefig(f'outputs/images/lb_{symbolX.lower()}_{symbolY.lower()}_{timestamp}.png')
    print(f"Saved image to outputs/images/lb_{symbolX.lower()}_{symbolY.lower()}_{timestamp}.png")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", help="Path to the csv file", default="./outpput.csv")
    parser.add_argument("--symbolX", help="Symbol of the first token", default="AVAX")
    parser.add_argument("--symbolY", help="Symbol of the second token", default="USDC")
    parser.add_argument("--activeBin", help="Active bin in the book", default=201)
    args = parser.parse_args()
    path = args.path
    symbolX, symbolY = args.symbolX, args.symbolY
    active_bin = int(args.activeBin)

    df = pd.read_csv(path)  
    draw_the_book(df, int(time.time()), active_bin, symbolX, symbolY)
