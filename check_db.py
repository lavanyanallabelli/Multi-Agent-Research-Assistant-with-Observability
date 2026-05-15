import sqlite3
import pandas as pd

conn = sqlite3.connect('trading.db')

print('--- OPEN POSITIONS ---')
try:
    positions = pd.read_sql_query("SELECT * FROM positions WHERE symbol='AAPL'", conn)
    print(positions if not positions.empty else 'No open AAPL positions.')
except Exception as e:
    print('Error:', e)

print('\n--- CLOSED TRADES ---')
try:
    trades = pd.read_sql_query("SELECT * FROM trades WHERE symbol='AAPL' ORDER BY closed_at DESC LIMIT 5", conn)
    print(trades if not trades.empty else 'No closed AAPL trades.')
except Exception as e:
    print('Error:', e)

conn.close()
