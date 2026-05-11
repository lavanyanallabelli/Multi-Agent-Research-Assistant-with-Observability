import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from trading.portfolio import get_open_positions, close_position

positions = get_open_positions()
print("Open positions:", len(positions))

if not positions:
    print("No open positions to close")
else:
    pos = positions[0]
    print(f"Closing {pos['symbol']} @ entry {pos['entry_price']}")
    exit_price = pos["entry_price"] * 1.02  # simulate +2% profit
    result = close_position(pos["id"], exit_price, "MANUAL")
    print("Closed:", result)