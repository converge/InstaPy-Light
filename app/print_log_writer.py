"""Module only used to log the number of followers to a file"""


def log_followed_pool(login, followed, logger):
    """
    Prints and logs the followed to a seperate file
    .. note::
        Can we delete it ?
    """
    try:
        with open('./logs/' + login + '_followedPool.csv', 'a+') as followPool:
            followPool.write(followed + ",\n")
    except BaseException:
        logger.exception('message')
