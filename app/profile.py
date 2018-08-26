"""
Class to manage Profile object
"""


class Profile:

    def __init__(self):
        self.name = None
        self.blacklist_likes = None
        self.blacklist_follows = None
        self.blacklist_never_follow_again = None

    def set_name(self, name):
        self.name = name

    def get_name(self):
        return self.name

    def set_blacklist_likes(self, blacklist_likes):
        self.blacklist_like = blacklist_likes

    def get_blacklist_likes(self):
        return self.blacklist_likes

    def set_blacklist_follows(self, blacklist_follows):
        self.blacklist_follows = blacklist_follows

    def get_blacklist_follows(self):
        return self.blacklist_follows

    def set_blacklist_never_follow_again(self, blacklist_never_follow_again):
        self.blacklist_never_follow_again = blacklist_never_follow_again

    def get_blacklist_never_follow_again(self):
        return self.blacklist_never_follow_again
