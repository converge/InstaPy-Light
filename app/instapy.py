import json
import logging
from math import ceil
import os
from datetime import datetime
from sys import maxsize
import random

from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.firefox.options import Options as Firefox_Options
from selenium.webdriver import DesiredCapabilities
import requests

from .like import check_link
from .like import get_links_for_tag
from .like import get_links_from_feed
from .like import get_tags
from .like import get_links_for_location
from .like import like_image
from .like import get_links_for_username
from .login import login_user
from .time_util import sleep
from .time_util import set_sleep_percentage
from .util import get_active_users
from .util import validate_username
from .util import get_account_id
from .util import register_account
from .unfollow import get_given_user_followers
from .unfollow import get_given_user_following
from .unfollow import unfollow_user
from .unfollow import follow_given_user_followers
from .unfollow import follow_given_user_following
from .unfollow import follow_user
from .unfollow import follow_given_user
from .unfollow import cancel_pending_requests
from .unfollow import unfollow_by_blacklist
from .unfollow import unfollow
from .blacklist import get_profiles_from_blacklist_campaign
from .blacklist import get_followed_by_campaign
from .blacklist import is_user_in_liked_blacklist
from .blacklist import is_user_in_followed_blacklist


class InstaPyLight:
    """
    Main Class
    """

    def __init__(self,
                 username=None,
                 password=None,
                 nogui=False,
                 selenium_local_session=True,
                 bypass_suspicious_attempt=False,
                 page_delay=25,
                 show_logs=True,
                 headless=False,
                 proxy_address=None,
                 proxy_port=0):

        self.account_id = None
        if nogui:
            self.display = Display(visible=0, size=(800, 600))
            self.display.start()

        self.browser = None
        self.headless = headless
        self.proxy_address = proxy_address
        self.proxy_port = proxy_port

        self.username = username or os.environ.get('INSTA_USER')
        self.password = password or os.environ.get('INSTA_PW')
        self.nogui = nogui

        self.page_delay = page_delay
        self.switch_language = True
        self.firefox_profile_path = None

        self.followed = 0
        self.follow_times = 1
        self.do_follow = False
        self.follow_percentage = 0
        self.dont_touch = []
        self.blacklist = {'enabled': False,
                          'campaign': '',
                          'blacklist_likes': False,
                          'blacklist_follows': False,
                          'liked_profiles': [],
                          'followed_profiles': [],
                          'blacklisted_profiles': [],
                          'never_follow_again': False}
        self.do_like = False
        self.like_percentage = 0
        self.smart_hashtags = []

        self.dont_like = ['sex', 'nsfw']
        self.ignore_if_contains = []

        self.user_interact_amount = 0
        self.user_interact_media = None
        self.user_interact_percentage = 0
        self.user_interact_random = False

        self.use_clarifai = False
        self.clarifai_api_key = None
        self.clarifai_img_tags = []
        self.clarifai_full_match = False

        self.like_by_followers_upper_limit = 0
        self.like_by_followers_lower_limit = 0

        self.bypass_suspicious_attempt = bypass_suspicious_attempt

        # register new account if it doesnt exist
        register_account(self.username)
        # set account_id
        self.account_id = get_account_id(self.username)

        # initialize and setup logging system
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        file_handler = logging.FileHandler(
            './logs/{}_general.log'.format(self.username))
        file_handler.setLevel(logging.DEBUG)
        logger_formatter = logging.Formatter(
            '%(asctime)s %(levelname)s - %(message)s',
            datefmt='%y-%m-%d %H:%M:%S')
        file_handler.setFormatter(logger_formatter)
        self.logger.addHandler(file_handler)

        if show_logs is True:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            console_handler.setFormatter(logger_formatter)
            self.logger.addHandler(console_handler)

        if selenium_local_session:
            self.set_selenium_local_session()

    def set_selenium_local_session(self):
        """
        Starts local session for a selenium server
        """
        firefox_options = Firefox_Options()
        if self.headless:
            firefox_options.add_argument('-headless')

        if self.firefox_profile_path is not None:
            firefox_profile = webdriver.FirefoxProfile(
                self.firefox_profile_path)
        else:
            firefox_profile = webdriver.FirefoxProfile()

        # permissions.default.image = 2: Disable images load,
        # this setting can improve pageload & save bandwidth
        firefox_profile.set_preference('permissions.default.image', 1)
        firefox_profile.set_preference('devtools.jsonview.enabled', False)

        if self.proxy_address and self.proxy_port > 0:
            firefox_profile.set_preference('network.proxy.type', 1)
            firefox_profile.set_preference('network.proxy.http',
                                           self.proxy_address)
            firefox_profile.set_preference('network.proxy.http_port',
                                           self.proxy_port)
            firefox_profile.set_preference('network.proxy.ssl',
                                           self.proxy_address)
            firefox_profile.set_preference('network.proxy.ssl_port',
                                           self.proxy_port)

        self.browser = webdriver.Firefox(
            firefox_profile=firefox_profile,
            options=firefox_options,
            executable_path=r'/usr/local/bin/geckodriver')

        self.browser.implicitly_wait(self.page_delay)
        self.logger.info('Session started')


    def set_selenium_remote_session(self, selenium_url=''):
        """
        Starts remote session for a selenium server. Useful for docker setup.
        """
        if self.use_firefox:
            self.browser = webdriver.Remote(
                command_executor=selenium_url,
                desired_capabilities=DesiredCapabilities.FIREFOX)
        else:
            self.browser = webdriver.Remote(
                command_executor=selenium_url,
                desired_capabilities=DesiredCapabilities.CHROME)

        self.logger.info('Session started - %s'
                         % (datetime.now().strftime('%Y-%m-%d %H:%M:%S')))


    def login(self):
        """
        Used to login the user either with the username and password
        """
        if not login_user(self.browser,
                          self.username,
                          self.password,
                          self.account_id,
                          self.switch_language,
                          self.bypass_suspicious_attempt):
            self.logger.critical('Wrong login data!')

        else:
            self.logger.info('Logged in successfully!')

    def set_sleep_reduce(self, percentage):
        """
        Can we delete it ?
        """
        set_sleep_percentage(percentage)

    def set_do_follow(self, percentage=0, times=1):
        """
        Defines if the user of the liked image should be followed
        """

        self.follow_times = times
        self.do_follow = True
        self.follow_percentage = percentage

    def set_do_like(self, percentage=0):

        self.do_like = True
        self.like_percentage = percentage

    def set_dont_like(self, tags=None):
        """
        Changes the possible restriction tags, if one of this words is in the
        description, the image won't be liked
        """
        if not isinstance(tags, list):
            self.logger.warning('Unable to use your set_dont_like '
                                'configuration!')

        self.dont_like = tags or []

    def set_user_interact(self,
                          amount=10,
                          percentage=100,
                          randomize=False,
                          media=None):
        """
        Define if posts of given user should be interacted
        """

        self.user_interact_amount = amount
        self.user_interact_random = randomize
        self.user_interact_percentage = percentage
        self.user_interact_media = media

    def set_ignore_if_contains(self, words=None):
        """
        Ignores the don't likes if the description contains one of the given
        words
        """
        self.ignore_if_contains = words or []

    def set_dont_touch(self, profiles=None):
        """
        Defines which accounts should not be liked, followed and unfollowed

        Args:
            :profiles: list of profiles to respect this rule
        """

        self.dont_touch = profiles or []

    def set_switch_language(self, option=True):
        self.switch_language = option

    def set_use_clarifai(self, api_key=None, full_match=False):
        """
        Defines if the clarifai img api should be used which 'project' will be
        used (only 5000 calls per month)
        """

        self.use_clarifai = True

        if api_key is None and self.clarifai_api_key is None:
            self.clarifai_api_key = os.environ.get('CLARIFAI_API_KEY')
        elif api_key is not None:
            self.clarifai_api_key = api_key

        self.clarifai_full_match = full_match

    def set_smart_hashtags(self,
                           tags=None,
                           limit=3,
                           sort='top',
                           log_tags=True):
        """
        Generate smart hashtags based on https://displaypurposes.com/ ranking,
        banned and spammy tags are filtered out
        """

        if tags is None:
            print('set_smart_hashtags is misconfigured')
            return

        for tag in tags:
            req = requests.get(
                'https://d212rkvo8t62el.cloudfront.net/tag/{}'.format(tag))
            data = json.loads(req.text)

            if data['tagExists'] is True:
                if sort == 'top':
                    # sort by ranking
                    ordered_tags_by_rank = sorted(
                        data['results'], key=lambda d: d['rank'], reverse=True)
                    ranked_tags = (ordered_tags_by_rank[:limit])
                    for item in ranked_tags:
                        # add smart hashtag to like list
                        self.smart_hashtags.append(item['tag'])

                elif sort == 'random':
                    random_tags = random.sample(data['results'], limit)
                    for item in random_tags:
                        self.smart_hashtags.append(item['tag'])

                if log_tags is True:
                    for item in self.smart_hashtags:
                        print('[smart hashtag generated: {}]'.format(item))
            else:
                print('Too few results for #{} tag'.format(tag))

        # delete duplicated tags
        self.smart_hashtags = list(set(self.smart_hashtags))

    def follow_by_list(self, followlist, times=1):
        """
        Allows to follow by any scrapped list
        """
        self.follow_times = times or 0

        followed = 0

        for acc_to_follow in followlist:
            if acc_to_follow in self.dont_touch:
                continue

            if self.follow_restrict.get(acc_to_follow, 0) < self.follow_times:
                followed += follow_given_user(self.account_id,
                                              self.browser,
                                              acc_to_follow,
                                              self.follow_restrict,
                                              self.blacklist,
                                              self.logger)
                self.followed += followed
                self.logger.info('Followed: {}'.format(str(followed)))
                followed = 0
            else:
                self.logger.info('---> {} has already been followed more than '
                                 '{} times'.format(
                                    acc_to_follow, str(self.follow_times)))
                sleep(1)

    def set_upper_follower_count(self, limit=None):
        """
        Used to chose if a post is liked by the number of likes
        """
        self.like_by_followers_upper_limit = limit or maxsize

    def set_lower_follower_count(self, limit=None):
        """
        Used to chose if a post is liked by the number of likes
        """
        self.like_by_followers_lower_limit = limit or 0

    def like_by_locations(self,
                          locations=None,
                          amount=50,
                          media=None,
                          skip_top_posts=True):
        """
        Likes (default) 50 images per given locations
        """

        liked_img = 0
        already_liked = 0
        inap_img = 0
        followed = 0

        locations = locations or []

        for index, location in enumerate(locations):
            self.logger.info('Location [{}/{}]'
                             .format(index + 1, len(locations)))
            self.logger.info('--> {}'.format(location.encode('utf-8')))

            try:
                links = get_links_for_location(self.browser,
                                               location,
                                               amount,
                                               self.logger,
                                               media,
                                               skip_top_posts)
            except NoSuchElementException:
                self.logger.warning('Too few images, skipping this location')
                continue

            for i, link in enumerate(links):
                self.logger.info('[{}/{}]'.format(i + 1, len(links)))
                self.logger.info(link)

                try:
                    inappropriate, user_name, is_video, reason = (
                        check_link(self.browser,
                                   link,
                                   self.dont_like,
                                   self.ignore_if_contains,
                                   self.username,
                                   self.like_by_followers_upper_limit,
                                   self.like_by_followers_lower_limit,
                                   self.logger)
                    )

                    if (inappropriate is False and
                       is_user_in_liked_blacklist(
                            user_name, self.blacklist) is False):
                        liked = like_image(self.account_id,
                                           self.browser,
                                           self.blacklist,
                                           self.logger)

                        if liked:
                            liked_img += 1
                            checked_img = True
                            following = random.randint(
                                0, 100) <= self.follow_percentage

                            if (self.do_follow and
                                user_name not in self.dont_touch and
                                checked_img and
                                following and
                                self.follow_restrict.get(user_name, 0) <
                                    self.follow_times):

                                # check blacklist
                                if not is_user_in_followed_blacklist(
                                    user_name,
                                    self.blacklist
                                ):

                                    followed += follow_user(
                                        self.account_id,
                                        self.browser,
                                        self.follow_restrict,
                                        self.username,
                                        user_name,
                                        self.blacklist,
                                        self.logger)

                            else:
                                self.logger.info('--> Not following')
                                sleep(1)
                        else:
                            already_liked += 1
                    else:
                        self.logger.info(
                            '--> Image not liked: {}'.format(reason))
                        inap_img += 1
                except NoSuchElementException:
                    self.logger.exception('message')

        self.logger.info('Liked: {}'.format(liked_img))
        self.logger.info('Already Liked: {}'.format(already_liked))
        self.logger.info('Inappropriate: {}'.format(inap_img))
        self.logger.info('Followed: {}'.format(followed))

        self.followed += followed

    def like_by_tags(self,
                     tags=None,
                     amount=50,
                     media=None,
                     skip_top_posts=True,
                     use_smart_hashtags=False):
        """
        Likes (default) 50 images per given tag

        Args:
            :tags: list of tags to be liked
            :amount: amount of interactions
            :media: Photo or Video are available
            :skip_top_posts: skip initial posts
            :use_smart_hashtags: auto generate hashtags to be liked
        """

        if not tags:
            self.logger.warning('Hashtags not set! skipping like by tags..')
            return

        liked_img = 0
        already_liked = 0
        inap_img = 0
        followed = 0

        # if smart hashtag is enabled
        if use_smart_hashtags is True and self.smart_hashtags is not []:
            print('Using smart hashtags')
            tags = self.smart_hashtags

        # deletes white spaces in tags
        tags = [tag.strip() for tag in tags]

        tags = tags or []

        for index, tag in enumerate(tags):
            self.logger.info('Tag [{}/{}]'.format(index + 1, len(tags)))
            self.logger.info('--> {}'.format(tag.encode('utf-8')))

            try:
                links = get_links_for_tag(self.browser,
                                          tag,
                                          amount,
                                          self.logger,
                                          media,
                                          skip_top_posts)
            except NoSuchElementException:
                self.logger.error('Too few images, skipping this tag')
                continue

            for i, link in enumerate(links):
                self.logger.info('[{}/{}]'.format(i + 1, len(links)))
                self.logger.info(link)
                try:
                    inappropriate, profile, is_video, reason = (
                        check_link(self.browser,
                                   link,
                                   self.dont_like,
                                   self.ignore_if_contains,
                                   self.username,
                                   self.like_by_followers_upper_limit,
                                   self.like_by_followers_lower_limit,
                                   self.logger)
                    )

                    if (is_user_in_liked_blacklist(profile,
                                                   self.blacklist) is True):
                        reason = '{} is in liked blacklist'.format(profile)
                        inappropriate = True

                    if inappropriate is False:
                        liked = like_image(self.account_id,
                                           self.browser,
                                           profile,
                                           self.blacklist,
                                           self.logger)

                        if liked:
                            liked_img += 1
                            checked_img = True
                            following = (random.randint(0, 100) <=
                                         self.follow_percentage)

                            if (self.do_follow and
                                profile not in self.dont_touch and
                                checked_img and
                                following and
                                self.follow_restrict.get(profile, 0) <
                                    self.follow_times):

                                # check blacklist
                                if not is_user_in_followed_blacklist(
                                    profile,
                                    self.blacklist
                                ):

                                    followed += follow_user(
                                        self.account_id,
                                        self.browser,
                                        self.follow_restrict,
                                        self.username,
                                        profile,
                                        self.blacklist,
                                        self.logger)
                            else:
                                self.logger.info('--> Not following')
                                sleep(1)
                        else:
                            already_liked += 1
                    else:
                        self.logger.info(
                            '--> Image not liked: {}'.format(reason))
                        inap_img += 1
                except NoSuchElementException:
                    self.logger.exception('message')

        self.logger.info('Liked: {}'.format(liked_img))
        self.logger.info('Already Liked: {}'.format(already_liked))
        self.logger.info('Inappropriate: {}'.format(inap_img))
        self.logger.info('Followed: {}'.format(followed))

        self.followed += followed

    def like_by_users(self, usernames, amount=10, randomize=False, media=None):
        """
        Likes some amounts of images for each usernames
        """

        total_liked_img = 0
        already_liked = 0
        inap_img = 0
        followed = 0
        usernames = usernames or []

        for index, username in enumerate(usernames):
            self.logger.info(
                'Username [{}/{}]'.format(index + 1, len(usernames)))
            self.logger.info('--> {}'.format(username.encode('utf-8')))
            following = random.randint(0, 100) <= self.follow_percentage

            valid_user = validate_username(self.browser,
                                           username,
                                           self.blacklist,
                                           self.like_by_followers_upper_limit,
                                           self.like_by_followers_lower_limit)
            if valid_user is not True:
                self.logger.info(valid_user)
                continue

            try:
                links = get_links_for_username(
                    self.browser,
                    username,
                    amount,
                    self.logger,
                    randomize,
                    media)
            except NoSuchElementException:
                self.logger.error('Element not found, skipping this username')
                continue

            if (self.do_follow and
                username not in self.dont_touch and
                following and
                    self.follow_restrict.get(username, 0) < self.follow_times):

                # check blacklist
                if not is_user_in_followed_blacklist(
                    username,
                    self.blacklist
                ):
                    followed += follow_user(self.account_id,
                                            self.browser,
                                            self.follow_restrict,
                                            self.username,
                                            username,
                                            self.blacklist,
                                            self.logger)
            else:
                self.logger.info('--> Not following')
                sleep(1)

            if links is False:
                continue

            # Reset like counter for every username
            liked_img = 0

            for i, link in enumerate(links):
                # Check if target has reached
                if liked_img >= amount:
                    self.logger.info('-------------')
                    self.logger.info("--> Total liked image reached it's "
                                     "amount given: {}".format(liked_img))
                    break

                self.logger.info('Post [{}/{}]'.format(liked_img + 1, amount))
                self.logger.info(link)

                try:
                    inappropriate, user_name, is_video, reason = (
                        check_link(self.browser,
                                   link,
                                   self.dont_like,
                                   self.ignore_if_contains,
                                   self.username,
                                   self.like_by_followers_upper_limit,
                                   self.like_by_followers_lower_limit,
                                   self.logger)
                    )

                    if (inappropriate is False and
                       is_user_in_liked_blacklist(
                            user_name, self.blacklist) is False):
                        liked = like_image(self.account_id,
                                           self.browser,
                                           user_name,
                                           self.blacklist,
                                           self.logger)

                        if liked:
                            total_liked_img += 1
                            liked_img += 1
                        else:
                            already_liked += 1

                    else:
                        self.logger.info(
                            '--> Image not liked: {}'.format(reason))
                        inap_img += 1
                except NoSuchElementException:
                    self.logger.exception('message')

            if liked_img < amount:
                self.logger.info('-------------')
                self.logger.info("--> Given amount not fullfilled, "
                                 "image pool reached its end\n")

        self.logger.info('Liked: {}'.format(total_liked_img))
        self.logger.info('Already Liked: {}'.format(already_liked))
        self.logger.info('Inappropriate: {}'.format(inap_img))

    def interact_by_users(self,
                          usernames,
                          amount=10,
                          randomize=False,
                          media=None):
        """
        Likes some amounts of images for each usernames
        """

        total_liked_img = 0
        already_liked = 0
        inap_img = 0
        followed = 0

        usernames = usernames or []

        for index, username in enumerate(usernames):
            self.logger.info(
                'Username [{}/{}]'.format(index + 1, len(usernames)))
            self.logger.info('--> {}'.format(username.encode('utf-8')))

            try:
                links = get_links_for_username(self.browser,
                                               username,
                                               amount,
                                               self.logger,
                                               randomize,
                                               media)
            except NoSuchElementException:
                self.logger.error('Element not found, skipping this username')
                continue

            if links is False:
                continue

            # Reset like counter for every username
            liked_img = 0

            for i, link in enumerate(links):
                # Check if target has reached
                if liked_img >= amount:
                    self.logger.info('-------------')
                    self.logger.info("--> Total liked image reached it's "
                                     "amount given: {}".format(liked_img))
                    break

                self.logger.info('Post [{}/{}]'.format(liked_img + 1, amount))
                self.logger.info(link)

                try:
                    inappropriate, user_name, is_video, reason = (
                        check_link(self.browser,
                                   link,
                                   self.dont_like,
                                   self.ignore_if_contains,
                                   self.username,
                                   self.like_by_followers_upper_limit,
                                   self.like_by_followers_lower_limit,
                                   self.logger)
                    )

                    if (inappropriate is False and
                       is_user_in_liked_blacklist(
                            user_name, self.blacklist) is False):

                        following = (
                            random.randint(0, 100) <= self.follow_percentage)
                        if (self.do_follow and
                            username not in self.dont_touch and
                            following and
                            self.follow_restrict.get(
                                username, 0) < self.follow_times):

                            # check blacklist
                            if not is_user_in_followed_blacklist(
                                user_name,
                                self.blacklist
                            ):
                                followed += follow_user(
                                    self.account_id,
                                    self.browser,
                                    self.follow_restrict,
                                    self.username,
                                    username,
                                    self.blacklist,
                                    self.logger)
                        else:
                            self.logger.info('--> Not following')
                            sleep(1)

                        liking = random.randint(0, 100) <= self.like_percentage
                        if self.do_like and liking:
                            liked = like_image(self.account_id,
                                               self.browser,
                                               user_name,
                                               self.blacklist,
                                               self.logger)
                        else:
                            liked = True

                        if liked:
                            total_liked_img += 1
                            liked_img += 1
                        else:
                            already_liked += 1

                    else:
                        self.logger.info(
                            '--> Image not liked: {}'.format(reason))
                        inap_img += 1
                except NoSuchElementException:
                    self.logger.exception('message')

            if liked_img < amount:
                self.logger.info('-------------')
                self.logger.info("--> Given amount not fullfilled, image pool "
                                 "reached its end\n")

        self.logger.info('Liked: {}'.format(total_liked_img))
        self.logger.info('Already Liked: {}'.format(already_liked))
        self.logger.info('Inappropriate: {}'.format(inap_img))

    def like_from_image(self, url, amount=50, media=None):
        """
        Gets the tags from an image and likes 50 images for each tag
        """

        try:
            if not url:
                urls = self.browser.find_elements_by_xpath(
                    "//main//article//div//div[1]//div[1]//a[1]")
                url = urls[0].get_attribute("href")
                self.logger.info("new url {}".format(url))
            tags = get_tags(self.browser, url)
            self.logger.info(tags)
            self.like_by_tags(tags, amount, media)
        except TypeError:
            self.logger.exception('message')

    def interact_user_followers(self, usernames, amount=10, randomize=False):
        """
        ?
        """
        user_to_interact = []
        if not isinstance(usernames, list):
            usernames = [usernames]
        try:
            for user in usernames:

                user = get_given_user_followers(self.browser,
                                                user,
                                                amount,
                                                self.dont_touch,
                                                self.username,
                                                self.follow_restrict,
                                                randomize,
                                                self.logger)
                if isinstance(user, list):
                    user_to_interact += user
        except (TypeError, RuntimeWarning) as err:
            if isinstance(err, RuntimeWarning):
                self.logger.warning(
                    u'Warning: {} , stopping follow_users'.format(err))
            else:
                self.logger.error('Sorry, an error occured: {}'.format(err))

        self.logger.info('--> Users: {} \n'.format(len(user_to_interact)))
        user_to_interact = random.sample(
            user_to_interact,
            int(ceil(
                self.user_interact_percentage * len(user_to_interact) / 100
            ))
        )

        self.like_by_users(user_to_interact,
                           self.user_interact_amount,
                           self.user_interact_random,
                           self.user_interact_media)

    def interact_user_following(self, usernames, amount=10, randomize=False):
        """
        ?
        """
        user_to_interact = []
        if not isinstance(usernames, list):
            usernames = [usernames]
        try:
            for user in usernames:
                user_to_interact += get_given_user_following(
                    self.browser,
                    user,
                    amount,
                    self.dont_touch,
                    self.username,
                    self.follow_restrict,
                    randomize,
                    self.logger)
        except (TypeError, RuntimeWarning) as err:
            if isinstance(err, RuntimeWarning):
                self.logger.warning(
                    u'Warning: {} , stopping follow_users'.format(err))
            else:
                self.logger.error('Sorry, an error occured: {}'.format(err))

        self.logger.info('--> Users: {}'.format(len(user_to_interact)))

        user_to_interact = random.sample(user_to_interact, int(ceil(
            self.user_interact_percentage * len(user_to_interact) / 100)))

        self.like_by_users(user_to_interact,
                           self.user_interact_amount,
                           self.user_interact_random,
                           self.user_interact_media)

    def follow_user_followers(self,
                              profiles,
                              amount=10,
                              randomize=False,
                              interact=False,
                              sleep_delay=600):
        """
        Follow competitors followers

        Args:
            :profiles: profiles to follow followers
            :amount: amount of follows per profile
            :randomize: follow profile randomly
            :interact: ?
            :sleep_delay: <- we need to automate it inside the feature

        :Example:

        .. code-block:: python

            profiles = ['profile1', 'profile2', 'profile3']
            follow_user_followers(profiles,
                                  amount=10,
                                  randomize=True)

        """
        userFollowed = []
        if not isinstance(profiles, list):
            profiles = [profiles]
        for profile in profiles:

            try:
                userFollowed += follow_given_user_followers(self.account_id,
                                                            self.browser,
                                                            profile,
                                                            amount,
                                                            self.dont_touch,
                                                            self.username,
                                                            randomize,
                                                            self.blacklist,
                                                            self.logger)

            except (TypeError, RuntimeWarning) as err:
                if isinstance(err, RuntimeWarning):
                    self.logger.warning(
                        u'Warning: {} , skipping to next user'.format(err))
                    continue
                else:
                    self.logger.error(
                        'Sorry, an error occured: {}'.format(err))
        self.logger.info(
            "--> Total people followed : {} ".format(len(userFollowed)))

        if interact:
            self.logger.info('--> User followed: {}'.format(userFollowed))
            userFollowed = random.sample(userFollowed, int(ceil(
                self.user_interact_percentage * len(userFollowed) / 100)))
            self.like_by_users(userFollowed,
                               self.user_interact_amount,
                               self.user_interact_random,
                               self.user_interact_media)

    def follow_user_following(self,
                              usernames,
                              amount=10,
                              randomize=False,
                              interact=False,
                              sleep_delay=600):
        """
        Follow competitor followings
        """
        userFollowed = []
        if not isinstance(usernames, list):
            usernames = [usernames]

        for user in usernames:
            try:
                userFollowed += follow_given_user_following(self.account_id,
                                                            self.browser,
                                                            user,
                                                            amount,
                                                            self.dont_touch,
                                                            self.username,
                                                            self.follow_restrict,
                                                            randomize,
                                                            sleep_delay,
                                                            self.blacklist,
                                                            self.logger)

            except (TypeError, RuntimeWarning) as err:
                if isinstance(err, RuntimeWarning):
                    self.logger.warning(
                        u'Warning: {} , skipping to next user'.format(err))
                    continue
                else:
                    self.logger.error(
                        'Sorry, an error occured: {}'.format(err))

        self.logger.info(
            "--> Total people followed : {} ".format(len(userFollowed)))

        if interact:
            self.logger.info('--> User followed: {}'.format(userFollowed))
            userFollowed = random.sample(userFollowed, int(ceil(
                self.user_interact_percentage * len(userFollowed) / 100)))
            self.like_by_users(userFollowed,
                               self.user_interact_amount,
                               self.user_interact_random,
                               self.user_interact_media)

    def unfollow_users(self, amount=10):
        """
        Unfollow users

        Args:
            :amount: amount of profiles to unfollow

        .. warning::
            onlyNotFollowMe feature not working

        :Example:

        .. code-block:: python

            unfollow_users(amount=10)
        """
        try:
            unfollowNumber = unfollow(self.browser,
                                      self.username,
                                      amount,
                                      self.dont_touch,
                                      self.logger)
            self.logger.info(
                "--> Total people unfollowed : {} ".format(unfollowNumber))

        except (TypeError, RuntimeWarning) as err:
            if isinstance(err, RuntimeWarning):
                self.logger.warning(
                    u'Warning: {} , stopping unfollow_users'.format(err))
            else:
                self.logger.info('Sorry, an error occured: {}'.format(err))

    def like_by_feed(self,
                     amount=50,
                     randomize=False,
                     unfollow=False,
                     interact=False):
        """
        Like the users feed
        """

        liked_img = 0
        already_liked = 0
        inap_img = 0
        followed = 0
        skipped_img = 0
        num_of_search = 0
        history = []

        while liked_img < amount:
            try:
                # Gets another load of links to be tested
                links = get_links_from_feed(self.browser,
                                            amount,
                                            num_of_search,
                                            self.logger)
            except NoSuchElementException:
                self.logger.warning('Too few images, aborting')

            num_of_search += 1

            for i, link in enumerate(links):
                if liked_img == amount:
                    break
                if randomize and random.choice([True, False]):
                    self.logger.warning('Post Randomly Skipped...\n')
                    skipped_img += 1
                else:
                    if link in history:
                        self.logger.info('This link has already '
                                         'been visited:\n', link, '\n')
                    else:
                        self.logger.info('New link found...')
                        history.append(link)
                        self.logger.info('[{} posts liked /{} amount]'
                                         .format(liked_img, amount))
                        self.logger.info(link)

                        try:
                            inappropriate, user_name, is_video, reason = (
                                check_link(self.browser,
                                           link,
                                           self.dont_like,
                                           self.ignore_if_contains,
                                           self.username,
                                           self.like_by_followers_upper_limit,
                                           self.like_by_followers_lower_limit,
                                           self.logger)
                            )

                            if (inappropriate is False and
                               is_user_in_liked_blacklist(
                                    user_name, self.blacklist) is False):
                                liked = like_image(self.account_id,
                                                   self.browser,
                                                   user_name,
                                                   self.blacklist,
                                                   self.logger)

                                if liked:
                                    username = (self.browser.
                                                find_element_by_xpath(
                                                    '//article/header/div[2]/'
                                                    'div[1]/div/a'))

                                    username = username.get_attribute("title")
                                    name = []
                                    name.append(username)

                                    if interact:
                                        self.logger.info(
                                            '--> User followed: {}'
                                            .format(name))
                                        self.like_by_users(
                                            name,
                                            self.user_interact_amount,
                                            self.user_interact_random,
                                            self.user_interact_media)

                                    liked_img += 1
                                    checked_img = True
                                    following = random.randint(
                                        0, 100) <= self.follow_percentage

                                    if (self.do_follow and
                                        user_name not in self.dont_touch and
                                        checked_img and
                                        following and
                                        self.follow_restrict.get(
                                            user_name, 0) < self.follow_times):

                                        # check blacklist
                                        if not is_user_in_followed_blacklist(
                                            user_name,
                                            self.blacklist
                                        ):
                                            followed += follow_user(
                                                self.account_id,
                                                self.browser,
                                                self.follow_restrict,
                                                self.username,
                                                user_name,
                                                self.blacklist,
                                                self.logger)
                                    else:
                                        self.logger.info('--> Not following')
                                        sleep(1)
                                else:
                                    already_liked += 1
                            else:
                                self.logger.info(
                                    '--> Image not liked: {}'.format(reason))
                                inap_img += 1
                                if reason == 'Inappropriate':
                                    unfollow_user(self.browser, self.logger)
                        except NoSuchElementException:
                            self.logger.exception('message')

        self.logger.info('Liked: {}'.format(liked_img))
        self.logger.info('Already Liked: {}'.format(already_liked))
        self.logger.info('Inappropriate: {}'.format(inap_img))
        self.logger.info('Followed: {}'.format(followed))
        self.logger.info('Randomly Skipped: {}'.format(skipped_img))

        self.followed += followed

    def set_dont_unfollow_active_users(self, posts=4):
        """
        Prevents unfollow followers who have liked one of your latest X posts

        Args:
            :posts: amount of posts to collect profile to not unfollow

        .. warning::
            feature not working
        """

        # list of users who liked our media
        active_users = get_active_users(self.browser,
                                        self.username,
                                        posts,
                                        self.logger)

        for user in active_users:
            # include active user to not unfollow list
            self.dont_touch.append(user)

    def set_blacklist(self,
                      campaign,
                      blacklist_likes,
                      blacklist_follows,
                      never_follow_again):
        """
        Enable blacklist feature

        Args:
            :campaign: every blacklist campaign has a name
            :blacklist_likes: blacklist profile after liking a post
            :blacklist_follows: blacklist profile after following
            :never_follow_again: mark profile to never be followed again

        :Example:

        .. code-block:: python

            set_blacklist('campaign_name',
                          blacklist_likes=False,
                          blacklist_follows=True,
                          never_follow_again=True)
        """
        # values for old/new campaign
        self.blacklist['enabled'] = True
        self.blacklist['campaign'] = campaign
        self.blacklist['blacklist_likes'] = blacklist_likes
        self.blacklist['blacklist_follows'] = blacklist_follows
        self.blacklist['never_follow_again'] = never_follow_again

        profiles = get_profiles_from_blacklist_campaign(self.blacklist,
                                                        self.account_id,
                                                        self.logger)
        if profiles is not None:
            for profile in profiles:
                self.blacklist['blacklisted_profiles'].append(profile.name)
            self.logger.info('{} profiles wont be followed based on {} '
                             'blacklist campaign'.format(
                                len(profiles), self.blacklist['campaign']))

    def cancel_pending_follow_requests(self, accounts, amount):
        """
        .. note::
            This feature is under development
        """
        for account in accounts:
            cancel_pending_requests(self.browser, account, amount)

    def save_screenshot(self, filename):
        """
        Save screen shot and save it

        Args:
            :filename: filename of the screen shot
        """
        self.browser.save_screenshot(filename)

    def whats_my_ip(self):
        """
        Check and retrieve actual IP address
        """
        self.browser.get('https://whour.net/')
        sleep(4)
        ip_address = self.browser.find_element_by_xpath(
            "//tbody/tr[1]/td[2]/strong")
        print(ip_address.text)

    def unfollow_by_blacklist_campaign(self,
                                       campaign,
                                       amount):
        """
        Unfollow only profiles in certain blacklist campaign

        Args:
            :campaign: blacklist campaign name
            :amount: amount of profiles to unfollow
        """
        profiles_to_unfollow = get_followed_by_campaign(campaign)
        if amount > len(profiles_to_unfollow):
            amount = len(profiles_to_unfollow)
        if len(profiles_to_unfollow) > 0:
            profiles_to_unfollow = random.sample(profiles_to_unfollow, amount)
            unfollow_by_blacklist(self.browser,
                                  self.logger,
                                  campaign,
                                  profiles_to_unfollow)
        else:
            self.logger.warning(
                'No profiles to unfollow in the "{}" campaign'
                .format(campaign))

    def end(self):
        """
        Closes the current session
        """
        self.browser.delete_all_cookies()
        self.browser.close()

        if self.nogui:
            self.display.stop()

        self.logger.info('Session ended - {}'.format(
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        self.logger.info('-' * 20 + '\n\n')

        with open('./logs/followed.txt', 'w') as followFile:
            followFile.write(str(self.followed))
