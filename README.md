# PulseChain Downloadable Data
Community built and driven collection of tools for data analysis for tokens and wallets on [PulseChain](https://www.pulsechain.com)

All public data, no API keys or access to private resources required, free and open source

# Data Sources
- Blockchain
- Block Explorers
- Dexscreener

If for some reason the scripts are not working properly, it could be because any of the services it's pulling data from is down or interacting with it changed in some way. Check the service to make sure its functioning properly in a web browser before concluding it's broken, but if there is some issue with the script feel free to [Create an Issue](https://github.com/rhmaxdotorg/downloadable-data-pulsechain/issues/new) with all the details so that (no expectations) it can be fixed.

# Quick Start

**Clone or download this repository**

Either click the green Code button -> Download ZIP or `git clone` via HTTPS url or SSH on the command line

**Use the setup scripts in `setup/` directory which would be `windows.bat` for Windows or `mac-or-linux.sh` for Linux**

This will install Python and the dependencies needed to run the scripts.

For Windows, right click `windows.bat` and **Run As Administrator**.

If using Linux, just run the script from command line as administator with `sudo mac-or-linux.sh` or with Mac it should be able to run as a normal user and it prompt to elevate to admin as needed.

**Run a script**

Open a command line prompt, nagivate to where you downloaded the scripts and on Windows just type the name of the script to run it, such as...

`get-token-holders.py`

And on Mac or Linux

`./get-token-holders.py`

If it throws `Permission Denied` error, then `chmod +x get-token-holders.py` (or any other script name that you are trying to run) to make it exectuable and try again.

# Disclaimer
Do not rely on any data from these scripts, it's gathered from public services that may or may not keep things up to date and should be used for education purposes only.

# Scripts

## get-token-holders

Returns a list of holders in ascending order for a given token

Format
`address,amount`

**Example**
```
get-token-holders.py hdrn 0x3819f64f282bf135d62168C1e513280dAF905e06
```

## get-contract-txs

Returns a list of transactions / contract calls details for a given contract or token

Format
`TX hash,method,from,to,value`

**Example**
```
get-contract-txs.py iburn 0xBd2826B7823537fcD30D738aBe4250AD6262209c
```

## get-token-liquidity

Returns a list and total USD amount of DEX liquidity for a given token

Output Format
`dex,LP,token,pair,value`

**Example**
```
get-token-liquidity.py hex 0x2b591e99afE9f32eAA6214f7B7629768c40Eeb39
```

## get-token-volume

Returns a list and total USD amount of 24hr volume for a given token

Output Format
`dex,LP,token,pair,value`

**Example**
```
get-token-volume.py ehex 0x57fde0a71132198BBeC939B98976993d8D89D225
```

## get-burned-tokens

Returns the number of burned tokens for a given token

Output Format
`token,address,number`

**Example**
```
get-burned-tokens.py inc 0x2fa878Ab3F87CC1C9737Fc071108F904c0B0C95d
```

## get-common-holding

Returns a list of common holdings for the holders of a given token

Output Format
`token,address,number`

**Example**
```
get-common-holding.py icsa 0xfc4913214444aF5c715cc9F7b52655e788A569ed
```

## liquidity-sim

Returns theoretical trade impact simulation using V2 AMM (x*y=k) formula with real liquidity data from DEX SCREENER API.

liquidity-sim is a community extension from author [CryptoKong145](https://cryptokong.pls.fyi/) adding theoretical trade impact simulation using the existing infrastructure for PulseChain data analysis.

⚠️ **FOR EDUCATIONAL AND ENTERTAINMENT PURPOSES ONLY** ⚠️

Format
`<token_name> <token_address>`

Output shown to screen containing pool states and price impact

**Example**
```
liquidity-sim.py hex 0x2b591e99afE9f32eAA6214f7B7629768c40Eeb39
```

Features:
- Shows theoretical price impact and pool states
- Tracks USD/token reserves before/after trades
- Historical simulation tracking
- Real-time liquidity data from DEX Screener

## hearts-law-sim

Returns simulated price calculations based on Hearts Law - a price relationship between paired tokens within an AMM. This concept relates to Richard Heart's explanation of liquidity bonding, where token prices may show correlated movements based on their paired liquidity.

hearts-law-sim is a community extension from author [CryptoKong145](https://cryptokong.pls.fyi/) adding the Hearts Law price relationship simulation using the existing infrastructure for PulseChain data analysis.

Learn More: Richard Heart explains [Liquidity Bonding](https://x.com/superhexwin/status/1844208597024244011)
 
⚠️ **FOR EDUCATIONAL AND ENTERTAINMENT PURPOSES ONLY** ⚠️

Format
`<token_name> <pair_address>`

Output shown to screen containing price correlations and calculations

**Example**
```
hearts-law-sim.py hex 0xf1F4ee610b2bAbB05C635F726eF8B0C568c8dc65
```

Features:
- Calculates theoretical future prices
- Tracks price correlations
- Historical simulation tracking
- Multiple pair analysis support

## Important Notes for Simulation Tools (liquidity-sim & hearts-law-sim)

These tools are provided for educational purposes and come with important limitations:

1. Market Reality
- If a large buy comes in as one market order, arbitrage bots would actively reduce the price impact. This would  enrich the people running bots, rather than the typical end user.
- Real trades include fees, slippage, and MEV
- Market sentiment affects actual prices
- DEX Screener may not capture 100% of liquidity/pairs

2. Unaccounted Factors
- Front-running
- Gas costs
- Market reaction
- Network conditions
- MEV 
- TWAP
- Buy and Burns
- Sell Volumes during buy & vice versa
- Add & removal of liquidity

3. Educational Value
Good for understanding:
- AMM mechanics
- Price impact
- Liquidity effects
- Market relationships

❌ NOT for:
- Investment advice
- Trading decisions
- Price predictions
- Financial planning

# Helpers

## csv2json

Converts script CSV default output to JSON

## get-html

Scripts may use this to get code for webpages as needed for data and analysis

## run

Scripts can use this to setup python path to ensure things run smoothly across Windows, Mac and Linux

# Requests
Have an idea or request for another script for data analysis like these?

[Create a Request](https://github.com/rhmaxdotorg/downloadable-data-pulsechain/issues/new) and add detailed information to Title and Description and (no expectations) and it may be considered for a new addition to the toolset.

# Notes
- Scripts may produce visual bar or pie charts, but accuracy may vary and could use fine tuning
- If a script is not producing output, check to see if the website or service it's using is working properly, such as Otterscan or Explorer being down or not working properly for some period of time
