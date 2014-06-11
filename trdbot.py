import logging
from sys import exit, stderr
from time import sleep
import praw
from praw.errors import *
from urllib2 import HTTPError


class trdbot(object):


    def __init__(self):
        """
        Initialize the bot with some basic info.
        """

        self.userAgent = "/r/TrueRedditDrama xposting bot by /u/SirNeon"

        # list of subreddits to crawl
        self.subredditList = set([
                    "SubredditDrama", "SubredditDramaDrama", 
                    "Drama",
                ])

        # subreddit flairs
        self.flairList = {
                "SubredditDrama": "SRD", 
                "SubredditDramaDrama": "SRDD", "Drama": "Drama", 
            }

        # list of threads already done
        self.alreadyDone = set()

        # post to this subreddit
        self.post_to = "trueredditdramatest"

        # scan no more than this number of threads
        self.scrapeLimit = 25


    def login(self, username, password):
        """
        Login to the bot's Reddit account. Give it the username
        and the password.
        """

        self.client = praw.Reddit(user_agent=self.userAgent)
        print "Logging in as {0}...".format(username)

        self.client.login(username, password)
        print "Login was successful."


    def get_content(self, submission):
        """
        Gets data from the desired submission. Feed it the 
        submission. It returns a tuple containing the title,
        the post content, and the link to the source.
        """

        try:
            subName = submission.subreddit
            title = submission.title
            postScore = submission.score
            permalink = submission.permalink.replace("www.reddit.com", "np.reddit.com")

        except AttributeError:
            raise Exception("Couldn't get submission attribute.")

        if postScore >= 5:
            if(submission.is_self):
                try:
                    postBody = submission.selftext

                except AttributeError:
                    raise Exception("Couldn't get submission text. Skipping...")

                text = postBody.replace("www.reddit.com", "np.reddit.com")

                return (title, text, permalink)

            else:
                url = submission.url.replace("www.reddit.com", "np.reddit.com")

            return (title, url, permalink)

        else:
            print "Thread karma beneath necessary threshold."
            return None


    def submit_url(self, title, url):
        """
        Submits a link post to Reddit. Feed it the post title 
        and the url. It returns the submission object.
        """

        mySubreddit = self.client.get_subreddit(self.post_to)

        return mySubreddit.submit(title=title, url=url)


    def submit_selfpost(self, title, text):
        """
        Submits the self post to reddit. Feed it the post 
        title and post content. It returns the submission object.
        """

        mySubreddit = self.client.get_subreddit(self.post_to)

        return mySubreddit.submit(title=title, text=text)


if __name__ == "__main__":
    trdBot = trdbot()

    # set this to False to turn off error logging
    # doing so is not recommended
    errorLogging = True

    if(errorLogging):
        logging.basicConfig(
            filename="trdbot_logerr.log", filemode='a', 
            format="%(asctime)s\nIn %(filename)s "
            "(%(funcName)s:%(lineno)s): %(message)s", 
            datefmt="%Y-%m-%d %H:%M:%S", level=logging.DEBUG, 
            stream=stderr
            )

    username = ""
    password = ""

    for i in range(0, 3):
        try:
            trdBot.login(username, password)
            break

        except (InvalidUser, InvalidUserPass, RateLimitExceeded, NonExistentUser, APIException) as e:
            print e
            logging.debug("Failed to login. " + str(e) + "\n\n")
            exit(1)

        except HTTPError, e:
            print e
            logging.debug(str(e) + "\n\n")

            if i == 2:
                print "Failed to login."
                exit(1)

            else:
                # wait a minute and try again
                sleep(60)
                continue

    while True:
        # keep the list from getting too big
        if len(trdBot.alreadyDone) >= 1000:
            for i, element in enumerate(trdBot.alreadyDone):
                if i < 900:
                    trdBot.alreadyDone.remove(element)

        for subreddit in trdBot.subredditList:
            print "Scanning /r/{0}...".format(subreddit)

            try:
                submissions = trdBot.client.get_subreddit(subreddit).get_new(limit=trdBot.scrapeLimit)

            except InvalidSubreddit, e:
                print e
                logging.debug("Invalid subreddit. Removing from list." + str(e) + "\n\n")
                trdBot.subredditList.remove(subreddit)
                continue

            except HTTPError, e:
                print e
                logging.debug(str(e) + "\n\n")
                sleep(60)
                continue

            except (APIException, ClientException, Exception) as e:
                print e
                logging.debug(str(e) + "\n\n")
                continue

            for i, submission in enumerate(submissions):
                print "Scanning thread ({0} / {1})...".format(i + 1, trdBot.scrapeLimit)

                try:
                    postID = submission.id

                except AttributeError:
                    print "Failed to get submission ID. Skipping..."
                    continue

                try:
                    if postID not in trdBot.alreadyDone:
                        print "Getting content from submission..."
                        result = trdBot.get_content(submission)

                except HTTPError, e:
                    print e
                    logging.debug(str(e) + "\n\n")
                    sleep(60)
                    continue

                except (APIException, ClientException, Exception) as e:
                    print e
                    logging.debug(str(e) + "\n\n")
                    continue

                try:
                    if result != None:
                        # concatenate elements from the 
                        # tuple to strings for submission
                        title = "".join(str(result[0]))
                        content = "".join(str(result[1]))
                        permalink = "".join(str(result[2]))

                    else:
                        continue

                except Exception, e:
                    print e
                    logging.debug(str(e) + "\n\n")
                    continue

                # try to submit the post 3 times before skipping
                for i in range(0, 3):
                    try:
                        if postID not in trdBot.alreadyDone:
                            print "Submitting post..."
                            if(submission.is_self):
                                post = trdBot.submit_selfpost(title, content)

                            else:
                                post = trdBot.submit_url(title, content)

                            trdBot.alreadyDone.add(postID)

                        try:
                            print "Setting flair..."
                            trdBot.client.set_flair(trdBot.post_to, post, flair_text=trdBot.flairList[subreddit])

                        except (APIException, ModeratorRequired) as e:
                            print e
                            logging.debug("Failed to set flair. " + str(e) + '\n' + str(post.permalink) + "\n\n")

                        print "Adding source comment..."
                        post.add_comment("[Link to source](" + permalink + ").")
                        break

                    except HTTPError, e:
                        print e
                        logging.debug(str(e) + "\n\n")
                        sleep(60)
                        continue

                    except (APIException, ClientException, Exception) as e:
                        print e
                        logging.debug(str(e) + "\n\n")

                        if str(e) == "`that link has already been submitted` on field `url`":
                            trdBot.alreadyDone.add(postID)
                            break
                        
                        else:
                            continue
