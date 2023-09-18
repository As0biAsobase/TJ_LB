import os, sys, signal, multiprocessing, requests, argparse, logging
import time, datetime
from pathlib import Path
from web3 import Web3
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Tuple

def exit_handler(signal, frame):
    print("\nKeyboard Interrupt, program exiting gracefully")
    sys.exit(0)

def create_folders() -> None:
    Path("./outputs/csvs").mkdir(parents=True, exist_ok=True)
    Path("./outputs/images").mkdir(parents=True, exist_ok=True)
    Path("./logs").mkdir(parents=True, exist_ok=True)

def load_pair():
    global w3
    w3 = Web3(Web3.HTTPProvider("https://api.avax.network/ext/bc/C/rpc"))

    lb_impl = Web3.to_checksum_address("0xee5A90098b270596Ec35D637b30d908C862c86df")
    abi=requests.get(f"https://api.snowtrace.io/api?module=contract&action=getabi&address={lb_impl}").json()['result']

    # Each pair is deployed as a proxy contract, so we get ABI from implementation, but interact with the proxy itself
    lb_proxy = Web3.to_checksum_address("0xD446eb1660F766d533BeCeEf890Df7A69d26f7d1")
    contract = w3.eth.contract(address=lb_proxy, abi=abi)

    return contract

def get_decimals(address) -> int:
    abi=requests.get(f"https://api.snowtrace.io/api?module=contract&action=getabi&address={Web3.to_checksum_address(address)}").json()['result']

    contract = w3.eth.contract(address=address, abi=abi)
    return contract.functions.decimals().call()

def get_tokens() -> Tuple[str, str]:
    tokenX = contract.functions.getTokenX().call()
    tokenY = contract.functions.getTokenY().call()

    return tokenX, tokenY

def get_target_bins(offset: int = 200) -> Tuple[list, int]:
    # We start by finding the current "active" bin and then find all bins with liquidity to the left and to the right
    active_bin = contract.functions.getActiveId().call()
    left_bins = [contract.functions.getNextNonEmptyBin(True, active_bin).call()]
    right_bins = [contract.functions.getNextNonEmptyBin(False, active_bin).call()]

    print("Looking for left-side bins with liqudity in them...")

    while True:
        next_bin = contract.functions.getNextNonEmptyBin(True, left_bins[0]).call()
        if next_bin > left_bins[0] or len(left_bins)==offset:
            break
        else:
            left_bins.insert(0, next_bin)

    print("Found all left-side bins, looking for right-side bins...")

    while True:
        next_bin = contract.functions.getNextNonEmptyBin(False, right_bins[-1]).call()
        if next_bin < right_bins[-1] or len(right_bins)==offset:
            break
        else:
            right_bins.append(next_bin) 
    
    return left_bins + [active_bin] + right_bins, active_bin

def get_liquidity_shape(target_bins: list) -> list:
    data = []
    bin_step = 0.002

    print("Retreiving all bins...")

    for i, bin in enumerate(target_bins):
        print(f"Retrieving bin {i} out of {len(target_bins)}. {len(target_bins)-i} bins left", end="\r")
        reserveX, reserveY = contract.functions.getBin(bin).call()
        bin_price = (1+bin_step)**(bin-2**23)
        data.append({"bin_id" : bin, "reserveX" : reserveX, "reserveY" : reserveY, "bin_price" : bin_price})

    print("Liquidity shape retrieved")

    return data

def process_bin(bin):
    bin_step = 0.002
    reserveX, reserveY = contract.functions.getBin(bin).call()
    bin_price = (1+bin_step)**(bin-2**23)
    print(f"Processing {bin}", end="\r")
    return {"bin_id" : bin, "reserveX" : reserveX, "reserveY" : reserveY, "bin_price" : bin_price}

def get_liquidity_shape_parallel(target_bins: list) -> list:
    corecount = os.cpu_count()
    print(f"Getting liquidity shape, using {corecount} threads")
    with multiprocessing.Pool(processes=corecount) as pool:
        results = pool.map(process_bin, target_bins)

    return results

def process_data(data: list, timestamp: int, min: int = 7, max: int = 12) -> pd.DataFrame:
    df = pd.DataFrame.from_dict(data)
    df.set_index('bin_id')

    tokenX_decimals = 18
    tokenY_decimals = 6

    df['reserveX'] = df['reserveX'].div(10**tokenX_decimals)
    df['reserveY'] = df['reserveY'].div(10**tokenY_decimals) 
    df['bin_price'] = df['bin_price'] * 10**(tokenX_decimals-tokenY_decimals)
    df["reserveX_in_Y"] = df['reserveX'] * df['bin_price']

    df = df[(df.bin_price > min) & (df.bin_price < max)]
    path = f'outputs/csvs/lb_avax_usdc_{timestamp}.csv'
    df.to_csv(path) 

    print(f"Dataframe processed and saved to {path}")

    return df

def draw_the_book(df: pd.DataFrame, timestamp: int, active_bin: int) -> None:
    tick_gap = 10

    tokenX_symbol = "AVAX"
    tokenY_symbol = "USDC"
    dt = datetime.datetime.utcfromtimestamp(timestamp)
    label = f"{tokenX_symbol}-{tokenY_symbol} pair on {dt:%Y-%m-%d %H:%M:%S}"

    xticks = df.bin_id[::tick_gap]
    xtick_lables = df.bin_price[::tick_gap]
    yticks = [i*10_000 for i in range(0, 21)]

    fig, ax = plt.subplots()

    ax.bar(list(df.bin_id), list(df.reserveY), label=tokenY_symbol, color='b', edgecolor="none")
    ax.bar(list(df.bin_id), list(df.reserveX_in_Y), bottom=np.array(df.reserveY, dtype=float), label=tokenX_symbol, color='r', edgecolor="none")

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

    plt.savefig(f'outputs/images/lb_avax_usdc_{timestamp}.png')

signal.signal(signal.SIGINT, exit_handler)

if __name__ == "__main__":
    global contract

    create_folders()
    logging.basicConfig(filename='./logs/nestor_all.log', level=logging.DEBUG)
    logging.basicConfig(filename='./logs/nestor_core.log', level=logging.INFO)
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--oneshot", help="Create a one-shot snapshot of liquidity and exit", action="store_true")
    args = parser.parse_args()
    one_shot = args.oneshot

    print("Starting the execution...")
    contract = load_pair()
    tokenX, tokenY = get_tokens()

    if one_shot: print("Running in one-shot mode")
    else: print("Main loop started, snaphoting every 15 minutes")
    
    while True:
        if (time.localtime().tm_min % 15 == 0 and time.localtime().tm_sec == 0) or one_shot == True:
            try:
                timestamp = int(time.time())
                target_bins, active_bin = get_target_bins()

                start = int(time.time())
                data = get_liquidity_shape_parallel(target_bins)

                df = process_data(data, timestamp)
                draw_the_book(df, timestamp, active_bin)
                
                print(f"Snaphot - {timestamp} completed in {int(time.time())-start}s")
                logging.info(f"{datetime.datetime.utcnow()}: Snaphot - {timestamp} completed in {int(time.time())-start}s")
            except:
                logging.error(f"{datetime.datetime.utcnow()}: Couldn't complete a snapshot")
                time.sleep(1)
            if one_shot: break
        time.sleep(0.1)

