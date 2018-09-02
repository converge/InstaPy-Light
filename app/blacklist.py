import sqlite3
from .profile import Profile
from .util import DATABASE_LOCATION


def get_profiles_from_blacklist_campaign(blacklist, username, logger):
    """
    Returns all users from a blacklist campaign

    Args:
        :blacklist: blacklist setup
        :account_id: username account id
        :logger: library to log actions
    Returns:
        list of profile names from the campaign
    """
    profiles = []
    try:
        conn = sqlite3.connect(DATABASE_LOCATION)
        with conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            sql = (
                "SELECT profile, campaign, liked, followed, "
                "never_follow_again FROM blacklist "
                "WHERE campaign = ? "
                "  AND profile = ?"
                "  AND liked = ?"
                "  AND never_follow_again = ?"
                "GROUP BY profile")
            cur.execute(sql, (blacklist['campaign'],
                              username,
                              blacklist['blacklist_likes'],
                              blacklist['never_follow_again']))
            data = cur.fetchall()
            if data is not None:
                for p in data:
                    profile = Profile()
                    profile.set_name(p['profile'])
                    profile.set_blacklist_likes(p['liked'])
                    profile.set_blacklist_follows(p['following'])
                    profile.set_blacklist_never_follow_again(
                        p['never_follow_again'])
                    profiles.append(profile)
                logger.info(
                    'There are {} profiles in "{}" blacklist campaign'
                    .format(len(data), blacklist['campaign']))
            else:
                logger.info(
                    "First time campaign '{}' is running"
                    .format(blacklist['campaign']))
        return profiles
    except Exception:
        logger.exception('message')


def get_followed_by_campaign(campaign):
    """
    Get all followed users from a blacklist campaign

    Args:
        :campaign: blacklist campaign name
    Returns:
        List of profiles followed by the campaign
    """
    conn = sqlite3.connect(DATABASE_LOCATION)
    followed = []
    with conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        sql = (
            "SELECT profile FROM blacklist WHERE campaign = ? AND "
            "following = 1")
        cur.execute(sql, (campaign,))
        data = cur.fetchall()
        if data is not None:
            for profile in data:
                followed.append(profile['profile'])
    return followed


def add_user_to_blacklist(account_id,
                          browser,
                          profile,
                          blacklist,
                          action,
                          logger):
    """
    Adds a profile to user blacklist campaign

    Args:
        :username: username (logged in user)
        :browser: web driver
        :profile: profile to be added to blacklist campaign
        :blacklist: blacklist setup
        :action: action done by the user (like or follow)
        :logger: library to log actions.
    """
    if action == 'like':
        try:
            conn = sqlite3.connect(DATABASE_LOCATION)
            with conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                sql = ("INSERT OR REPLACE INTO blacklist "
                       "(account_id, profile, campaign, liked, created) "
                       "VALUES (?, ?, ?, ?, date('now'))")
                cur.execute(sql, (account_id,
                                  profile,
                                  blacklist['campaign'],
                                  blacklist['blacklist_likes'],))
            conn.commit()

            logger.info('--> {} added to blacklist for "{}" campaign'
                        '(action: {})'
                        .format(profile, blacklist['campaign'], action))
        except Exception:
            logger.exception('message')

    elif action == 'follow':
        try:
            conn = sqlite3.connect(DATABASE_LOCATION)
            with conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                sql = ("INSERT OR REPLACE INTO blacklist "
                       "(username, profile, campaign, following, "
                       "never_follow_again, created) "
                       "VALUES (?, ?, ?, ?, ?, date('now'))")
                cur.execute(sql, (username,
                                  profile,
                                  blacklist['campaign'],
                                  blacklist['blacklist_follows'],
                                  blacklist['never_follow_again'],))
            conn.commit()

            logger.info('--> {} added to blacklist for "{}" campaign '
                        '(action: {})'
                        .format(profile, blacklist['campaign'], action))
        except Exception:
            logger.exception('message')


def mark_as_unfollowed_by_blacklist_campaign(profile, campaign, logger):
    """
    Update database marking the profile as unfollowed by the blacklist campaign

    Args:
        :profile: profile to by marked as unfollowed by blacklist campaign
        :campaign: black campaign name
        :logger: library to log actions
    """
    try:
        conn = sqlite3.connect(DATABASE_LOCATION)
        with conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            sql = ("UPDATE blacklist "
                   "SET following = 0 "
                   "WHERE profile = ? "
                   "AND campaign = ?")
            cur.execute(sql, (profile, campaign,))
        conn.commit()
    except Exception:
        logger.exception('message')


def is_user_in_followed_blacklist(profile, blacklist):
    """
    Check if profile is in blacklist (followed by the blacklist campaign)

    Args:
        :profile: profile to be checked
        :blacklist: blacklist setup
    Returns:
        True or False
    """
    if blacklist['enabled'] is True:
        if profile in blacklist['followed_profiles']:
            return True
    return False


def is_user_in_liked_blacklist(profile, blacklist):
    """
    Check if profile is in blacklist (liked by the blacklist campaign)

    Args:
        :profile: profile to be checked
        :blacklist: blacklist setup
    Returns:
        True or False
    """
    if blacklist['campaign']:
        if profile in blacklist['liked_profiles']:
            return True
    return False
