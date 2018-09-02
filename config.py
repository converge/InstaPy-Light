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


tags = ['lawofattraction', 'datalimite', 'johnassaraf']
# from tag list, pick randomly 3 tags
tags = sample(set(tags), 3)

try:
    session = InstaPyLight(username='',
                           password='',
                           headless=False)
    session.login()
finally:
    # it will save the last page screen before end
    session.save_screenshot('last_screen.png')
    session.end()
