

# Contents

* [Introduction](#introduction-and-initial-setup)
* [Installation](#installation)
  * [Install on MacOS](#install-on-macos)
* [Features](#features)
  * [Like By Tags](#like-by-tags)
  * [Follow Competitors Followers](#follow-competitors-followers)
  * [Blacklist](#blacklist)
  * [Unfollow by Blacklist Campaign](#unfollow-by-blacklist-campaign)
  * [Unfollow](#unfollow)
  * [Save Screenshot](#save-screenshot)
* [Developers documentation](#developers-documentation)
* [Feedback](#feedback)
* [Keep The Project Alive](#keep-the-project-alive)

## Introduction and initial setup

InstaPy-Light is a light version of InstaPy. The main goal is to have a minimalistic approach over InstaPy, beeing easier to setup and use, including basic features.

## Installation

InstaPy-Light uses only Firefox and Geckodriver as default browser and driver.

The basics steps to install in any operational system is:

1) install firefox
2) install geckodriver
3) git clone the project or download it using the zip file
4) pip3 install requests selenium pyvirtualdisplay

### Install On MacOS

Video tutorial in Brazilian Portuguese:

<a href="http://www.youtube.com/watch?feature=player_embedded&v=h9svDhveps8" target="_blank"><img src="http://img.youtube.com/vi/h9svDhveps8/0.jpg"
alt="IMAGE ALT TEXT HERE" width="240" height="180" border="10" /></a>

### Setup your Instagram account

<img src="https://media.giphy.com/media/klwq5Nnl7riXxIvOoH/giphy.gif">

## Features

### Like By Tags

- **tags** a list of tags to be used to like posts
- **amount** the amount of posts you would like to like

**example:**

```python
tags = ['johnassaraf', 'lawofattraction']
session.like_by_tags(tags, amount=3)
```

Every tag will be liked n(amount) times.

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

### Save Screenshot

This is useful when you´re running it in a server and don´t have access to the
screen of the browser. If some error was raised, you can see the last screen to
be able to check what could be wrong.

- **filename** file name to be saved in the root folder of InstaPy-Light
```python
session.save_screenshot(filename='image.png')
```

## Developers Documentation:

https://converge.github.io/InstaPy-Light

## Feedback

Feel free to send me feedbacks to joaovanzuita@me.com

## Keep The Project Alive

[Donate any value using Paypal](https://www.paypal.me/joaovanzuita?ppid=PPC000628&cnac=BR&rsta=en_BR%28en_AR%29&cust=Z8V4LFWNLXJ5S&unptid=9a9fa222-b75f-11e8-822d-441ea1470e54&t=&cal=62f3404cebe63&calc=62f3404cebe63&calf=62f3404cebe63&unp_tpcid=ppme-social-user-profile-created&page=main:email&pgrp=main:email&e=op&mchn=em&s=ci&mail=sys)
