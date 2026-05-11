import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

from trading.alpaca import buy_stock, sell_stock, get_account, get_position

# test account connection
print("=== Account ===")
account = get_account()
print(account)

# test buy
print("\n=== BUY AAPL (1 share) ===")
result = buy_stock("AAPL", 1)
print(result)

# test position
print("\n=== Position AAPL ===")
position = get_position("AAPL")
print(position)