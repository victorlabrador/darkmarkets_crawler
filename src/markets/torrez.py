import re


# Execute and commit SQL queries to save on database
def execute_sql(conn, sql, logging, product):
    if conn is not None:
        try:
            c = conn.cursor()
            c.execute(sql)
            conn.commit()
            print("SQL executed correctly! Product: %s" % product)
        except Exception as e:
            logging.info("Error in SQL of product %s. ERROR: %s SQL: %s" % (product, e, sql))
    else:
        logging.error("ERROR! Cannot connect to the database")


# Function to obtain all urls of a product
def obtain_all_products_urls(driver, logging):
    input("1) Solve CAPTCHA\n2) Login into market then press ENTER")
    # Prepare file to write all products
    products_file = open("products.txt", "w")

    # URL to display all contents sorted by old
    url = 'http://yxuy5oau7nugw4kpb4lclrqdbixp3wvc4iuiad23ebyp2q3gx7rtrgqd.onion/items/search?order=created-asc' \
          '&vendors=all&shipping_to=any&shipping_from=any&product_type=any&payments_method=any&search_category=all' \
          '-items'
    driver.get(url)

    page_number = 650
    more_pages = True
    while more_pages:
        # Obtain links for this page
        links_this_page = driver.find_elements_by_xpath(
            '/html/body/div/main/div[2]/div/div[2]/div[2]/div[2]/div[2]/table/tbody/*/td[2]/a')

        for link in links_this_page:
            url_to_write = link.get_property("href")
            if "items" in url_to_write:  # to get links that are a product
                logging.info("This link is a product: %s " % link.text)
                products_file.write("%s\n" % url_to_write)

        # Check if there are more pages
        page_number += 1
        try:
            actual_url = url + "&page=" + str(page_number)
            driver.get(actual_url)
            logging.info("There is another page!")
        except Exception as e:
            more_pages = False
            logging.info("There are no more pages! ERROR: %s " % e)

    products_file.close()


# Function to obtain info of products
def obtain_info_product(driver, url, conn, logging):
    input("1) Solve CAPTCHA\n2) Login into market then press ENTER")

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

            try:
                all_content_text = driver.find_element_by_class_name("singleItemDetails").text

                all_content_by_lines = all_content_text.splitlines()

                name_of_product = driver.find_element_by_class_name("titleHeader.mb-2").\
                    text.replace("'", "''").replace("\"", "\"\"")

                # Searching where shipping from
                i = 0
                categories = "null"
                while i < len(all_content_by_lines):
                    if "Category" in all_content_by_lines[i]:
                        categories = all_content_by_lines[i].replace("Category All Items » ", "")
                        break
                    i += 1

                try:
                    result = re.search(r"([\w| ]+) » (.*)", categories)
                    category = result.group(1)
                    subcategory = result.group(2)
                    if "»" in subcategory:
                        subcategory = subcategory.replace(" »", ",")
                except Exception as e:
                    category = categories
                    subcategory = "null"
                    logging.info("No info related to categories in product \"%s\". Error trying to obtain"
                                 " subcategory of product. ERROR: %s " % (name_of_product, e))

                description = driver.find_element_by_class_name("tab-pane").text\
                    .replace("'", "''").replace("\"", "\"\"")

                # Mirar la quantity con expresiones regulares y el precio tambien, el resto es practicamente directo
                try:
                    result = re.search("([0-9]+[.|,]?[0-9]?[ ]?(mg|MG|gr|GR|ug|UG|Gr|g|G))", name_of_product)
                    quantity = result.group(1)
                except Exception as e:
                    quantity = "1"
                    logging.info("No info related to quantity in product \"%s\". Error trying to obtain"
                                 " quantity of product. ERROR: %s " % (name_of_product, e))

                # Searching the prices
                i = 0
                all_prices = "null"
                while i < len(all_content_by_lines):
                    if "Price" in all_content_by_lines[i]:
                        all_prices = all_content_by_lines[i]
                        break
                    i += 1

                try:
                    result = re.search(r"(€\S+)", all_prices)
                    price = result.group(1)
                except Exception as e:
                    price = all_prices
                    logging.info("Not able to obtain price in € format in product \"%s\". Error trying to obtain"
                                 " price of product. ERROR: %s " % (name_of_product, e))

                i = 0
                views_of_product = "null"
                while i < len(all_content_by_lines):
                    if "Item views" in all_content_by_lines[i]:
                        views_of_product = all_content_by_lines[i].replace("Item views ", "")
                        break
                    i += 1

                # Searching where shipping from
                i = 0
                shipping_from = "null"
                while i < len(all_content_by_lines):
                    if "Ships from" in all_content_by_lines[i]:
                        shipping_from = all_content_by_lines[i].replace("Ships from ", "")
                        break
                    i += 1

                # Searching where shipping from
                i = 0
                shipping_to = "null"
                while i < len(all_content_by_lines):
                    if "Ships to" in all_content_by_lines[i]:
                        shipping_to = all_content_by_lines[i].replace("Ships to ", "")
                        break
                    i += 1

                product_rating = "null"  # This market doesn't have info related to rating of each product

                # Info about the seller
                i = 0
                seller_line = "null"
                while i < len(all_content_by_lines):
                    if "Sold by" in all_content_by_lines[i]:
                        seller_line = all_content_by_lines[i]
                        break
                    i += 1

                try:
                    result = re.search(r"(Sold by )(\w+)(.*)", seller_line)
                    seller = result.group(2)
                except Exception as e:
                    seller = "null"
                    logging.info("Not able to obtain seller of product \"%s\". Error trying to obtain"
                                 " seller of product. ERROR: %s " % (name_of_product, e))

                url_seller = "http://yxuy5oau7nugw4kpb4lclrqdbixp3wvc4iuiad23ebyp2q3gx7rtrgqd.onion/profile/" + seller

                driver.get(url_seller)

                seller_info_total = driver.find_elements_by_xpath("/html/body/div/main/div[2]/div/div[2]/div[3]")[
                    0].text
                seller_info = seller_info_total.splitlines()
                seller_rating_info = seller_info[5]
                try:
                    result = re.search(r"(.* )(\S+%) \((\d+)\)", seller_rating_info)
                    seller_rating = result.group(2)
                    seller_number_ratings = result.group(3)
                except Exception as e:
                    seller_rating = "null"
                    seller_number_ratings = "null"
                    logging.info("Not able to obtain seller ratings. ERROR: %s " % e)

                seller_number_of_sales = seller_info[3].replace("Total Amount Of Transactions ", "")

                seller_profile = \
                    driver.find_elements_by_xpath("/html/body/div/main/div[2]/div/div[2]/div[4]/div[2]/div/div/div")[
                        0].text.replace("'", "''").replace("\"", "\"\"")

                url_fingerprint = url_seller + "/pgp"
                driver.get(url_fingerprint)

                seller_fingerprint = driver.find_elements_by_xpath(
                    "/html/body/div/main/div[2]/div/div[2]/div[4]/div[2]/div/div/div/div/p[1]")[0].text.replace(
                    "Fingerprint: ", "")

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
                      'datetime(\'now\'), "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", ' \
                      '"%s", "%s", "%s", "%s", "%s"); ' \
                      % (market, category, subcategory, name_of_product, description, quantity, price,
                         views_of_product, shipping_from, shipping_to, product_rating, seller, seller_profile,
                         seller_fingerprint, seller_rating, seller_number_ratings, seller_number_of_sales)

                execute_sql(conn, sql, logging, name_of_product)

            except Exception as e:
                logging.info("This URL product doesn't exists... Going next. ERROR: %s " % e)

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
