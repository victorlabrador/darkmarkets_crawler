import re

import pandas as pd
from sqlite3 import connect

conn = connect("xxxxx.db")
df = pd.read_sql('SELECT * FROM darkweb_markets', conn)

new_quantities = []

for i, item in df.iterrows():
    name_product = item.name_of_product
    new_quantity = item.quantity
    category = item.category
    subcategory = item.subcategory

    if new_quantity == "1":
        # Maybe one product or maybe 1 kg
        try:
            new_quantity = re.search(r"([0-9]+[.|,]?[0-9]?[ ]?(mg|MG|gr|kilos|kg|KG|GR|ug|UG|Gr|g|G|GRAM|gram|ml))",
                                     name_product).group(1)
        except Exception as e:
            new_quantity = "-1"

    if new_quantity != "-1":
        new_quantity = str(new_quantity).lower() 
        if "mg" in new_quantity:
            value = re.search(r"(\d+([,.]\d+)?)", new_quantity).group(1).replace(",", ".")
            new_quantity = float(value) / 1000
        elif "ug" in new_quantity:
            value = re.search(r"(\d+([,.]\d+)?)", new_quantity).group(1).replace(",", ".")
            new_quantity = float(value) / 1000000
        elif "k" in new_quantity:
            value = re.search(r"(\d+([,.]\d+)?)", new_quantity).group(1).replace(",", ".")
            new_quantity = float(value) * 1000
        elif "ml" in new_quantity:
            value = re.search(r"(\d+([,.]\d+)?)", new_quantity).group(1).replace(",", ".")
            new_quantity = float(value) / 1000
        elif "gr" or "g" in new_quantity:
            value = re.search(r"(\d+([,.]\d+)?)", new_quantity).group(1).replace(",", ".")
            new_quantity = float(value)
    else:
        new_quantity = "-1"

    print("# %s Before: %s. Now: %s" % (i, item.quantity, new_quantity))

    new_quantities.append(new_quantity)

# Using DataFrame.insert() to add a column
print(df)

df.insert(7, "quantity_gr", new_quantities, True)

# Save data
pd.to_numeric(df['quantity_gr'])

print(df)
df.to_sql('darkweb_markets', conn, index=False, if_exists='replace', dtype='int32')
