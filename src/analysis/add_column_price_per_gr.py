import re

import pandas as pd
from sqlite3 import connect

conn = connect("xxxx.db")
df = pd.read_sql('SELECT * FROM darkweb_markets', conn)

price_per_gram = []

for i, item in df.iterrows():
    quantity_gr = item.quantity_gr
    price = item.price
    price_gram = -1

    if quantity_gr != -1:  # There is a real value of quantity (grams)
        price_gram = round(price / quantity_gr, 2)

    print("# %s Product: %s. Price_gram: %s" % (i, item.name_of_product, price_gram))

    price_per_gram.append(price_gram)

# Using DataFrame.insert() to add a column
print(df)

df.insert(9, "price_per_gram", price_per_gram, True)

# Save data
pd.to_numeric(df['price_per_gram'])

print(df)
df.to_sql('darkweb_markets', conn, index=False, if_exists='replace', dtype='int32')
