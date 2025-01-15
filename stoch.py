import time
from datetime import datetime
import ccxt
import pandas as pd
from ta.momentum import StochRSIIndicator
import json  # Importing the json module

# Initialize exchange
exchange = ccxt.bybit({
    "rateLimit": 1200,
    "enableRateLimit": True
})

# List of trading pairs (A)
all_pairs = [
    "BTC/USDT", "LTC/USDT", "LINK/USDT", "TIA/USDT", "ETH/USDT",
    "AVAX/USDT", "DOGE/USDT", "ADA/USDT", "XRP/USDT", "SOL/USDT", "BNB/USDT"
]

# Initialize variables
BL = []  # Long positions list
BS = []  # Short positions list
hold_pairs = []  # List C
refresh_time = 600  # Full refresh interval in seconds

# Function to save the updated BL and BS lists to a JSON file
def save_to_json():
    data = {
        "BL": BL,
        "BS": BS
    }
    with open("pairs.json", "w") as f:
        json.dump(data, f, indent=4)

# Function to clear the JSON file at the end of the refresh time
def clear_json():
    with open("pairs.json", "w") as f:
        json.dump({}, f, indent=4)

# Function to fetch OHLCV data and calculate StochRSI
def get_stochrsi(pair, timeframe="1d"):
    try:
        ohlcv = exchange.fetch_ohlcv(pair, timeframe=timeframe)
        df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
        indicator = StochRSIIndicator(df["close"], window=14, smooth1=3, smooth2=3)
        return round(indicator.stochrsi_k().iloc[-1] * 100, 3)
    except Exception as e:
        print(f"Error fetching StochRSI for {pair}: {e}")
        return None

# Function to process a pair and make a decision based on StochRSI values
def process_pair(pair, T1, T2, T3):
    if T1 is None or T2 is None or T3 is None:
        print(f"{pair}: Missing data. Adding to hold pairs.")
        if pair not in hold_pairs:
            hold_pairs.append(pair)
        if pair in all_pairs:
            all_pairs.remove(pair)
        return

    # Decision logic based on StochRSI values
    if T1 < T2 < T3:
        print(f"{pair}: StochRSI is increasing. Enter Long.")
        if pair not in BL:  # Ensure the pair is added to the Long list
            BL.append(pair)
            save_to_json()  # Save to JSON after updating BL
        if pair in hold_pairs:
            hold_pairs.remove(pair)
        if pair in all_pairs:
            all_pairs.remove(pair)
    elif T1 > T2 > T3:
        print(f"{pair}: StochRSI is decreasing. Enter Short.")
        if pair not in BS:  # Ensure the pair is added to the Short list
            BS.append(pair)
            save_to_json()  # Save to JSON after updating BS
        if pair in hold_pairs:
            hold_pairs.remove(pair)
        if pair in all_pairs:
            all_pairs.remove(pair)
    else:
        print(f"{pair}: No clear trend. Keeping in hold pairs.")
        if pair not in hold_pairs:
            hold_pairs.append(pair)
        if pair in all_pairs:
            all_pairs.remove(pair)

# Main loop
while True:
    print(f"\nStarting new iteration at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    iteration_start = time.time()  # Track start time of the iteration

    # Fetch T1 values for all pairs
    T1_values = {}
    print("\nFetching T1 values for all pairs...")
    for pair in all_pairs[:]:  # Use slicing to avoid modification issues
        T1_values[pair] = get_stochrsi(pair)
    
    # Wait for 60 seconds before fetching T2 values
    print("\nWaiting for 60 seconds before fetching T2 values...")
    time.sleep(60)

    # Fetch T2 values for all pairs
    T2_values = {}
    print("\nFetching T2 values for all pairs...")
    for pair in all_pairs[:]:  # Use slicing to avoid modification issues
        T2_values[pair] = get_stochrsi(pair)
    
    # Wait for 60 seconds before fetching T3 values
    print("\nWaiting for 60 seconds before fetching T3 values...")
    time.sleep(60)

    # Fetch T3 values for all pairs
    T3_values = {}
    print("\nFetching T3 values for all pairs...")
    for pair in all_pairs[:]:  # Use slicing to avoid modification issues
        T3_values[pair] = get_stochrsi(pair)

    # Process each pair in all_pairs using T1, T2, and T3 values
    print("\nProcessing all pairs based on T1, T2, T3 values...")
    for pair in all_pairs[:]:
        T1 = T1_values.get(pair)
        T2 = T2_values.get(pair)
        T3 = T3_values.get(pair)
        process_pair(pair, T1, T2, T3)

    # Process pairs in C every 60 seconds until refresh time elapses
    print("\nProcessing hold pairs (C list)...")
    while (time.time() - iteration_start) < refresh_time:
        if not hold_pairs:
            print("Hold pairs list is empty. Waiting for refresh time to end...")
            break

        # Fetch T1, T2, and T3 for hold pairs
        T1_values_C = {}
        print("\nFetching T1 values for hold pairs...")
        for pair in hold_pairs[:]:
            T1_values_C[pair] = get_stochrsi(pair)
        
        print("\nWaiting for 60 seconds before fetching T2 values for hold pairs...")
        time.sleep(60)

        T2_values_C = {}
        print("\nFetching T2 values for hold pairs...")
        for pair in hold_pairs[:]:
            T2_values_C[pair] = get_stochrsi(pair)
        
        print("\nWaiting for 60 seconds before fetching T3 values for hold pairs...")
        time.sleep(60)

        T3_values_C = {}
        print("\nFetching T3 values for hold pairs...")
        for pair in hold_pairs[:]:
            T3_values_C[pair] = get_stochrsi(pair)

        # Process each pair in hold_pairs using T1, T2, and T3 values
        print("\nProcessing hold pairs (C list) based on T1, T2, T3 values...")
        for pair in hold_pairs[:]:
            T1 = T1_values_C.get(pair)
            T2 = T2_values_C.get(pair)
            T3 = T3_values_C.get(pair)
            process_pair(pair, T1, T2, T3)

        # Print time remaining for refresh
        time_remaining = refresh_time - (time.time() - iteration_start)
        print(f"Time remaining for refresh: {int(time_remaining)} seconds\n")
        time.sleep(60)  # Wait 60 seconds before reprocessing pairs in C

    # End of iteration: Reset data
    print("\nRefreshing for the next iteration...")
    all_pairs = BL + BS + hold_pairs  # Add back all pairs
    BL.clear()
    BS.clear()
    hold_pairs.clear()

    # Clear the JSON file at the end of the refresh time
    clear_json()