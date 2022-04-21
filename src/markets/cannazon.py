import re
import time

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
    c.execute("SELECT seller_profile, seller_pgp, seller_rating, seller_number_ratings, "
              "seller_number_of_sales FROM darkweb_markets WHERE seller=?", (seller,))
    rows = c.fetchall()

    return rows[0]


# Function to obtain all urls of a product
def obtain_all_products_urls(driver, logging, products_file):
    input("1) Solve CAPTCHA\n2) Login into market then press ENTER")
    # Prepare file to write all products
    products_file = open(products_file, "w")

    # URL to display all contents sorted by old
    url = 'http://cannazo73ou34ev3vnvuq75wb2ienpcztqudkdozpuitvykqhvtiffyd.onion/products?sorting=1'
    actual_url = url + '&page=1'
    driver.get(actual_url)

    page_number = 1
    more_pages = True
    already_links = []
    while more_pages:
        # Obtain links for this page
        links_this_page = driver.find_elements_by_xpath(
            "/html/body/div/div[3]/div/div[2]/div[3]/div[1]/*/div/div/div/a")
        if len(links_this_page) == 0:  # There is nothing in this page, no more pages
            break
        for link in links_this_page:
            url_to_write = link.get_property("href")
            if "products" in url_to_write and url_to_write not in already_links:  # to get links that are a product
                logging.info("This link is a product: %s " % link.text)
                already_links.append(url_to_write)
                products_file.write("%s\n" % url_to_write)

        # Check if there are more pages
        page_number += 1
        try:
            actual_url = url + "&page=" + str(page_number)
            time.sleep(10)
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
            time.sleep(3)
            driver.get(product)

            try:
                all_content_text = driver.find_elements_by_xpath("/html/body/div/div[3]/div/div[2]/div[2]/div[1]/div["
                                                                 "2]/div[1]/p")
                all_content_by_lines = []

                if not all_content_text:
                    # Error on product, maybe doesn't exist anymore
                    global number_of_products
                    number_of_products += 1
                    print("#%s ERROR!! Product: %s." % (number_of_products, product))
                    error_file = open("errors.txt", "w")
                    error_file.write("%s\n" % product)
                    error_file.close()

                    del lines[0]
                    writable_file = open(products_file, "w+")
                    for line in lines:
                        writable_file.write(line)
                    writable_file.close()

                    # Read again the file
                    readable_file = open(products_file, "r")
                    lines = readable_file.readlines()
                    readable_file.close()

                    continue

                for content in all_content_text:
                    all_content_by_lines.append(content.text)

                name_of_product = \
                    driver.find_elements_by_xpath("/html/body/div/div[3]/div/div[2]/div[2]/div[1]/div[2]/div[1]/h2")[
                        0].text

                more_information = driver.find_element_by_class_name(
                    "product-information.border-box.container-box.product-information-vendor").text
                more_information_by_lines = more_information.splitlines()

                # Searching category
                i = 0
                categories = "null"
                while i < len(all_content_by_lines):
                    if "Category" in all_content_by_lines[i]:
                        categories = all_content_by_lines[i].replace("Category: ", "")
                        break
                    i += 1

                try:
                    result = re.search(r"(\w+) > (\w+)", categories)
                    category = result.group(1)
                    subcategory = result.group(2)
                except Exception as e:
                    category = categories
                    subcategory = "null"
                    logging.info("No info related to categories in product \"%s\". Error trying to obtain"
                                 " subcategory of product. ERROR: %s " % (name_of_product, e))

                description = driver.find_elements_by_xpath("/html/body/div/div[3]/div/div[2]/div[2]/div[2]/div/div/"
                                                            "div[1]")[0].text.replace("'", "''").replace("\"", "\"\"")

                try:
                    result = re.search("([0-9]+[.|,]?[0-9]?[ ]?(mg|MG|gr|GR|ug|UG|Gr|g|G|GRAM|gram))", name_of_product)
                    quantity = result.group(1)
                except Exception as e:
                    quantity = "1"
                    logging.info("No info related to quantity in product \"%s\". Error trying to obtain"
                                 " quantity of product. ERROR: %s " % (name_of_product, e))

                # Searching the prices
                j = 0
                price = 0
                while j < len(all_content_by_lines):
                    if "€" in all_content_by_lines[j]:
                        price = float(all_content_by_lines[j].replace("€", ""))
                        break
                    j += 1

                # try:
                #     result = re.search(r"(EUR \S+)", all_prices)
                #     price = result.group(1)
                # except Exception as e:
                #     price = all_prices
                #     logging.info("Not able to obtain price in € format in product \"%s\". Error trying to obtain"
                #                  " price of product. ERROR: %s " % (name_of_product, e))

                views_of_product = "null"  # This market doesn't have info related to views of each product

                # Searching where shipping from
                k = 0
                shipping_from = "null"
                while k < len(more_information_by_lines):
                    if "Shipping From" in more_information_by_lines[k]:
                        shipping_from = more_information_by_lines[k].replace("Shipping From: ", "")
                        break
                    k += 1

                # Searching where shipping to
                n = 0
                shipping_to = "null"
                while n < len(more_information_by_lines):
                    if "Shipping To" in more_information_by_lines[n]:
                        shipping_to = more_information_by_lines[n].replace("Shipping To: ", "")
                        break
                    n += 1

                url_ratings = product + "#ratings"
                driver.get(url_ratings)

                product_rating_info = \
                    driver.find_elements_by_xpath("/html/body/div/div[3]/div/div[2]/div[2]/div[2]/div/div/div[2]/ul")[
                        0].text
                positive_rating = int(re.search(r"POSITIVE \((\w+)\)", product_rating_info).group(1))
                negative_rating = int(re.search(r"NEGATIVE \((\w+)\)", product_rating_info).group(1))
                neutral_rating = int(re.search(r"NEUTRAL \((\w+)\)", product_rating_info).group(1))
                try:
                    product_rating = str(
                        round(positive_rating / (positive_rating + neutral_rating + negative_rating) * 100, 2)) + "%"
                except Exception as e:
                    product_rating = "No reviews"
                    logging.info("Not able to obtain reviews in product \"%s\". Error trying to obtain"
                                 " reviews of product. ERROR: %s " % (name_of_product, e))
                # try:
                #     result = re.search(r"([.\d]+ /5) .*", product_rating)
                #     product_rating = result.group(1)
                # except Exception as e:
                #     product_rating = "No reviews"
                #     logging.info("Not able to obtain reviews in product \"%s\". Error trying to obtain"
                #                  " reviews of product. ERROR: %s " % (name_of_product, e))

                # Info about the seller
                m = 0
                seller_line = "null"
                while m < len(more_information_by_lines):
                    if "Vendor" in more_information_by_lines[m]:
                        seller_line = more_information_by_lines[m]
                        break
                    m += 1

                try:
                    result = re.search(r"Vendor: (\w+) (.*)", seller_line)
                    seller = result.group(1)
                except Exception as e:
                    seller = "null"
                    logging.info("Not able to obtain seller of product \"%s\". Error trying to obtain"
                                 " seller of product. ERROR: %s " % (name_of_product, e))

                if seller in sellers:
                    info_about_seller = obtain_seller_info(seller, conn)

                    seller_profile = info_about_seller[0]
                    seller_pgp = info_about_seller[1]
                    seller_rating = info_about_seller[2]
                    seller_number_ratings = info_about_seller[3]
                    seller_number_of_sales = info_about_seller[4]

                else:  # Obtain all seller info
                    url_seller = driver.find_element_by_class_name("vendor_rating").get_property("href")

                    time.sleep(1)
                    driver.get(url_seller)

                    seller_rating_all_info = driver.find_element_by_class_name(
                        "col-xs-12.vendor-box.container-box").text.splitlines()
                    try:

                        total_ratings = \
                            driver.find_elements_by_xpath("/html/body/div/div[3]/div/div[2]/div[3]/div/div/div[1]/ul")[
                                0].text

                        positive_ratings = int(re.search(r"POSITIVE \((\w+)\)", total_ratings).group(1))
                        negative_ratings = int(re.search(r"NEGATIVE \((\w+)\)", total_ratings).group(1))
                        neutral_ratings = int(re.search(r"NEUTRAL \((\w+)\)", total_ratings).group(1))
                        try:
                            seller_rating = str(
                                round(positive_ratings / (positive_ratings + neutral_ratings + negative_ratings) * 100,
                                      2)) + "%"
                        except Exception as e:
                            seller_rating = "No reviews"
                            logging.info("Not able to obtain reviews in seller \"%s\". Error trying to obtain"
                                         " reviews of seller. ERROR: %s " % (seller, e))

                        seller_number_ratings = str(int(re.search(r"ALL \((\w+)\)", total_ratings).group(1)))
                    except Exception as e:
                        seller_rating = "null"
                        seller_number_ratings = "null"
                        logging.info("Not able to obtain seller ratings. ERROR: %s " % e)

                    seller_number_of_sales = seller_rating_all_info[5].replace("Completed Orders: ", "")

                    url_seller_description = url_seller + "#vendorDescription"
                    driver.get(url_seller_description)
                    seller_profile = driver.find_element_by_xpath(
                        "/html/body/div/div[3]/div/div[2]/div[3]/div/div/div[2]").text.replace("'", "''")\
                        .replace("\"", "\"\"")

                    url_seller_pgp = url_seller + "#vendorPgp"
                    driver.get(url_seller_pgp)
                    seller_pgp = driver.find_element_by_xpath(
                        "/html/body/div/div[3]/div/div[2]/div[3]/div/div/div[5]/textarea").text

                sql = 'INSERT INTO darkweb_markets (' \
                      'timestamp, ' \
                      'product, ' \
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
                      'seller_pgp, ' \
                      'seller_rating, ' \
                      'seller_number_ratings, ' \
                      'seller_number_of_sales) ' \
                      'VALUES (' \
                      'datetime(\'now\'), "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", ' \
                      '"%s", "%s", "%s", "%s", "%s"); ' \
                      % (product.replace("'", "''").replace("\"", "\"\""),
                         category.replace("'", "''").replace("\"", "\"\""),
                         subcategory.replace("'", "''").replace("\"", "\"\""),
                         name_of_product.replace("'", "''").replace("\"", "\"\""),
                         description.replace("'", "''").replace("\"", "\"\""),
                         quantity.replace("'", "''").replace("\"", "\"\""),
                         price,
                         views_of_product.replace("'", "''").replace("\"", "\"\""),
                         shipping_from.replace("'", "''").replace("\"", "\"\""),
                         shipping_to.replace("'", "''").replace("\"", "\"\""),
                         product_rating.replace("'", "''").replace("\"", "\"\""),
                         seller.replace("'", "''").replace("\"", "\"\""),
                         seller_profile.replace("'", "''").replace("\"", "\"\""),
                         seller_pgp.replace("'", "''").replace("\"", "\"\""),
                         seller_rating.replace("'", "''").replace("\"", "\"\""),
                         seller_number_ratings.replace("'", "''").replace("\"", "\"\""),
                         seller_number_of_sales.replace("'", "''").replace("\"", "\"\""))

                execute_sql(conn, sql, logging, name_of_product)
                sellers.append(seller)

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
