from __future__ import print_function
from nordvpn_switcher import initialize_VPN, rotate_VPN, terminate_VPN

import random
import re
import time
import webbrowser
import requests
import whatismyip
import subprocess

try:
    import config
except ImportError:

    class ConfigClass:  # minimal config incase you don't have the config.py
        MAX_DEPTH = 10  # dive no deeper than this for each root URL
        MIN_DEPTH = 3  # dive at least this deep into each root URL
        MAX_WAIT = 10  # maximum amount of time to wait between HTTP requests
        MIN_WAIT = 5  # minimum amount of time allowed between HTTP requests
        DEBUG = True  # set to True to enable useful console output

        # use this single item list to test how a site responds to this crawler
        # be sure to comment out the list below it.
        # ROOT_URLS = ["https://digg.com/"]
        ROOT_URLS = [
            "https://www.hell-brands.com"
        ]

        # items can be a URL "https://t.co" or simple string to check for "amazon"
        blacklist = [
            'facebook.com',
            'pinterest.com'
        ]

        # must use a valid user agent or sites will hate you
        USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) ' \
                     'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'


    config = ConfigClass


class Colors:
    RED = '\033[91m'
    YELLOW = '\033[93m'
    PURPLE = '\033[95m'
    NONE = '\033[0m'


def debug_print(message, color=Colors.NONE):
    """ A method which prints if DEBUG is set """
    if config.DEBUG:
        print(color + message + Colors.NONE)


def hr_bytes(bytes_, suffix='B', si=False):
    """ A method providing a more legible byte format """

    bits = 1024.0 if si else 1000.0

    for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if abs(bytes_) < bits:
            return "{:.1f}{}{}".format(bytes_, unit, suffix)
        bytes_ /= bits
    return "{:.1f}{}{}".format(bytes_, 'Y', suffix)


def do_request(url):
    """ A method which loads a page """

    global good_requests
    global bad_requests

    debug_print("  Requesting page...".format(url))
    debug_print("  With IP {}".format(whatismyip.whatismyip()))

    headers = {'user-agent': config.USER_AGENT}

    try:
        r = requests.get(url, headers=headers, timeout=5)
    except:
        # Prevent 100% CPU loop in a net down situation
        time.sleep(30)
        return False

    status = r.status_code

    if status != 200:
        bad_requests += 1
        debug_print("  Response status: {}".format(r.status_code), Colors.RED)
        if status == 429:
            debug_print(
                "  We're making requests too frequently... sleeping longer...")
            config.MIN_WAIT += 10
            config.MAX_WAIT += 10
    else:
        good_requests += 1
        webbrowser.open_new_tab(url=url)

    return r


def get_links(page):
    """ A method which returns all links from page, less blacklisted links """

    pattern = r"(?:href\=\")(https?:\/\/[^\"]+)(?:\")"
    links = re.findall(pattern, str(page.content))
    valid_links = [link for link in links if not any(
        b in link for b in config.blacklist)]
    for link in valid_links:
        if link.find("hell-brands") == -1:
            valid_links.remove(link)

    return valid_links


def get_blog_links_static():
    """ A method which returns all static blog links"""
    links = ["https://hell-brands.com/beitrag/digital/was-ist-ein-data-warehouse-teil-1/",
             "https://hell-brands.com/beitrag/digital/was-ist-ein-data-warehouse-teil-2/",
             "https://hell-brands.com/beitrag/digital/was-ist-ein-data-warehouse-teil-3/",
             "https://hell-brands.com/beitrag/digital/was-ist-ein-data-warehouse-teil-4/",
             "https://hell-brands.com/beitrag/digital/was-ist-ein-data-warehouse-teil-5/",
             "https://hell-brands.com/beitrag/lifestyle/die-krux-mit-dem-abnehmen-teil-1/",
             "https://hell-brands.com/beitrag/lifestyle/die-krux-mit-dem-abnehmen-teil-2/"
             ]

    return links


def get_main_links_static():
    links = ["https://hell-brands.com/",
             "https://hell-brands.com/landingpage/startseite/",
             "https://hell-brands.com/feurige-beitraege/"
             ]

    return links


def recursive_browse(url, used_depth):
    """ A method which recursively browses URLs, using given depth """
    # Base: load current page and return
    # Recursively: load page, pick random link and browse with decremented depth

    debug_print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    debug_print(
        "Recursively browsing [{}] ~~~ [depth = {}]".format(url, used_depth))

    if not used_depth:  # base case: depth of zero, load page

        do_request(url)
        return

    else:  # recursive case: load page, browse random link, decrement depth

        page = do_request(url)  # load current page

        # give up if error loading page
        if not page:
            debug_print(
                "  Stopping and blacklisting: page error".format(url), Colors.YELLOW)
            # config.blacklist.append(url)
            # return
            while not whatismyip.amionline():
                time.sleep(1)

            debug_print('online again, continue!')

        # scrape page for links not in blacklist
        # debug_print("  Scraping page for links".format(url))
        # valid_links = get_links(page)
        valid_links = get_blog_links_static()
        # debug_print("  Found {} valid links".format(len(valid_links)))

        # give up if no links to browse
        if not valid_links:
            debug_print("  Stopping and blacklisting: no links".format(
                url), Colors.YELLOW)
            config.blacklist.append(url)
            return

        # sleep and then recursively browse
        sleep_time = random.randrange(config.MIN_WAIT, config.MAX_WAIT)
        debug_print("  Pausing for {} seconds...".format(sleep_time))
        time.sleep(sleep_time)

        recursive_browse(random.choice(valid_links), used_depth - 1)


def main_traffic():
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print("Traffic generator started")
    print("Diving between {} and {} links deep into {} root URLs,".format(
        config.MIN_DEPTH, config.MAX_DEPTH, len(config.ROOT_URLS)))
    print("Waiting between {} and {} seconds between requests. ".format(
        config.MIN_WAIT, config.MAX_WAIT))

    links = get_main_links_static()

    for i in range(100):
        for x in range(3):
            if x == 0:
                for link in links:
                    webbrowser.open(link)
                    time.sleep(2)

            debug_print("Randomly selecting one of {} Root URLs".format(
                len(config.ROOT_URLS)), Colors.PURPLE)

            random_url = random.choice(config.ROOT_URLS)
            depth = random.choice(range(config.MIN_DEPTH, config.MAX_DEPTH))

            recursive_browse(random_url, depth)
            rotate_VPN()

        subprocess.Popen(["taskkill", "/IM", 'brave.exe', "/F"], shell=True)

    terminate_VPN()


if __name__ == "__main__":
    # Initialize global variables
    good_requests = 0
    bad_requests = 0

    initialize_VPN(stored_settings=1, area_input=['complete rotation'])

    main_traffic()
