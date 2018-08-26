"""Module which handles the follow features like unfollowing and following"""
from .time_util import sleep
from .util import scroll_bottom
from .util import formatNumber
from .util import update_activity
from .blacklist import add_user_to_blacklist
from .blacklist import mark_as_unfollowed_by_blacklist_campaign
from .print_log_writer import log_followed_pool
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import random


def unfollow(browser,
             username,
             amount,
             dont_touch,
             logger):
    """
    Unfollows the given amount of users

    Args:
        :browser: web driver
        :username: our username
        :amount: amount of profiles to unfollow
        :dont_touch: profiles to not unfollow
        :logger: library to log actions
    Returns:
        Amount of unfollowed profiles
    """
    unfollowNum = 0

    browser.get('https://www.instagram.com/' + username)

    # update server calls
    update_activity()

    #  check how many poeple we are following
    #  throw RuntimeWarning if we are 0 people following
    try:
        allfollowing = formatNumber(
            browser.find_element_by_xpath('//li[3]/a/span').text)
    except NoSuchElementException:
        logger.warning('There are 0 people to unfollow')

    # unfollow from profile
    try:
        following_link = browser.find_elements_by_xpath(
            '//section//ul//li[3]')
        following_link[0].click()
        # update server calls
        update_activity()
    except BaseException:
        logger.exception('message')

    sleep(2)

    # find dialog box
    dialog = browser.find_element_by_xpath(
        "//div[text()='Followers' or text()='Following']"
        "/../../following-sibling::div")

    # scroll down the page
    scroll_bottom(browser, dialog, allfollowing)

    # get persons, unfollow buttons, and length of followed pool
    person_list_a = dialog.find_elements_by_tag_name("a")
    person_list = []

    for person in person_list_a:
        if person and hasattr(person, 'text') and person.text:
            person_list.append(person.text)

    follow_buttons = dialog.find_elements_by_tag_name('button')

    # unfollow loop
    try:
        hasSlept = False
        import ipdb
        ipdb.set_trace()
        for button, person in zip(follow_buttons, person_list):
            if unfollowNum >= amount:
                logger.info(
                    "--> Total unfollowNum reached it's amount given: {}"
                    .format(unfollowNum))
                break

            sleep_delay = random.randint(60, 440)
            if unfollowNum != 0 and \
               hasSlept is False and \
               unfollowNum % 10 == 0:
                    logger.info('sleeping for about {}min'
                                .format(int(sleep_delay/60)))
                    sleep(sleep_delay)
                    hasSlept = True
                    continue

            if person not in dont_touch:
                unfollowNum += 1
                button.click()
                try:
                    sleep(random.randint(1, 5))
                    unfollow_confirm_button = (
                        browser.find_element_by_xpath(
                            "//*[contains(@class, '-Cab_')]"))
                    unfollow_confirm_button.click()
                except Exception:
                    pass
                update_activity('unfollows')

                logger.info(
                    '--> Ongoing Unfollow {}, now unfollowing: {}'
                    .format(str(unfollowNum), person.encode('utf-8')))
                sleep(15)
                # To only sleep once until there is the next unfollow
                if hasSlept:
                    hasSlept = False

                continue
            else:
                continue

    except BaseException:
        logger.exception('message')

    return unfollowNum


def follow_user(account_id,
                browser,
                follow_restrict,
                login,
                user_name,
                blacklist,
                logger):
    """
    Follows the user of the currently open image

    Args:
        :account_id: Instagram Account Id
        :browser: web driver
        :follow_restrict: ?
        :login: ?
        :user_name: ?
        :blacklist: blacklist setup
        :logger: library to log actions
    """

    try:
        follow_button = browser.find_element_by_xpath(
                "//div[text()='Following']/../../following-sibling::div")

        # Do we still need this sleep?
        sleep(2)

        if follow_button.is_displayed():
            follow_button.click()
            update_activity('follows')
        else:
            browser.execute_script(
                "arguments[0].style.visibility = 'visible'; "
                "arguments[0].style.height = '10px'; "
                "arguments[0].style.width = '10px'; "
                "arguments[0].style.opacity = 1", follow_button)
            follow_button.click()
            update_activity('follows')

        logger.info('--> Now following')
        log_followed_pool(login, user_name, logger)
        follow_restrict[user_name] = follow_restrict.get(user_name, 0) + 1
        if blacklist['enabled'] is True:
            action = 'follow'
            add_user_to_blacklist(account_id,
                                  browser,
                                  user_name,
                                  blacklist,
                                  action,
                                  logger)
        sleep(3)
        return 1
    except NoSuchElementException:
        logger.info('--> Already following')
        sleep(1)
        return 0


def unfollow_profile_from_campaign(count,
                                   browser,
                                   logger,
                                   campaign,
                                   profile):
    """
    Unfollow profile from a blacklist campaign and mark is as unfollowed from
    the blacklist campaign

    Args:
        :count: current unfollow index
        :browser: web driver
        :logger: library to log actions
        :campaign: blacklist campaign name
        :profile: profile to unfollow

    """
    browser.get('https://www.instagram.com/{}'.format(profile))
    sleep(3)
    try:
        unfollow_button = WebDriverWait(browser, 3).until(
            EC.presence_of_element_located((By.XPATH,
                                            "//button[text()='Following']"))
        )
        unfollow_button.click()
        logger.info('#{} profile "{}" unfollowed from "{}" campaign'
                    .format(count, profile, campaign))
        update_activity('unfollows')
        mark_as_unfollowed_by_blacklist_campaign(profile, campaign, logger)
    except Exception:
        try:
            unfollow_button = WebDriverWait(browser, 3).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//button[text()='Requested']"))
            )
            unfollow_button.click()
            logger.info('#{} profile "{}" unfollowed from "{}" campaign'
                        .format(count, profile, campaign))
            update_activity('unfollows')
            mark_as_unfollowed_by_blacklist_campaign(profile, campaign, logger)
        except Exception:
            try:
                unfollow_button = WebDriverWait(browser, 3).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//button[text()='Follow']"))
                )
                logger.info('#{} profile "{}" already unfollowed by "{}"'
                            'campaign'.format(count, profile, campaign))
                update_activity('unfollows')
                mark_as_unfollowed_by_blacklist_campaign(profile,
                                                         campaign,
                                                         logger)
            except Exception:
                mark_as_unfollowed_by_blacklist_campaign(profile,
                                                         campaign,
                                                         logger)
                logger.warning('Unable to unfollow profile "{}", non existing '
                               'account ?'.format(profile))


def unfollow_user(browser, logger):
    """
    Unfollows the user of the currently open image

    Args:
        :browser: web driver
        :logger: library to log actions
    Returns:
        True / False
    """

    unfollow_button = browser.find_element_by_xpath(
        "//*[contains(text(), 'Following')]")

    if unfollow_button.text == 'Following':
        unfollow_button.click()
        update_activity('unfollows')
        logger.warning('--> User unfollowed due to Inappropriate Content')
        sleep(3)
        return True
    else:
        return False


def follow_given_user(account_id,
                      browser,
                      acc_to_follow,
                      follow_restrict,
                      blacklist,
                      logger):
    """
    Follows a given user

    Args:
        :account_id: Instagram Account ID
        :browser: web driver
        :acc_to_follow: account to follow
        :follow_restrict: ?
        :blacklist: blacklist setup
        :logger: library to log actions
    Returns:
        True / False
    """
    browser.get('https://www.instagram.com/' + acc_to_follow)
    # update server calls
    update_activity()
    logger.info('--> {} instagram account is opened...'.format(acc_to_follow))

    try:
        sleep(10)
        follow_button = browser.find_element_by_xpath("//*[text()='Follow']")
        follow_button.click()
        update_activity('follows')
        logger.info('---> Now following: {}'.format(acc_to_follow))
        follow_restrict[acc_to_follow] = follow_restrict.get(
            acc_to_follow, 0) + 1

        if blacklist['enabled'] is True:
            action = 'follow'
            add_user_to_blacklist(
                account_id,
                browser,
                acc_to_follow,
                blacklist,
                action,
                logger
            )

        sleep(3)
        return True
    except NoSuchElementException:
        logger.warning('---> {} is already followed'.format(acc_to_follow))
        sleep(3)
        return False


def follow_through_dialog(account_id,
                          browser,
                          profile,
                          amount,
                          dont_touch,
                          username,
                          follow_restrict,
                          allfollowing,
                          randomize,
                          blacklist,
                          logger,
                          callbacks=[]):
    """
    Follow profiles from dialog

    Args:
        :account_id: Instagram Account ID
        :browser: web driver
        :amount: amount of profiles to be followed
        :dont_touch: profiles to not follow
        :username: our username
        :follow_restrict: ?
        :all_following: ?
        :randomize: follow profiles randomly
        :blacklist: blacklist setup
        :logger: library to log actions
        :callbacks: ?
    Returns:
        All followed profiles
    """
    sleep(2)
    person_followed = []
    real_amount = amount
    if randomize and amount >= 3:
        # expanding the popultaion for better sampling distribution
        amount = amount * 3

    # find dialog box
    dialog = browser.find_element_by_xpath(
      "//div[text()='Followers' or text()='Following']/following-sibling::div")

    # scroll down the page
    scroll_bottom(browser, dialog, allfollowing)

    # get follow buttons. This approch will find the follow buttons and
    # ignore the Unfollow/Requested buttons.
    follow_buttons = dialog.find_elements_by_xpath(
        "//div/div/span/button[text()='Follow']")

    person_list = []
    abort = False
    total_list = len(follow_buttons)

    # scroll down if the generated list of user to follow is not enough to
    # follow amount set
    while (total_list < amount) and not abort:
        amount_left = amount - total_list
        before_scroll = total_list
        scroll_bottom(browser, dialog, amount_left)
        sleep(1)
        follow_buttons = dialog.find_elements_by_xpath(
            "//div/div/span/button[text()='Follow']")
        total_list = len(follow_buttons)
        abort = (before_scroll == total_list)

    for person in follow_buttons:

        if person and hasattr(person, 'text') and person.text:
            try:
                person_list.append(person.find_element_by_xpath("../../../*")
                                   .find_elements_by_tag_name("a")[1].text)
            except IndexError:
                pass  # Element list is too short to have a [1] element

    if amount >= total_list:
        amount = total_list
        logger.warning("{} -> Less users to follow than requested."
                       .format(profile))

    # follow loop
    try:
        hasSlept = False
        btnPerson = list(zip(follow_buttons, person_list))

        if randomize:
            sample = random.sample(range(0, len(follow_buttons)), real_amount)
            finalBtnPerson = []
            for num in sample:
                finalBtnPerson.append(btnPerson[num])
        else:
            finalBtnPerson = btnPerson

        followNum = 0

        for button, person in finalBtnPerson:
            if followNum >= real_amount:
                logger.info("--> Total followNum reached: {}"
                            .format(followNum))
                break

            if followNum != 0 and hasSlept is False and followNum % 10 == 0:
                sleep_time = random.randint(60, 480)
                logger.info('sleeping for about {} minutes'
                            .format(sleep_time/60))
                sleep(sleep_time)
                hasSlept = True
                continue

            # skip if user in dont_include list
            if (person in dont_touch or
               person in blacklist['blacklisted_profiles']):
                continue

            followNum += 1
            # Register this session's followed user for further interaction
            person_followed.append(person)

            button.click()
            log_followed_pool(username, person, logger)
            update_activity('follows')

            follow_restrict[profile] = follow_restrict.get(
                profile, 0) + 1

            logger.info('--> #{} followed ({}) from ({}) profile'
                        .format(str(followNum), person, profile))

            if blacklist['enabled'] is True:
                action = 'follow'
                add_user_to_blacklist(account_id,
                                      browser,
                                      person,
                                      blacklist,
                                      action,
                                      logger)

            for callback in callbacks:
                callback(person.encode('utf-8'))
            sleep(15)

            # To only sleep once until there is the next follow
            if hasSlept:
                hasSlept = False
            continue

    except BaseException:
        logger.exception('message')

    return person_followed


def get_given_user_followers(browser,
                             user_name,
                             amount,
                             dont_include,
                             login,
                             follow_restrict,
                             randomize,
                             logger):
    """
    Retrieve a competitors profile followers

    Args:
        :browser: web driver
        :user_name: competitor?
        :amount: amount of profiles to load
        :dont_include: profiles to not follow
        :login: ?
        :follow_restrict: ?
        :randomize: randomize the following process
        :logger: library to log actions

    Returns:
        A list of profiles from the competitors profile
    """
    browser.get('https://www.instagram.com/' + user_name)
    # update server calls
    update_activity()

    # check how many poeple are following this user.
    # throw RuntimeWarning if we are 0 people following this user or
    # if its a private account
    try:
        allfollowing = formatNumber(
            browser.find_element_by_xpath("//li[2]/a/span").text)
    except NoSuchElementException:
        logger.warning('Can\'t interact with private account')
        return

    following_link = browser.find_elements_by_xpath(
        '//a[@href="/' + user_name + '/followers/"]')
    following_link[0].click()
    # update server calls
    update_activity()

    sleep(2)

    # find dialog box
    dialog = browser.find_element_by_xpath(
        "//div[text()='Followers']/following-sibling::div")

    # scroll down the page
    scroll_bottom(browser, dialog, allfollowing)

    # get follow buttons. This approch will find the follow buttons and
    # ignore the Unfollow/Requested buttons.
    follow_buttons = dialog.find_elements_by_xpath(
        "//div/div/span/button[text()='Follow']")
    person_list = []

    if amount >= len(follow_buttons):
        amount = len(follow_buttons)
        logger.warning("{} -> Less users to follow than requested."
                       .format(user_name))

    finalBtnPerson = []
    if randomize:
        sample = random.sample(range(0, len(follow_buttons)), amount)

        for num in sample:
            finalBtnPerson.append(follow_buttons[num])
    else:
        finalBtnPerson = follow_buttons[0:amount]
    for person in finalBtnPerson:

        if person and hasattr(person, 'text') and person.text:
            person_list.append(person.find_element_by_xpath(
                "../../../*").find_elements_by_tag_name("a")[1].text)

    return person_list


def get_given_user_following(browser,
                             user_name,
                             amount,
                             dont_include,
                             login,
                             follow_restrict,
                             randomize,
                             logger):
    """
    Return competitors followings

    .. note::
        is it correct ?
    """
    browser.get('https://www.instagram.com/' + user_name)

    # update server calls
    update_activity()

    #  check how many poeple are following this user.
    #  throw RuntimeWarning if we are 0 people following this user
    try:
        allfollowing = formatNumber(
            browser.find_element_by_xpath("//li[3]/a/span").text)
    except NoSuchElementException:
        logger.warning('There are 0 people to follow')

    try:
        following_link = browser.find_elements_by_xpath(
            '//a[@href="/' + user_name + '/following/"]')
        following_link[0].click()
        # update server calls
        update_activity()
    except BaseException:
        logger.exception('message')

    sleep(2)

    # find dialog box
    dialog = browser.find_element_by_xpath(
        "//div[text()='Following']/following-sibling::div")

    # scroll down the page
    scroll_bottom(browser, dialog, allfollowing)

    # get follow buttons. This approch will find the follow buttons and
    # ignore the Unfollow/Requested buttons.
    follow_buttons = dialog.find_elements_by_xpath(
        "//div/div/span/button[text()='Follow']")
    person_list = []

    if amount >= len(follow_buttons):
        amount = len(follow_buttons)
        logger.warning("{} -> Less users to follow than requested."
                       .format(user_name))

    finalBtnPerson = []
    if randomize:
        sample = random.sample(range(0, len(follow_buttons)), amount)

        for num in sample:
            finalBtnPerson.append(follow_buttons[num])
    else:
        finalBtnPerson = follow_buttons[0:amount]
    for person in finalBtnPerson:

        if person and hasattr(person, 'text') and person.text:
            person_list.append(person.find_element_by_xpath(
                "../../../*").find_elements_by_tag_name("a")[1].text)

    return person_list


def follow_given_user_followers(account_id,
                                browser,
                                profile,
                                amount,
                                dont_include,
                                username,
                                follow_restrict,
                                random,
                                blacklist,
                                logger):
    """
    Goes to competitor profile, load followers list and follow the profiles

    Args:
        :account_id: Instagram Account ID
        :browser: web driver
        :profile: competitor profile
        :amount: amount of profile to be followed
        :dont_include: profiles to not follow
        :username: ?
        :follow_restrict: ?
        :random: randomize the following process
        :blacklist: blacklist setup
        :logger: library to log actions

    .. deprecated:: 0.0
        dont_include should be renamed to dont_touch

    Returns:
        A list of followed profiles
    """
    browser.get('https://www.instagram.com/{}'.format(profile))
    # update server calls
    update_activity()

    #  check how many poeple are following this user.
    #  throw RuntimeWarning if we are 0 people following this user
    try:
        allfollowing = formatNumber(
            browser.find_element_by_xpath("//li[2]/a/span").text)
    except NoSuchElementException:
        logger.warning('There are 0 people to follow')

    try:
        following_link = browser.find_elements_by_xpath('//li[2]/a/span')
        following_link[0].click()
        # update server calls
        update_activity()
    except BaseException:
        logger.exception('message')
        try:
            browser.refresh()
            sleep(3)
            link2 = browser.find_element_by_xpath("//li[2]/a/span")
            link2.click()
        except BaseException:
            logger.exception('message')

    personFollowed = follow_through_dialog(account_id,
                                           browser,
                                           profile,
                                           amount,
                                           dont_include,
                                           username,
                                           follow_restrict,
                                           allfollowing,
                                           random,
                                           blacklist,
                                           logger,
                                           callbacks=[])

    return personFollowed


def follow_given_user_following(account_id,
                                browser,
                                user_name,
                                amount,
                                dont_include,
                                login,
                                follow_restrict,
                                random,
                                delay,
                                blacklist,
                                logger):
    """
    I dont like this feature and I refuse to doc it :P
    """
    browser.get('https://www.instagram.com/' + user_name)
    # update server calls
    update_activity()

    #  check how many poeple are following this user.
    #  throw RuntimeWarning if we are 0 people following this user
    try:
        allfollowing = formatNumber(
            browser.find_element_by_xpath("//li[3]/a/span").text)
    except NoSuchElementException:
        logger.warning('There are 0 people to follow')

    try:
        following_link = browser.find_elements_by_xpath(
            '//a[@href="/' + user_name + '/following/"]')
        following_link[0].click()
        # update server calls
        update_activity()
    except BaseException:
        logger.exception('message')

    personFollowed = follow_through_dialog(account_id,
                                           browser,
                                           user_name,
                                           amount,
                                           dont_include,
                                           login,
                                           follow_restrict,
                                           allfollowing,
                                           random,
                                           blacklist,
                                           logger)

    return personFollowed


def cancel_pending_requests(browser, account, amount):
    """
    Cancel every pending follow request

    Args:
        :browser: web driver
        :account: our account
        :amount: amount of profiles to cancel pending requests

    .. warning::
        we can do the same action using the setup window
    """
    browser.get('https://www.instagram.com/{}'.format(account))

    # click followes button
    followers = browser.find_element_by_xpath('//li[2]/a/span')
    followers.click()

    # find dialog box
    dialog = browser.find_element_by_xpath(
      "//div[text()='Followers' or text()='Following']"
      "/following-sibling::div")

    # scroll down the page
    followers_amount = formatNumber(followers.text)
    scroll_bottom(browser, dialog, followers_amount)

    request_buttons = browser.find_elements_by_xpath(
        "//button[text()='Requested']")
    for profile in request_buttons:
        profile.click()
        print('pending test.. sleeping')
        sleep(10)


def unfollow_by_blacklist(browser,
                          logger,
                          campaign,
                          profiles_to_unfollow):
    count = 1
    for profile in profiles_to_unfollow:
        if (count % 11 == 0):
            sleep_delay = random.randint(60, 440)
            logger.info('sleeping for about {}min'
                        .format(int(sleep_delay/60)))
            sleep(sleep_delay)
        unfollow_profile_from_campaign(count,
                                       browser,
                                       logger,
                                       campaign,
                                       profile)
        count += 1
