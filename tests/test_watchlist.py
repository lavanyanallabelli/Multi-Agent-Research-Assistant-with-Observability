import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from memory.watchlist import (
    get_watchlist,
    get_all_assets,
    add_to_watchlist,
    remove_from_watchlist,
)

print("Current watchlist:")
for item in get_watchlist():
    print(f"  {item['symbol']} ({item['asset_type']})")

print("\nRemoving ETH from watchlist...")
print(remove_from_watchlist("ETH"))

print("\nWatchlist after remove:")
for item in get_watchlist():
    print(f"  {item['symbol']}")

print("\nAdding ETH back...")
print(add_to_watchlist("ETH"))

print("\nAll assets in universe:")
for item in get_all_assets():
    status = "✅" if item["in_watchlist"] else "⬜"
    print(f"  {status} {item['symbol']} ({item['asset_type']})")