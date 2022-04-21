import re

import pandas as pd
from sqlite3 import connect

conn = connect("xxx.db")
df = pd.read_sql('SELECT * FROM darkweb_markets', conn)

print(df['price'])

for i, value in df.iterrows():
    price = value.price
    if "null" in price:
        df['price'][i] = 0.0
        print("# %s. Before: %s. After: %s" % (i + 1, price, 0.0))
    if "€" in price:
        new_value = price.replace("€", "").replace(",", "")
        df['price'][i] = new_value
        print("# %s. Before: %s. After: %s" % (i + 1, price, new_value))
    else:
        print("# %s. Value not changed: %s" % (i + 1, price))

print(df['price'])

# Save data
pd.to_numeric(df['price'])
df.to_sql('darkweb_markets', conn, index=False, if_exists='replace', dtype='int32')
