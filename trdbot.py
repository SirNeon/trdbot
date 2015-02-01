from __future__ import print_function
import os
import re
from socket import timeout
import sqlite3 as db
from sys import exit
from time import sleep
import praw
from praw.errors import *
from requests.exceptions import HTTPError
from simpleconfigparser import simpleconfigparser


config = simpleconfigparser()

if not(os.path.isfile("settings.cfg")):
    print("Couldn't find settings.cfg. Exiting.")
    exit(1)
else:
    config.read("settings.cfg")

con = db.connect("alreadydone.db")
cur = con.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS submissions(permalink TEXT)")

client = praw.Reddit(user_agent="/r/TrueRedditDrama xposting bot by /u/SirNeon")

USERNAME = str(config.login.username)
PASSWORD = str(config.login.password)
SUBREDDIT_LIST = list(set(str(config.main.subreddits).split(',')))

SRD_MINIMUM_KARMA = int(config.main.srd_minimum_karma)
SRDD_MINIMUM_KARMA = int(config.main.srdd_minimum_karma)
DRAMA_MINIMUM_KARMA = int(config.main.drama_minimum_karma)
MINIMUM_KARMA = {"Drama": DRAMA_MINIMUM_KARMA, "SubredditDrama": SRD_MINIMUM_KARMA,
                 "SubredditDramaDrama": SRDD_MINIMUM_KARMA}

REDDIT_URL_PATTERN = re.compile("https?:\/\/[\w.]+reddit\.com\/r\/[\w\d_]+\/[\w\d.-_/]+")
POST_TO = str(config.main.post_to)
SUBREDDIT_FLAIR = {"SubredditDrama": "SRD", "SubredditDramaDrama": "SRDD", "Drama": "Drama"}


def login(username, password):
    print("Logging in as {}...".format(username))
    while True:
        try:
            client.login(username, password)
            break
        except (HTTPError, timeout) as e:
            continue
        except (InvalidUser, InvalidUserPass) as e:
            print(e)
            exit(1)


def get_submissions(multireddit):
    while True:
        try:
            submissions = client.get_subreddit(multireddit).get_new(limit=50)
            break
        except (HTTPError, timeout) as e:
            continue

    return submissions


def remove_noparticipation(content):
    if "np.reddit.com" in content:
        content = content.replace("np.reddit.com", "www.reddit.com")

    if "www.np.reddit.com" in content:
        content = content.replace("www.np.reddit.com", "www.reddit.com")

    return content


def get_drama(submission):
    try:
        subreddit = str(submission.subreddit)
        karma = int(submission.score)
        title = str(submission.title)
        permalink = str(submission.permalink)
    except AttributeError:
        return None

    cur.execute("SELECT * FROM submissions WHERE permalink=?", (permalink,))

    if cur.fetchone() is not None:
        return None

    if(karma >= MINIMUM_KARMA[subreddit]):
        cur.execute("INSERT INTO submissions VALUES(?)", (permalink,))

        if(submission.is_self):
            try:
                text = str(submission.selftext)
            except AttributeError:
                return None

            reddit_urls = REDDIT_URL_PATTERN.findall(text)

            if reddit_urls == []:
                return None

            text = remove_noparticipation(text)

            return ("self", subreddit, title, text, permalink)

        else:
            try:
                url = str(submission.url)
            except AttributeError:
                return None

            reddit_url = REDDIT_URL_PATTERN.match(text)

            if reddit_url is None:
                return None

            url = remove_noparticipation(url)

            return ("link", subreddit, title, url, permalink)

    else:
        return None


def submit_linkpost(title, url):
    while True:
        try:
            subreddit = client.get_subreddit(POST_TO)
            post = subreddit.submit(title=title, url=url)
            break
        except (HTTPError, timeout):
            continue

    return post


def submit_selfpost(title, text):
    while True:
        try:
            subreddit = client.get_subreddit(POST_TO)
            post = subreddit.submit(title=title, text=text)
            break
        except (HTTPError, timeout):
            continue

    return post


def set_flair(subreddit, submission):
    while True:
        try:
            submission.set_flair(POST_TO, submission, flair_text=SUBREDDIT_FLAIR[subreddit])
            break
        except (HTTPError, timeout):
            continue


def link_source(submission, permalink):
    while True:
        try:
            submission.add_comment("[source]({}).".format(permalink))
            break
        except (HTTPError, timeout):
            continue


def main():
    multireddit = ""
    for subreddit in SUBREDDIT_LIST:
        multireddit += subreddit + '+'

    multreddit = multireddit.strip('+')

    while True:
        login(USERNAME, PASSWORD)
        submissions = get_submissions(multireddit)
        for submission in submissions:
            post = get_drama(submissions)

            if post is None:
                continue

            submission_type = post[0]
            submission_source_subreddit = post[1]
            submission_title = post[2]
            submission_content = post[3]
            submission_source = post[4]

            if(submission_type == "link"):
                post = submit_linkpost(submission_title, submission_content)

            if(submission_type == "self"):
                post = submit_selfpost(submission_title, submission_content)

            set_flair(submission_source_subreddit, post)
            link_source(post, submission_source)

        sleep(60)


if __name__ == "__main__":
    main()
