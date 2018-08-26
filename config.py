#
# This is a basic configuration, all features are explained at
# https://github.com/converge/InstaPy-Light
#
from app import InstaPyLight
from random import randint, sample


def get_like_n_times():
    return randint(1, 3)


def get_follow_n_times():
    return randint(1, 3)


def get_random_sleep_delay():
    return randint(45, 140)


def get_unfollow_n_times():
    return randint(1, 3)


accounts_to_follow = ['account1', 'account2', 'account3']

tags = ['tag1', 'tag2', 'tag3']

accounts_to_follow = sample(set(accounts_to_follow), 3)
try:
    session = InstaPyLight(username='',
                           password='',
                           use_firefox=True,
                           headless=False)
    session.login()
    tags = sample(set(tags), 3)
    session.set_blacklist(campaign='blacklist_campaign',
                          blacklist_likes=False,
                          blacklist_follows=True,
                          never_follow_again=True)
    # session.like_by_tags(tags, amount=3) @todo: fix this feature
    session.unfollow_users(amount=get_unfollow_n_times())
finally:
    session.save_screenshot('last_screen.png')
    session.end()
