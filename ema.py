import time
import json
from datetime import datetime
import ccxt
import pandas as pd
from ta.trend import EMAIndicator
from telegram_utils import send_telegram_message

message1 = "Enter long position "
message2 = "Enter short position "
message3 = "Hold position "
# Initialize exchange
exchange = ccxt.bybit({
    "rateLimit": 1200,
    "enableRateLimit": True
})

# Function to fetch EMA values and real-time price
def get_ema(pair, timeframe="1d"):
    try:
        ohlcv = exchange.fetch_ohlcv(pair, timeframe=timeframe, limit=200)
        if not ohlcv or len(ohlcv) < 200:
            raise ValueError(f"Insufficient OHLCV data for {pair}")

        df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
        live_price = exchange.fetch_ticker(pair)["last"]
        df.loc[len(df.index)] = [None, None, None, None, live_price, None]
        
        ema_50 = EMAIndicator(close=df["close"], window=50).ema_indicator().iloc[-1]
        ema_200 = EMAIndicator(close=df["close"], window=200).ema_indicator().iloc[-1]
        return live_price, ema_50, ema_200
    except ccxt.BaseError as e:
        print(f"[Exchange Error] Failed to fetch data for {pair}: {e}")
    except ValueError as ve:
        print(f"[Data Error] {ve}")
    except Exception as e:
        print(f"[Unexpected Error] Failed to process {pair}: {e}")
    return None, None, None

# Function to process EMA logic
def process_ema_lists(bl, bs, holding_pairs):
    try:
        if not bl and not bs and not holding_pairs:
            print("[Info] All lists are empty. No pairs to process.")
            return

        for pair in bl:
            live_price, ema_50, ema_200 = get_ema(pair)
            if None in (live_price, ema_50, ema_200):
                print(f"[Warning] Skipping {pair} due to missing data.")
                continue
            if live_price > ema_50 and live_price > ema_200:
              main = f"{pair}:{message1}"
              send_telegram_message(main)
              print(f"{pair}: {message1}")
            else:
              holding_pairs.append(pair)  # Keep for future checking
              print(f"{pair}: {message3}")

        for pair in bs:
            live_price, ema_50, ema_200 = get_ema(pair)
            if None in (live_price, ema_50, ema_200):
                print(f"[Warning] Skipping {pair} due to missing data.")
                continue
            if live_price < ema_50 and live_price < ema_200:
              main = f"{pair}:{message2}"
              send_telegram_message(main)
              print(f"{pair}: {message2}")
            else:
              holding_pairs.append(pair)  # Keep for future checking
              print(f"{pair}: {message3}")

        # Recheck holding pairs for change of status
        for pair in holding_pairs[:]:  # Iterate over a copy to avoid modification during iteration
            live_price, ema_50, ema_200 = get_ema(pair)
            if None in (live_price, ema_50, ema_200):
                print(f"[Warning] Skipping {pair} due to missing data.")
                continue
            if live_price > ema_50 and live_price > ema_200:
                main = f"{pair}:{message1}"
                send_telegram_message(main)
                print(f"{pair}: {message1}")
                holding_pairs.remove(pair)  # Remove from holding if decision is made
            elif live_price < ema_50 and live_price < ema_200:
                main = f"{pair}:{message2}"
                send_telegram_message(main)
                print(f"{pair}: {message2}")
                holding_pairs.remove(pair)  # Remove from holding if decision is made
    except Exception as e:
        print(f"[Unexpected Error] Failed to process lists: {e}")

# Main loop
def main():
    previous_bl, previous_bs = [], []
    holding_pairs = []  # List to track pairs that are on "Hold position"
    last_refresh_time = time.time()

    while True:
        try:
            print(f"\n[Info] Checking lists at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

            # Read BL and BS lists from file
            with open("pairs.json", "r") as file:
                data = json.load(file)
                current_bl = data.get("BL", [])
                current_bs = data.get("BS", [])

            # Full refresh every 600 seconds (10 minutes)
            if time.time() - last_refresh_time >= 600:
                print("[Info] Full refresh triggered. Resetting all lists...")
                previous_bl, previous_bs = [], []  # Reset previous lists
                holding_pairs = []  # Reset holding pairs
                last_refresh_time = time.time()  # Update the refresh time
                print("[Info] Lists reset. Reprocessing all pairs...")

            # Process only new pairs that were added or have changed
            if current_bl != previous_bl or current_bs != previous_bs:
                print("[Info] Changes detected in BL or BS. Processing new pairs and holding pairs...")
                process_ema_lists(current_bl, current_bs, holding_pairs)
                previous_bl, previous_bs = current_bl, current_bs
            else:
                print("[Info] No changes in BL or BS. Waiting for the next check...")

            time.sleep(60)  # Wait before next iteration
        except FileNotFoundError:
            print("[Error] pairs.json not found. Ensure calculate.py is running.")
            time.sleep(60)
        except json.JSONDecodeError:
            print("[Error] Failed to decode JSON. Check if the file is correctly formatted.")
            time.sleep(60)
        except KeyboardInterrupt:
            print("[Info] Process interrupted by user. Exiting...")
            break
        except Exception as e:
            print(f"[Unexpected Error] {e}. Retrying after 60 seconds...")
            time.sleep(60)

if __name__ == "__main__":
    main()