import logging
from shutil import copyfile
import stem.process
import os
import codecs
import stem
import time
import sys
import random

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from datetime import datetime
import sqlite3
from sqlite3 import Error
from selenium.webdriver import ActionChains

# Import of marketplaces logic to obtain info of products
import markets.cannazon as cannazon

logging.basicConfig(format='%(asctime)s %(name)s [%(processName)s] [%(levelname)s] %(message)s',
                    filename='logs/myLog.log', level=logging.INFO)

# Path to Firefox binary
FIREFOX_BINARY = '/usr/bin/firefox'


# Set proxy to connect .onion
def set_proxy(driver, http_port='', http_addr='', ssl_addr='', ssl_port=0, socks_addr='', socks_port=5):
    driver.execute("SET_CONTEXT", {"context": "chrome"})
    try:
        driver.execute_script("""
        Services.prefs.setIntPref('network.proxy.type', 1);
		Services.prefs.setCharPref("network.proxy.http", arguments[0]);
		Services.prefs.setIntPref("network.proxy.http_port", arguments[1]);
		Services.prefs.setCharPref("network.proxy.ssl", arguments[2]);
		Services.prefs.setIntPref("network.proxy.ssl_port", arguments[3]);
		Services.prefs.setCharPref('network.proxy.socks', arguments[4]);
		Services.prefs.setIntPref('network.proxy.socks_port', arguments[5]);
		""", http_addr, http_port, ssl_addr, ssl_port, socks_addr, socks_port)
    finally:
        driver.execute("SET_CONTEXT", {"context": "content"})


# Returns a driver using Firefox
def get_driver(port, useragent):
    # Settings
    webdriver.DesiredCapabilities.FIREFOX[
        "firefox.page.customHeaders.User-Agent"] = useragent
    webdriver.DesiredCapabilities.FIREFOX[
        'firefox.page.customHeaders.Accept'] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    webdriver.DesiredCapabilities.FIREFOX['firefox.page.customHeaders.Accept-Language'] = "en-US,en;q=0.5"
    caps = webdriver.DesiredCapabilities.FIREFOX.copy()

    # Set preferences to access .onion
    firefox_profile = webdriver.FirefoxProfile()
    firefox_profile.set_preference('javascript.enabled', False)  # This preference doesn't work
    firefox_profile.set_preference('network.dns.blockDotOnion', False)
    firefox_profile.set_preference('network.proxy.socks_remote_dns', True)
    firefox_profile.set_preference('dom.ipc.plugins.enabled.libflashplayer.so', 'false')
    firefox_profile.set_preference('dom.webdriver.enabled', False)
    firefox_profile.set_preference('useAutomationExtension', False)

    firefox_profile.set_preference("network.proxy.type", 1)
    firefox_profile.set_preference("network.proxy.http", '127.0.0.1')
    firefox_profile.set_preference("network.proxy.http_port", int(port))
    firefox_profile.update_preferences()

    # Options
    options = Options()
    options.binary = FIREFOX_BINARY
    options.profile = firefox_profile

    caps.update(options.to_capabilities())

    # Obtain driver
    driver = webdriver.Firefox(desired_capabilities=caps, options=options)
    # create action chain object
    action = ActionChains(driver)

    set_proxy(driver, socks_addr='127.0.0.1', socks_port=str(port))

    return driver, action


# Function to launch Tor process
def tor_connection(port, relay, datadir):
    logging.info("Trying to launch Tor process on port: %s" % port)

    if not os.path.exists(datadir):
        os.makedirs(datadir)

    logging.info("Temporal directory created for Tor process")
    try:
        tor_process = stem.process.launch_tor_with_config(
            config={
                "SOCKSPort": str(port),
                "ExitNodes": relay,
                "DataDirectory": datadir,
            },
            timeout=300,
            take_ownership=True,
            completion_percent=80,
        )

        logging.info("Successfully started Tor process (PID = %d)." % tor_process.pid)

    except OSError:
        logging.warning("Couldn't launch Tor on port %s" % port)
        os.rmdir(datadir)
        return None
    return tor_process


# Function to check if TOR connection is enabled
def check_connection():
    logging.info("Checking TOR connection...")
    bash_command = "curl --socks5 localhost:9050 --socks5-hostname localhost:9050 -s " \
                   "https://check.torproject.org/ | grep -m 1 Congratulations | xargs"
    os.system(bash_command)


# Function to obtain a filename based on time and type
def obtain_name_file(folder, type_file, url, extension):
    save_path = os.path.expanduser('~')
    final_path = save_path + '/tfm/crawler/' + folder
    now = datetime.now()
    date_time = now.strftime('%Y_%m_%d__%H_%M_%S')
    file_name = type_file + '_' + url[7:15] + '_' + date_time + '.' + extension
    complete_name = os.path.join(final_path, file_name)
    return complete_name


# Function to save the URL into an HTML
def save_html(driver, url):
    file_name = obtain_name_file("results", "index", url, "html")

    file_object = codecs.open(file_name, "w", "utf-8")
    html = driver.page_source
    file_object.write(html)


# Function to process URL where obtains the info of products
def process_url(driver, url, conn, products_file):
    # Get page
    driver.get(url)

    # Obtain URLs
    if not os.path.isfile(products_file):
        if "cannazo73ou34ev3vnvuq75wb2ienpcztqudkdozpuitvykqhvtiffyd" in url:
            cannazon.obtain_all_products_urls(driver, logging, products_file)
        else:
            logging.error("No scraping function prepared for this market. Sorry!")
            exit()

        # Create copy of file with all products
        src = os.path.abspath(products_file)
        dst = src.replace("products_cannazon", "products_cannazon_20211125")
        copyfile(src, dst)

    # Obtain contents and insert into DB
    if "cannazo73ou34ev3vnvuq75wb2ienpcztqudkdozpuitvykqhvtiffyd" in url:
        cannazon.obtain_info_product(driver, url, conn, logging, products_file)
    else:
        logging.error("No scraping function prepared for this market. Sorry!")
        exit()

    # Remove file if is empty
    if os.path.getsize(products_file) == 0:
        os.remove(products_file)


# Obtain relay 
def obtain_relay():
    possible_relay = ['702fd318aeed49702b5c16255ed5f595da116516', '2bd1936e0b4d5bb615cf99b0cff74eaf19426888',
                      '9493135bc3ec01a29707eaca058fcebd619f3bb1', 'c0aeaba1b55519fe5384aa44d0312be98216da71',
                      '0b1120660999ad1022d08664be1ad08a77f55e50', '62f4994c6f3a5b3e590aeece522591696c8ddee2',
                      '18eae30a4585beb0d63d36bcfe3f9ca786cb55c7', 'f4c836a27bf192f3364a67166e8ee2b19693aed1',
                      '7f0cf3d96c1c910020149eea5a10294117dc67aa', '0fbb3c61ab6d93e10abde69eb8ccc60518a8bf3a']
    relay = possible_relay[random.randint(0, 9)]
    return relay


# Execute and commit SQL queries to save on database
def execute_sql(conn, sql):
    if conn is not None:
        c = conn.cursor()
        c.execute(sql)
        conn.commit()
    else:
        logging.error("ERROR! Cannot connect to the database")


# Function to create/connect to the database
def create_database(market):
    file_name = "/home/victor/paper/darkweb_crawler/database/" + market + ".db"

    logging.info("Trying to create SQLLite DB: %s" % file_name)
    conn = None
    try:
        conn = sqlite3.connect(file_name)
        return conn
    except Error as e:
        print(e)

    return conn


# main
def main():
    logging.info("*** Starting crawler ***")
    products_file = "null"
    database = "null"
    port = 0
    if len(sys.argv) == 4:
        database = sys.argv[1]
        port = str(sys.argv[2])
        products_file = sys.argv[3]
    else:
        print("Wrong number of parameters. Need 2: database, port, products_file")
        exit()

    relay = obtain_relay()
    useragent_array = ['Mozilla/6.0 (Macintosh; Intel Mac OS X 10.11; rv:59.0) Gecko/20100101 Firefox/59.0',
                       'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.3',
                       'Mozilla/5.0 (Macintosh; Intel Mac OS X x.y; rv:42.0) Gecko/20100101 Firefox/43.4',
                       'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 '
                       'Safari/537.36']
    useragent = useragent_array[random.randint(0, 3)]
    logging.info(" Relay:" + relay + " UA:" + useragent)

    # Config
    dir_name = '/tmp/torDataDir'
    data_dir = dir_name + str(port)

    url = 'http://cannazo73ou34ev3vnvuq75wb2ienpcztqudkdozpuitvykqhvtiffyd.onion'  # Cannazon

    # Check if TOR connection is possible
    # check_connection()

    # Run TOR
    logging.info("Trying to launch Tor on port %s using data dir:%s" % (port, data_dir))

    while not tor_connection(port, relay, data_dir):
        port = port + 1
        data_dir = dir_name + str(port)
        logging.info("Trying to launch Tor on port %s using data dir:%s" % (port, data_dir))

    # Create database to save data
    conn = create_database(database)
    logging.info("Connecting database...")
    sql = "CREATE TABLE IF NOT EXISTS darkweb_markets (" \
          " timestamp text NOT NULL," \
          " product text NOT NULL," \
          " category text NOT NULL," \
          " subcategory text NOT NULL," \
          " name_of_product text NOT NULL," \
          " description text NOT NULL," \
          " quantity text," \
          " price float NOT NULL," \
          " views_of_product text," \
          " shipping_from text," \
          " shipping_to text," \
          " product_rating text," \
          " seller text," \
          " seller_profile text," \
          " seller_pgp text," \
          " seller_rating text," \
          " seller_number_ratings text," \
          " seller_number_of_sales text); "
    execute_sql(conn, sql)

    # Driver connection
    driver, action = get_driver(port, useragent)

    # Fixing settings of javascript disabled due to bug of Selenium
    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[1])
    driver.get("about:config")
    continue_button = driver.find_elements_by_xpath('//*[@id="warningButton"]')[0]
    continue_button.click()
    input_element = driver.find_element_by_id("about-config-search")
    input_element.send_keys('javascript.enabled')
    time.sleep(1)
    boolean_button = driver.find_elements_by_xpath('/html/body/table/tr/td[2]/button')[0]
    boolean_button.click()
    driver.close()
    driver.switch_to.window(driver.window_handles[0])

    logging.info("Driver obtained!")

    # Download html
    save_html(driver, url)

    # Process data
    process_url(driver, url, conn, products_file)
    logging.info("URL processed!")

    conn.close()
    driver.close()

    logging.info("END!\n")


main()
