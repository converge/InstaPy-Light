
# Contents

* [Introduction](#introduction-and-initial-setup)
* [Features](#features)
  * [Like By Tags](#like-by-tags)
  * [Follow Competitors Followers](#follow-competitors-followers)
  * [Blacklist](#blacklist)
  * [Unfollow by Blacklist Campaign](#unfollow-by-blacklist-campaign)
  * [Unfollow](#unfollow)
* [Developers documentation](#developers-documentation)
* [Feedback](#feedback)

## Introduction and initial setup

InstaPy-Light is a light version of InstaPy. The main goal is to have a minimalism approach over InstaPy, beeing easier to setup and use, including basic features.

### Setup your Instagram account

<img src="https://media.giphy.com/media/klwq5Nnl7riXxIvOoH/giphy.gif">

## Features

### Like By Tags

- **tags** a list of tags to be used to like posts
- **amount** the amount of posts you would like to like

**example:**

```python
tags ['johnassaraf', 'lawofattraction']
session.like_by_tags(tags, amount=3)
```

Every tag will be liked n(amount) times

### Follow Competitors Followers

Follow your competitors followers.

- **profile** list of competitors to follow their followers
- **amount** the amount of profiles to be followed by competitor

```python
profiles = ['instagram', 'facebook', 'spotify']
session.follow_user_followers(profiles, amount=5)
```

### Blacklist

This feature allows us to blacklist profiles **by campaign**.

- **campaign** campaign name
- **blacklist_likes=True** avoid liking profiles already liked
- **blacklist_follows=True** avoid following already followed profiles
- **never_follow_again=True** avoid unfollow and follow a profile again. After follow/unfollow process, the profile won't be followed again.

**example:**

```python
session.set_blacklist(campaign='blacklist_campaign',
                      blacklist_likes=True,
                      blacklist_follows=True,
                      never_follow_again=True)
```

### Unfollow by Blacklist Campaign

Unfollow only profiles saved in your previous blacklist campaign

- **campaign** blacklist campaign name
- **amount** amount of profiles to be unfollowed

```python
session.unfollow_by_blacklist_campaign(campaign='blacklist_campaign',
                                       amount=5)
```

### Unfollow

Unfollow profiles

- **amount** amount of profiles to be unfollowed

```python
session.unfollow_users(amount=5)
```

## Developers Documentation:

https://converge.github.io/InstaPy-Light

## Feedback

Feel free to send me feedbacks to joaovanzuita@me.com
