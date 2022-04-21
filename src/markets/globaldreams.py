import re


# Execute and commit SQL queries to save on database
def execute_sql(conn, sql, logging):
    if conn is not None:
        c = conn.cursor()
        c.execute(sql)
        conn.commit()
    else:
        logging.error("ERROR! Cannot connect to the database")


# Function to obtain all urls of a product
def obtain_all_products_urls(driver, logging):
    links_category = driver.find_elements_by_tag_name("a")

    # Prepare file to write all products
    products_file = open("products.txt", "w")

    categories = []
    # Loop to obtain all categories
    for link in links_category:
        url = link.get_property("href")
        if "product_cat" in url:  # to get links of product_category
            logging.info("This link is a category: %s " % link.text)
            categories.append(url)

    # Loop to obtain list of products
    for category in categories:
        # Access this category
        driver.get(category)
        products_links = driver.find_elements_by_xpath("/html/body/div/main/div/div/div/ul/li[*]")

        # Obtain URLs of products in the actual page
        for product in products_links:
            url = product.find_elements_by_tag_name("a")[0].get_property("href")
            if "product" in url:
                logging.info("This link is a product: %s " % product.text)

                products_file.write("%s\n" % url)

        # Check if there are more pages
        next_pages = []
        links = driver.find_elements_by_tag_name("a")
        for link in links:
            url = link.get_property("href")
            if "paged" in url:
                if url not in next_pages:  # Needed because page "2" and "next" page have the same value
                    next_pages.append(url)

        # Loop to acces all pages of the same category
        for page in next_pages:
            driver.get(page)
            products_links = driver.find_elements_by_xpath("/html/body/div/main/div/div/div/ul/li[*]")

            for product in products_links:
                url = product.find_elements_by_tag_name("a")[0].get_property("href")
                if "product" in url:
                    logging.info("This link is a product: %s " % product.text)
                    products_file.write("%s\n" % url)

    products_file.close()


# Function to obtain info of products
def obtain_info_product(driver, url, conn, logging):
    # Read products from file
    try:
        readable_file = open("products.txt", "r")

        # Read all content to write it back
        lines = readable_file.readlines()
        readable_file.close()

        market = re.sub(r"http://(\w+).*", r"\1", url)
        logging.info("Starting with marketplace: %s" % market)

        while lines:
            product = lines[0].replace("\n", "")

            # Access this product
            driver.get(product)

            category = "Drugs"
            subcategory = driver.find_element_by_class_name("posted_in").\
                text.replace("Category: ", "").replace("Categories: ", "")
            name_and_quantity = driver.find_element_by_class_name("product_title").text

            logging.info("Retrieving info from product %s" % name_and_quantity)

            # Regex to obtain quantity and name of product
            try:
                result = re.search("([0-9]+[.|,]?[0-9]?[ ]?(mg|gr|ug|Gr))", name_and_quantity)
                quantity = result.group(1)
                name_of_product = re.sub("( – )?([0-9]+[.|,]?[0-9]?[ ]?(mg|gr|ug|Gr))", "", name_and_quantity)
            except Exception as e:
                name_of_product = name_and_quantity
                logging.info("No info related to quantity in product \"%s\". Error trying to obtain"
                             " quantity of product: %s " % (name_of_product, e))
                quantity = "null"

            # Regex to extract the actual price, not the previous one
            price = driver.find_element_by_class_name("price").text
            try:
                result = re.search("€[0-9]+.[0-9]+$", price)
                price = result.group(0)
            except Exception as e:
                logging.info("There is not \"2\" prices, only one on product \"%s\". Error trying to "
                             "obtain the price: %s" % (name_of_product, e))

            description = driver.find_element_by_id("tab-description").text

            views_of_product = "null"  # This market doesn't say the views of each product
            shipping_from = "null"  # This market doesn't say where they ship from
            shipping_to = "null"   # This market doesn't say where they ship to
            product_rating = "null"  # This market doesn't have ratings of products
            seller = "null"  # This market doesn't say the seller
            seller_profile = "null"  # This market doesn't have info about the seller
            seller_fingerprint = "null"  # This market doesn't have info about the seller
            seller_rating = "null"  # This market doesn't have info about the seller
            seller_number_ratings = "null"  # This market doesn't have info about the seller
            seller_number_of_sales = "null"  # This market doesn't have info about the seller

            sql = 'INSERT INTO darkweb_markets (' \
                  'timestamp, ' \
                  'market, ' \
                  'category, ' \
                  'subcategory, ' \
                  'name_of_product, ' \
                  'description, ' \
                  'quantity, ' \
                  'price, ' \
                  'views_of_product, ' \
                  'shipping_from, ' \
                  'shipping_to, ' \
                  'product_rating, ' \
                  'seller, ' \
                  'seller_profile, ' \
                  'seller_fingerprint, ' \
                  'seller_rating, ' \
                  'seller_number_ratings, ' \
                  'seller_number_of_sales) ' \
                  'VALUES (' \
                  'datetime(\'now\'), "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", ' \
                  '"%s", "%s", "%s", "%s"); ' \
                  % (market, category, subcategory, name_of_product, description, quantity, price, views_of_product,
                     shipping_from, shipping_to, product_rating, seller, seller_profile, seller_fingerprint,
                     seller_rating, seller_number_ratings, seller_number_of_sales)

            execute_sql(conn, sql, logging)

            # Remove product of file to have some log of processed products
            del lines[0]
            writable_file = open("products.txt", "w+")
            for line in lines:
                writable_file.write(line)
            writable_file.close()

            # Read again the file
            readable_file = open("products.txt", "r")
            lines = readable_file.readlines()
            readable_file.close()

    except Exception as e:
        logging.error("ERROR retrieving some product: %s " % e)
