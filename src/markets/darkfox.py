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
    url = "http://57d5j6hfzfpsfev6c7f5ltney5xahudevvttfmw4lrtkt42iqdrkxmqd.onion/results?exclude_on_vacation=no" \
          "&orderby=timeasc "
    actual_url = url + '&page=769'
    driver.get(actual_url)

    page_number = 769
    more_pages = True
    while more_pages:
        # Obtain links for this page
        links_this_page = driver.find_elements_by_xpath("/html/body/main/div/div[2]/div/div[2]/div/div[*]/article["
                                                        "*]/div/div[1]/figure/a")
        if len(links_this_page) == 0:  # There is nothing in this page, no more pages
            break
        for link in links_this_page:
            url_to_write = link.get_property("href")
            if "product" in url_to_write:  # to get links that are a product
                logging.info("This link is a product: %s " % url_to_write)
                products_file.write("%s\n" % url_to_write)

        # Check if there are more pages
        page_number += 1
        try:
            actual_url = url + "&page=" + str(page_number)
            time.sleep(4)
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
        errors = 0

        while lines:
            product = lines[0].replace("\n", "")

            # Access this product
            time.sleep(5)
            driver.get(product)

            try:
                all_content_by_lines = driver.find_element_by_class_name("content").text.splitlines()

                name_of_product = driver.find_elements_by_xpath("/html/body/main/div/div[2]/div/div[2]/div/div["
                                                                "2]/div[1]/h1")[0].text

                # Searching category
                categories_driver = driver.find_elements_by_xpath("/html/body/main/div/div[1]/nav/ul/li[*]/a")
                category = categories_driver[1].text
                try:
                    subcategory = categories_driver[2].text
                except Exception as e:
                    subcategory = "null"
                    logging.info("No info related to subcategory in product \"%s\". Error trying to obtain"
                                 " subcategory of product. ERROR: %s " % (name_of_product, e))

                description = driver.find_element_by_class_name("pre-line").text

                try:
                    result = re.search("([0-9]+[.|,]?[0-9]?[ ]?(mg|MG|gr|GR|ug|UG|Gr|g|G|GRAM|gram))", name_of_product)
                    quantity = result.group(1)
                except Exception as e:
                    if category == "Drugs":
                        quantity = "1 gr"
                    else:
                        quantity = "1"
                    logging.info("No info related to quantity in product \"%s\". Error trying to obtain"
                                 " quantity of product. ERROR: %s " % (name_of_product, e))

                # Searching the prices
                j = 0
                price = "null"
                while j < len(all_content_by_lines):
                    if "Pricing details" in all_content_by_lines[j]:
                        price_usd = float(
                            re.search(r"(.*) - ([\d|,.]+)", all_content_by_lines[j + 2].replace(",", "")).group(2))
                        price = str(round(price_usd * 0.84, 2)) + " €"
                        break
                    j += 1

                views_of_product = "null"  # This market doesn't have info related to views of each product

                # Searching where shipping from
                k = 0
                shipping_from = "null"
                while k < len(all_content_by_lines):
                    if "Ships from" in all_content_by_lines[k]:
                        shipping_from = all_content_by_lines[k].replace("Ships from: ", "")
                        break
                    k += 1
                if k == len(all_content_by_lines):
                    logging.info("No info related to shipping from")
                    shipping_from = "null"

                # Searching where shipping to
                n = 0
                shipping_to = "null"
                while n < len(all_content_by_lines):
                    if "Ships to" in all_content_by_lines[n]:
                        shipping_to = all_content_by_lines[n].replace("Ships to: ", "")
                        break
                    n += 1
                if shipping_to == "certain countries":  # Searching all countries
                    n += 1
                    shipping_to = ""
                    while n < len(all_content_by_lines):
                        shipping_to += all_content_by_lines[n] + ", "
                        n += 1

                m = 0
                communication = 0
                shipping = 0
                quality = 0
                value_for_price = 0
                while m < len(all_content_by_lines):
                    if "Communication:" in all_content_by_lines[m]:
                        communication = float(all_content_by_lines[m + 1])
                    elif "Shipping:" in all_content_by_lines[m]:
                        shipping = float(all_content_by_lines[m + 1])
                    elif "Quality:" in all_content_by_lines[m]:
                        quality = float(all_content_by_lines[m + 1])
                    elif "Value for price:" in all_content_by_lines[m]:
                        value_for_price = float(all_content_by_lines[m + 1])
                    m += 1

                try:
                    product_rating = str(round((communication + shipping + quality + value_for_price) / 4) * 20) + "%"
                except Exception as e:
                    product_rating = "No reviews"
                    logging.info("Not able to obtain reviews in product \"%s\". Error trying to obtain"
                                 " reviews of product. ERROR: %s " % (name_of_product, e))

                o = 0
                seller = "null"
                while o < len(all_content_by_lines):
                    if "Vendor" in all_content_by_lines[o]:
                        seller = re.search(r"Vendor: (\w+) .*", all_content_by_lines[o]).group(1)
                        break
                    o += 1

                if seller in sellers:
                    info_about_seller = obtain_seller_info(seller, conn)

                    seller_profile = info_about_seller[0]
                    seller_fingerprint = info_about_seller[1]
                    seller_rating = info_about_seller[2]
                    seller_number_ratings = info_about_seller[3]
                    seller_number_of_sales = info_about_seller[4]

                else:  # Obtain all seller info
                    url_seller = url + "/user/" + seller
                    time.sleep(3)
                    driver.get(url_seller)
                    time.sleep(2)

                    seller_rating_info = float(driver.find_element_by_xpath(
                        "/html/body/main/div/div/div/div/div/div[1]/div/div[2]/div[2]/p[6]/font/span[6]").text)
                    seller_rating = str(seller_rating_info * 20) + "%"
                    seller_number_ratings = "null"  # This market doesn't have info related to number of ratings

                    seller_number_of_sales = driver.find_element_by_xpath(
                        "/html/body/main/div/div/div/div/div/div[1]/div/div[2]/div[2]/p[4]/font").text

                    url_seller_description = url_seller + "/about"
                    time.sleep(3)
                    driver.get(url_seller_description)
                    time.sleep(2)
                    try:
                        seller_profile = driver.find_element_by_class_name("pre-line").text
                    except Exception as e:
                        seller_profile = "no profile"
                        logging.info("Not able to obtain profile of seller \"%s\". Error trying to obtain"
                                     " seller profile from product %s. ERROR: %s " % (seller, name_of_product, e))

                    url_seller_pgp = url_seller + "/pgp"
                    time.sleep(3)
                    driver.get(url_seller_pgp)
                    time.sleep(2)
                    try:
                        seller_fingerprint = driver.find_element_by_class_name("textarea").text
                    except Exception as e:
                        seller_fingerprint = "no pgp"
                        logging.info("Not able to obtain PGP of seller \"%s\". Error trying to obtain"
                                     " seller PGP from product %s. ERROR: %s " % (seller, name_of_product, e))

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
                      % (market.replace("'", "''").replace("\"", "\"\""),
                         category.replace("'", "''").replace("\"", "\"\""),
                         subcategory.replace("'", "''").replace("\"", "\"\""),
                         name_of_product.replace("'", "''").replace("\"", "\"\""),
                         description.replace("'", "''").replace("\"", "\"\""),
                         quantity.replace("'", "''").replace("\"", "\"\""),
                         price.replace("'", "''").replace("\"", "\"\""),
                         views_of_product.replace("'", "''").replace("\"", "\"\""),
                         shipping_from.replace("'", "''").replace("\"", "\"\""),
                         shipping_to.replace("'", "''").replace("\"", "\"\""),
                         product_rating.replace("'", "''").replace("\"", "\"\""),
                         seller.replace("'", "''").replace("\"", "\"\""),
                         seller_profile.replace("'", "''").replace("\"", "\"\""),
                         seller_fingerprint.replace("'", "''").replace("\"", "\"\""),
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

                errors = 0

            except Exception as e:
                logging.error("Stopped by timeout. Resolve CAPTCHA and continue. ERROR: %s " % e)
                if errors < 5:
                    print("ERROR #%s... Sleeping 15 sec" % errors)
                    errors += 1
                    time.sleep(15)
                else:
                    errors = 0
                    input("ERROR %s. RELOAD then press ENTER" % errors)

    except Exception as e:
        logging.error("ERROR retrieving some product: %s " % e)
