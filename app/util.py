"""
When we don`t know where to place a feature, this is mamas house
"""
from .time_util import sleep
from selenium.common.exceptions import NoSuchElementException
import sqlite3


DATABASE_LOCATION = './db/instapy-light.db'


def validate_username(browser,
                      username,
                      blacklist,
                      like_by_followers_upper_limit,
                      like_by_followers_lower_limit):
    """
    Check if we can interact with the user

    Args:
        :browser: web driver
        :username: our username
        :blacklist: blacklist setup
        :like_by_followers_upper_limit: <-
        :like_by_followers_lower_limit: <-

    .. note:: are we using it ?
    """

    if username in blacklist:
        return '---> {} is in blacklist, skipping user...'

    browser.get('https://www.instagram.com/{}'.format(username))
    sleep(1)
    try:
        followers = (formatNumber(browser.find_element_by_xpath("//a[contains"
                     "(@href,'followers')]/span").text))
    except NoSuchElementException:
        return '---> {} account is private, skipping user...'.format(username)

    if like_by_followers_upper_limit != 0 or like_by_followers_lower_limit != 0:
        if followers > like_by_followers_upper_limit:
            return '---> User {} exceeds followers limit'.format(username)
        elif followers < like_by_followers_lower_limit:
            return ('---> {}, number of followers does not reach '
                    'minimum'.format(username))

    # if everything ok
    return True


def update_activity(action=None):
    """
    Record every Instagram server call (page load, content load, likes,
    comments, follows, unfollow).

    .. note:: we need to reorganize this idea
    """
    conn = sqlite3.connect(DATABASE_LOCATION)
    with conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        # collect today data
        cur.execute("SELECT * FROM statistics WHERE created == date('now')")
        data = cur.fetchone()

        if data is None:
            # create a new record for the new day
            cur.execute("INSERT INTO statistics VALUES "
                        "(0, 0, 0, 0, 1, date('now'))")
        else:
            # sqlite3.Row' object does not support item assignment -> so,
            # convert it into a new dict
            data = dict(data)
            # update
            data['server_calls'] += 1

            if action == 'likes':
                data['likes'] += 1
            elif action == 'comments':
                data['comments'] += 1
            elif action == 'follows':
                data['follows'] += 1
            elif action == 'unfollows':
                data['unfollows'] += 1

            sql = ("UPDATE statistics set likes = ?, comments = ?, "
                   "follows = ?, unfollows = ?, server_calls = ? "
                   "WHERE created = date('now')")
            cur.execute(sql, (data['likes'], data['comments'], data['follows'],
                              data['unfollows'], data['server_calls']))
        # commit
        conn.commit()


def get_active_users(browser, username, posts, logger):
    """
    Returns a list with users who liked the latest posts

    Args:
        :browser: web driver
        :username: our username
        :posts: amount of posts to be verified
        :logger: library to log actions
    Returns:
        Active Users based on filter above
    """

    browser.get('https://www.instagram.com/' + username)
    sleep(2)

    total_posts = formatNumber(browser.find_element_by_xpath(
        "//span[contains(@class,'_t98z6')]//span").text)

    # if posts > total user posts, assume total posts
    if posts >= total_posts:
        # reaches all user posts
        posts = total_posts

    # click latest post
    browser.find_element_by_xpath(
        "(//div[contains(@class, '_si7dy')])[1]").click()

    active_users = []

    # posts argument is the number of posts to collect usernames
    for count in range(1, posts):
        try:
            browser.find_element_by_xpath(
                "//a[contains(@class, '_nzn1h')]").click()
            sleep(1)
            tmp_list = browser.find_elements_by_xpath(
                "//a[contains(@class, '_2g7d5')]")
        except NoSuchElementException:
            try:
                tmp_list = browser.find_elements_by_xpath(
                    "//div[contains(@class, '_3gwk6')]/a")
            except NoSuchElementException:
                logger.exception('message')

        if len(tmp_list) is not 0:
            for user in tmp_list:
                active_users.append(user.text)

        sleep(1)
        # if not reached posts(parameter) value, continue
        if count+1 != posts:
            try:
                # click next button
                browser.find_element_by_xpath(
                    "//a[@class='_3a693 coreSpriteRightPaginationArrow']"
                    "[text()='Next']").click()
            except Exception:
                logger.exception('message')

    # delete duplicated users
    active_users = list(set(active_users))

    return active_users


def scroll_bottom(browser, element, range_int):
    """
    Instagram doesn`t load all content once, and we need to scroll the pages
    down to load more content

    Args:
        :browser: web driver
        :element: web page element to be scrolled
        :rand_int: calculates the scrolling limit
    Returns:
        wtf?

    .. todo:: why are we returning nothing here ?
    """
    # put a limit to the scrolling
    if range_int > 50:
        range_int = 50

    for i in range(int(range_int / 2)):
        browser.execute_script(
            "arguments[0].scrollTop = arguments[0].scrollHeight", element)
        # update server calls
        update_activity()
        sleep(1)

    return


def formatNumber(number):
    """
    Receive an unformated number an return a formated number
    """
    formattedNum = number.replace(',', '').replace('.', '')
    formattedNum = int(formattedNum.replace('k', '00').replace('m', '00000'))
    return formattedNum


def is_account_active(browser, profile):
    """
    Check if it`s an active Instagram Account

    Args:
        :browser: web driver
        :profile: profile name to be checked
    Returns:
        True for active profiles / False for invalid profiles
    """
    browser.get('https://www.instagram.com/{}'.format(profile))
    browser.implicitly_wait(3)
    try:
        browser.find_element_by_xpath('//h2/self::h2')
    except Exception:
        browser.implicitly_wait(0)
        # is active
        return True
    # is desactive
    browser.implicitly_wait(0)
    return False


def register_account(username):
    conn = sqlite3.connect(DATABASE_LOCATION)
    with conn:
        cur = conn.cursor()
        # INSERT OR REPLACE
        sql = (
            "INSERT OR IGNORE INTO accounts (username, modified, created) "
            "VALUES (?, date('now'), date('now'))")
        cur.execute(sql, (username, ))
        conn.commit()


def get_account_id(username):
    """
    Return the related account id

    Args:
        :username: username to be consulted
    """
    conn = sqlite3.connect(DATABASE_LOCATION)
    with conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        sql = "SELECT id FROM accounts WHERE username = ?"
        cur.execute(sql, (username,))
        data = cur.fetchone()
        if data is not None:
            return data['id']
