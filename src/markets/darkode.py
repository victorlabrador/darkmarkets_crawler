import re

number_of_products = 0


# Execute and commit SQL queries to save on database
def execute_sql(conn, sql, logging, product):
    if conn is not None:
        try:
            c = conn.cursor()
            c.execute(sql)
            conn.commit()
            global number_of_products
            number_of_products += 1
            print("#%s SQL executed correctly! Product: %s" % (number_of_products, product))
        except Exception as e:
            logging.info("Error in SQL of product %s. ERROR: %s SQL: %s" % (product, e, sql))
    else:
        logging.error("ERROR! Cannot connect to the database")


# Function to obtain info about the seller that is already on DB
def obtain_seller_info(seller, conn):
    c = conn.cursor()
    c.execute("SELECT seller_profile, seller_fingerprint, seller_rating, seller_number_ratings, "
              "seller_number_of_sales FROM darkweb_markets WHERE seller=?", (seller,))
    rows = c.fetchall()

    return rows[0]


# Function to obtain all urls of a product
def obtain_all_products_urls(driver, logging, products_file):
    input("1) Solve CAPTCHA\n2) Login into market then press ENTER")
    # Prepare file to write all products
    products_file = open(products_file, "w")

    # URL to display all contents sorted by old
    url = 'http://darkodemard3wjoe63ld6zebog73ncy77zb2iwjtdjam4xwvpjmjitid.onion/search?page=3842&stype=All&sorigin' \
          '=All&sdest=All&svendor=All&sdeaddrop=All&minprice=0&maxprice=9999999&searchterm=&weight=0&unit=All&purity' \
          '=0&sortby=Oldest '
    driver.get(url)

    page_number = 3842
    more_pages = True
    while more_pages:
        # Obtain links for this page
        links_this_page = driver.find_elements_by_xpath("/html/body/div[2]/div[1]/div[1]/div[1]/div[2]/div[2]/div["
                                                        "2]/*/div/div[1]/a")

        for link in links_this_page:
            url_to_write = link.get_property("href")
            if "product" in url_to_write:  # to get links that are a product
                logging.info("This link is a product: %s " % url_to_write.replace(
                    "http://darkodemard3wjoe63ld6zebog73ncy77zb2iwjtdjam4xwvpjmjitid.onion", ""))
                products_file.write("%s\n" % url_to_write)

        print("Pagina %s obtenida con un total de %s productos" % (page_number, len(links_this_page)))
        # Check if there are more pages
        page_number += 1
        try:
            if page_number == 3846:
                more_pages = False
                logging.info("There are no more pages!")
            else:
                next_page = "page=" + str(page_number)
                actual_url = re.sub(r'page=\d+', next_page, url)
                driver.get(actual_url)
                logging.info("There is another page!")
        except Exception as e:
            more_pages = False
            logging.info("There are no more pages! ERROR: %s " % e)

    products_file.close()


# Function to obtain info of products
def obtain_info_product(driver, url, conn, logging, products_file):
    input("1) Solve CAPTCHA\n2) Login into market then press ENTER")

    # Read products from file
    try:
        readable_file = open(products_file, "r")

        # Read all content to write it back
        lines = readable_file.readlines()
        readable_file.close()

        market = re.sub(r"http://(\w+).*", r"\1", url)
        logging.info("Starting with marketplace: %s" % market)

        sellers = []

        while lines:
            product = lines[0].replace("\n", "")

            # Access this product
            driver.get(product)

            try:
                all_content_text = driver.find_element_by_class_name("product-description").text
                all_content_by_lines = all_content_text.splitlines()

                name_of_product = all_content_by_lines[0]

                more_information = driver.find_element_by_class_name("place-orders").text
                more_information_by_lines = more_information.splitlines()

                # Searching where shipping from
                i = 0
                categories = "null"
                while i < len(more_information_by_lines):
                    if "Category" in more_information_by_lines[i]:
                        categories = more_information_by_lines[i].replace("Category: ", "")
                        break
                    i += 1

                try:
                    result = re.search(r"([\w| ]+)(, (.*))?", categories)
                    category = result.group(1)
                    subcategory = result.group(3)
                except Exception as e:
                    category = categories
                    subcategory = "null"
                    logging.info("No info related to categories in product \"%s\". Error trying to obtain"
                                 " subcategory of product. ERROR: %s " % (name_of_product, e))

                description = driver.find_elements_by_xpath("/html/body/div[2]/div[1]/div[1]/div/div[1]/div[1]/div["
                                                            "6]/div[2]/xmp[1]")[0].text.replace("'", "''") \
                    .replace("\"", "\"\"")

                try:
                    result = re.search("([0-9]+[.|,]?[0-9]?[ ]?(mg|MG|gr|GR|ug|UG|Gr|g|G|GRAM|gram))", name_of_product)
                    quantity = result.group(1)
                except Exception as e:
                    quantity = "1"
                    logging.info("No info related to quantity in product \"%s\". Error trying to obtain"
                                 " quantity of product. ERROR: %s " % (name_of_product, e))

                # Searching the prices
                j = 0
                all_prices = "null"
                while j < len(all_content_by_lines):
                    if "Price" in all_content_by_lines[j]:
                        all_prices = all_content_by_lines[j]
                        break
                    j += 1

                try:
                    result = re.search(r"(EUR \S+)", all_prices)
                    price = result.group(1)
                except Exception as e:
                    price = all_prices
                    logging.info("Not able to obtain price in € format in product \"%s\". Error trying to obtain"
                                 " price of product. ERROR: %s " % (name_of_product, e))

                views_of_product = "null"  # This market doesn't have info related to views of each product

                # Searching where shipping from
                k = 0
                shipping_from = "null"
                while k < len(more_information_by_lines):
                    if "Supplier Location" in more_information_by_lines[k]:
                        shipping_from = more_information_by_lines[k].replace("Supplier Location(s): ", "")
                        break
                    k += 1

                # Searching where shipping to
                n = 0
                shipping_to = "null"
                while n < len(more_information_by_lines):
                    if "Shipping to" in more_information_by_lines[n]:
                        shipping_to = more_information_by_lines[n].replace("Shipping to (vendor): ", "")
                        break
                    n += 1

                product_rating = all_content_by_lines[1]
                try:
                    result = re.search(r"([.\d]+ /5) .*", product_rating)
                    product_rating = result.group(1)
                except Exception as e:
                    product_rating = "No reviews"
                    logging.info("Not able to obtain reviews in product \"%s\". Error trying to obtain"
                                 " reviews of product. ERROR: %s " % (name_of_product, e))

                # Info about the seller
                m = 0
                seller_line = "null"
                while m < len(all_content_by_lines):
                    if "Vendor" in all_content_by_lines[m]:
                        seller_line = all_content_by_lines[m]
                        break
                    m += 1

                try:
                    result = re.search(r"(Vendor: )(\w+)(.*)", seller_line)
                    seller = result.group(2)
                except Exception as e:
                    seller = "null"
                    logging.info("Not able to obtain seller of product \"%s\". Error trying to obtain"
                                 " seller of product. ERROR: %s " % (name_of_product, e))

                if seller in sellers:
                    info_about_seller = obtain_seller_info(seller, conn)

                    seller_profile = info_about_seller[0]
                    seller_fingerprint = info_about_seller[1]
                    seller_rating = info_about_seller[2]
                    seller_number_ratings = info_about_seller[3]
                    seller_number_of_sales = info_about_seller[4]

                else:  # Obtain all seller info
                    url_seller = "http://darkodemard3wjoe63ld6zebog73ncy77zb2iwjtdjam4xwvpjmjitid.onion/" \
                                 + seller + "/profile "

                    driver.get(url_seller)

                    seller_rating_all_info = driver.find_element_by_class_name("main_right_info").text.splitlines()
                    seller_rating_info = seller_rating_all_info[0]
                    try:
                        result = re.search(r"([.\d]+ /5) \((\d+).*", seller_rating_info)
                        seller_rating = result.group(1)
                        seller_number_ratings = result.group(2)
                    except Exception as e:
                        seller_rating = "null"
                        seller_number_ratings = "null"
                        logging.info("Not able to obtain seller ratings. ERROR: %s " % e)

                    seller_number_of_sales = driver.find_element_by_class_name("user-rating").text

                    seller_profile = driver.find_element_by_class_name("prod_blocks").text.replace("'", "''").replace(
                        "\"", "\"\"")

                    try:
                        seller_fingerprint = \
                            driver.find_elements_by_xpath(
                                "/html/body/div[2]/div[1]/div[1]/div[2]/div[1]/div/div[2]/div/xmp")[
                                0].text
                    except Exception as e:
                        seller_fingerprint = "null"
                        logging.info("Not able to obtain PGP seller. ERROR: %s " % e)

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
                sellers.append(seller)

                # Remove product of file to have some log of processed products
                del lines[0]
                writable_file = open(products_file, "w+")
                for line in lines:
                    writable_file.write(line)
                writable_file.close()

                # Read again the file
                readable_file = open(products_file, "r")
                lines = readable_file.readlines()
                readable_file.close()

            except Exception as e:
                logging.info("Stopped by timeout. Resolve CAPTCHA and continue. ERROR: %s " % e)
                input("Solve CAPTCHA then press ENTER")

    except Exception as e:
        logging.error("ERROR retrieving some product: %s " % e)
