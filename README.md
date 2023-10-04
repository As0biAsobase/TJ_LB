### Liquidity Book Visualisation Tool

Liquidity Book (LB) is an Automated Market Maker (AMM) designed and deployed by Trader Joe (TJ). Its mechanism is similar to traditional CLOBs (central limit order books), as it places buy- and sell-side liquidity in discrete "pricing bins".

This tool is designed to visualise the state of any particular LB pair across a specified interval and log the changes as the liquidity is deposited/withdrawn and moved in response to market conditions.

## Installation and Setup
1. Ensure Python is installed
2. Run `pip install -r requirements.txt`

## `core.py`

`core.py` is the "core" component of the tool, responsible for logging the state of LB pair. It can be run either in "one-shot" mode, where it'll produce one snapshot or "normal" mode, where it will produce snapshots at regular pre-defined intervals. 
For a full list of accepted parameters run `python core.py --help`.

## `goya.py`

Goya is a drawing component, that can turn a csv snapshot into an image of a Liqudity Book.

![Liquidity Book graph](https://raw.githubusercontent.com/As0biAsobase/TJ_LB/master/examples/lb_avax_usdc_1695062700.png)

For a full list of accepted parameters run `python goya.py --help`.

## `monet.py`

Monet takes images produced by Goya and assembles them into a gif. It can be run in the ram-optimised, where images are loaded one-by-one, or normal mode, where images are loaded in one large batch.

![Output Gif](https://github.com/As0biAsobase/TJ_LB/blob/master/examples/output.gif?raw=true)

For a full list of accepted parameters run `python monet.py --help`.
