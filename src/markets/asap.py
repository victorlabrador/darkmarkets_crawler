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
    url = "http://asap2u4pvplnkzl7ecle45wajojnftja45wvovl3jrvhangeyq67ziid.onion/search?page=350&currency=EUR&sortType=Alphabetical"
    driver.get(url)

    page_number = 350
    more_pages = True
    while more_pages:
        # Obtain links for this page
        links_this_page = driver.find_elements_by_class_name("clr-col-lg-4.clr-col-md-6.card-search-listing")

        if len(links_this_page) == 0:  # There is nothing in this page, no more pages
            break
        for link in links_this_page:
            url_to_write = link.find_elements_by_tag_name("a")[0].get_property("href")
            if "listing" in url_to_write:  # to get links that are a product
                logging.info("This link is a product: %s " % link.text.split('\n')[0])
                products_file.write("%s\n" % url_to_write)

        # Check if there are more pages
        page_number += 1
        try:
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
        errors = 0

        while lines:
            product = lines[0].replace("\n", "")

            # Access this product
            driver.get(product)


            try:
                try:
                    all_content_by_lines = driver.find_element_by_class_name("table.table-vertical.table-noborder.table-compact.table-no-margin").text.splitlines()
                except Exception as e:
                    javascript = driver.find_element_by_class_name("alert-text.text-center").text
                    if "JavaScript" in javascript:
                        logging.warn("Error loading webpage... Trying again")
                        driver.get(product)
                        all_content_by_lines = driver.find_element_by_class_name(
                            "table.table-vertical.table-noborder.table-compact.table-no-margin").text.splitlines()
                    else:
                        logging.warn("This product doesn't exist anymore: %s. Warning: %s" % (product, e))
                        logging.info("Deleting this line of the file of products...")
                        del lines[0]
                        writable_file = open(products_file, "w+")
                        for line in lines:
                            writable_file.write(line)
                        writable_file.close()

                        # Read again the file
                        readable_file = open(products_file, "r")
                        lines = readable_file.readlines()
                        readable_file.close()
                        logging.info("Line of non existing product deleted!")
                        continue

                name_of_product = driver.find_element_by_class_name("breadcrumbs").text

                # Searching category
                i = 0
                categories = "null"
                while i < len(all_content_by_lines):
                    if "Category" in all_content_by_lines[i]:
                        categories = all_content_by_lines[i+1]
                        break
                    i += 1

                try:
                    result = re.search(r"(\w+)( > (.*))?", categories)
                    category = result.group(1)
                    subcategory = result.group(3)
                    if "None" in subcategory:
                        subcategory = "null"
                except Exception as e:
                    category = categories
                    subcategory = "null"
                    logging.info("No info related to categories in product \"%s\". Error trying to obtain"
                                 " subcategory of product. ERROR: %s " % (name_of_product, e))

                description = driver.find_element_by_class_name("white-space-formatted").text

                try:
                    result = re.search("([0-9]+[.|,]?[0-9]?[ ]?(mg|MG|gr|ml|GR|ug|UG|Gr|g|G|GRAM|gram))", name_of_product)
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
                    if "Price" in all_content_by_lines[j]:
                        price_usd = float(
                            re.search(r"([\d|,.]+)", all_content_by_lines[j + 1].replace(",", "")).group(1))
                        price = str(round(price_usd * 0.85, 2)) + " €"
                        break
                    j += 1

                views_of_product = "null"  # This market doesn't have info related to views of each product

                # Searching where shipping from
                k = 0
                shipping_from = "null"
                while k < len(all_content_by_lines):
                    if "Ships from:" in all_content_by_lines[k]:
                        shipping_from = all_content_by_lines[k+1]
                        break
                    k += 1

                # Searching where shipping to
                n = 0
                shipping_to = "null"
                while n < len(all_content_by_lines):
                    if "Ships to:" in all_content_by_lines[n]:
                        shipping_to = all_content_by_lines[n+1]
                        break
                    n += 1

                m = 0
                total = 0
                positive = 0
                total_bool = False
                positive_bool = False
                while m < len(all_content_by_lines):
                    if "Total" in all_content_by_lines[m] and not total_bool:
                        total = float(all_content_by_lines[m + 1])
                        total_bool = True
                    elif "Positive" in all_content_by_lines[m] and not positive_bool:
                        positive = float(all_content_by_lines[m + 1])
                        positive_bool = True
                    m += 1

                if total == 0:
                    product_rating = "No reviews"
                else:
                    try:
                        product_rating = str(round(positive / total) * 100, 2) + "%"
                    except Exception as e:
                        product_rating = "No reviews"
                        logging.info("Not able to obtain reviews in product \"%s\". Error trying to obtain"
                                     " reviews of product. ERROR: %s " % (name_of_product, e))

                o = 0
                seller = "null"
                while o < len(all_content_by_lines):
                    if "Vendor:" in all_content_by_lines[o]:
                        seller = re.search(r"(\w+) \(\d+\)", all_content_by_lines[o+1]).group(1)
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
                    url_seller = driver.find_element_by_class_name("btn.btn-sm.btn-link.btn-no-margin.custom-link-action").get_property("href")
                    driver.get(url_seller)

                    seller_rating_info = driver.find_elements_by_class_name("badge")
                    seller_number_ratings = seller_rating_info[0].text
                    seller_positive_ratings = float(seller_rating_info[1].text)

                    try:
                        seller_rating = str(round((seller_positive_ratings / float(seller_number_ratings) * 100), 2)) + "%"
                    except Exception as e:
                        seller_rating = "No reviews"
                        logging.info("Not able to obtain reviews in product \"%s\". Error trying to obtain"
                                     " reviews of product. ERROR: %s " % (name_of_product, e))

                    seller_number_of_sales_info = driver.find_element_by_xpath(
                        "/html/body/div/div[2]/div/div[2]/table/tbody/tr/td/table/tbody/tr[1]/td").text

                    seller_number_of_sales = re.search("\w+ \((\d+)\)", seller_number_of_sales_info).group(1)

                    seller_profile = driver.find_element_by_class_name("white-space-formatted").text


                    url_seller_pgp = url_seller + "?tab=PGP"
                    driver.get(url_seller_pgp)
                    try:
                        seller_fingerprint = driver.find_element_by_class_name("clr-textarea.pgp-key-text").text
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
                    print("ERROR #%s... Sleeping 10 sec" % errors)
                    errors += 1
                    time.sleep(10)
                else:
                    errors = 0
                    input("ERROR %s. RELOAD then press ENTER" % errors)

    except Exception as e:
        logging.error("ERROR retrieving some product: %s " % e)
