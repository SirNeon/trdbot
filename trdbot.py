# fixed bad style and added stuff for new features
from datetime import datetime
import logging
from sys import exit, stderr
from time import sleep
import praw
from requests import HTTPError


# make it a class to improve maintainability and flexibility
class trdbot(object):


    def __init__(self):
        """
        Initialize the bot with some basic info.
        """

        # optional logging
        self.errorLogging = True

        self.userAgent = "/r/MirrorNetwork xposting bot"

        # list of subreddits to crawl
        self.subredditList = set(["SubredditDrama", "Drama"])

        # subreddit flairs
        self.flairList = [
                {"subredditdrama": "SRD"}, {"drama": "MILEY"}
            ]

        # list of stuff already done
        self.alreadyDone = set()

        # post to this subreddit
        self.post_to = "mirrornetworktest"

        # scrape no more than this number of threads
        self.scrapLimit = 25


    def login(self, username, password):
        """
        Login to the bot's Reddit account. Give it the username
        and the password.
        """

        self.client = praw.Reddit(user_agent=self.userAgent)
        print "Logging in as %s..." % username

        self.client.login(username, password)
        print "Login was successful."


    def check_new(self, submissionID):
        """
        Checks if a submission has already been posted. Give
        it the submission's ID.
        """

        if submissionID in self.alreadyDone:
            return False

        else:
            return True


    def check_post(self, submission):
        """
        Checks to see if the submission meets the necessary
        criteria to be posted.
        """

        try:
            subName = submission.subreddit.lower()
            subScore = submission.score 

        except AttributeError:
            print "Failed to collect necessary data."
            return False

        # SRD threads need at least +10 karma
        if subName == "subredditdrama":
            if subScore >= 10:
                return True

        # Drama threads need at least +3 karma
        elif subName == "drama":
            if subScore >= 3:
                return True

        # everything else needs at least +7 karma
        else:
            if subScore >= 7:
                return True

        return False


    def submit_content(self, submission):
        """
        This will submit the post to Reddit. Give it a tuple with
        the post title and then post body in it.
        """

        title = submission.title

        if(submission.is_self):
            # swap out normal reddit links for np links
            text = submission.selftext.replace("www.reddit.com", "np.reddit.com")

        else:
            text = submission.url.replace("www.reddit.com", "np.reddit.com")

        mySubreddit = self.client.get_subreddit(self.post_to)

        mySubreddit.submit(title, text)


    def log_err(self, error):
        """
        This is for logging errors.
        """

        if(self.errorLogging):
            logging.basicConfig(
                filename="trdbot_logerr.log", filemode='a', 
                format="%(asctime)s\nIn %(filename)s "
                "(%(funcName)s:%(lineno)s): %(message)s", 
                datefmt="%Y-%m-%d %H:%M", level=logging.DEBUG, 
                stream=stderr
            )
            
            logging.debug(str(error) + "\n\n")


if __name__ == "__main__":
    myBot = trdbot()

    username = ""
    password = ""

    # set this to False to turn off logging
    # I don't recommend that though
    myBot.errorLogging = True

    try:
        myBot.login(username, password)

    except (praw.errors.InvalidUser, praw.errors.InvalidUserPass, HTTPError) as e:
        print e
        myBot.log_err(e)
        exit(1)

    while True:
        # keep the list from getting too big
        if len(myBot.alreadyDone) == 1000:
            for i, element in enumerate(myBot.alreadyDone):
                if i < 900:
                    myBot.alreadyDone.remove(element)

        try:
            # iterate through the list of subreddits to scan
            for subreddit in myBot.subredditList:
                # scan the new queue
                submissions = myBot.client.get_subreddit(subreddit).get_new(limit=myBot.scrapLimit)

                for i, submission in enumerate(submissions):
                    try:
                        print "Scanning thread (%d / %d)..." % (i + 1, myBot.scrapLimit)
                        # make sure the bot hasn't already done
                        # this thread before
                        newPost = myBot.check_new(submission.id)
                        
                        # get the name of the sub where the
                        # thread was posted to originally
                        subName = submission.subreddit.lower()

                    except AttributeError:
                        continue

                    if(newPost):
                        print "Checking if post is worthy..."
                        # make sure the post meets the criteria
                        # necessary to xpost it
                        goodPost = self.check_post(submission)

                    if(goodPost):
                        myBot.alreadyDone.add(submission.id)

                        # keep trying to submit the post until
                        # either it's successful or you get an 
                        # error besides HTTPError
                        while True:
                            try:
                                print "Submitting thread..."
                                post = myBot.submit_content(submission)
                                break

                            except HTTPError, e:
                                print str(e) + "Sleeping...trying again..."
                                myBot.log_err(e)
                                sleep(60)

                            # keyboard interrupt will skip post 
                            # instead of killing the bot
                            except KeyboardInterrupt:
                                print "Skipping post..."
                                break

                            except Exception, e:
                                print str(e) + "Skipping thread..."
                                myBot.log_err(e)
                                break

                    if(post):
                        # try to assign flair 3 times
                        # could have it try more, but that
                        # doesn't seem worth the time
                        for i in range(0, 2):
                            try:
                                print "Setting flair..."
                                post.set_flair(myBot.flairList[subName])
                                print "Adding link to source..."
                                post.add_comment("[Comments in source subreddit](%s)", submission.permalink)
                                break

                            except HTTPError, e:
                                print str(e) + "Sleeping... trying again..."
                                sleep(60)
                                continue

                            except KeyboardInterrupt:
                                print "Skipping flair/commenting..."
                                break

                            except Exception, e:
                                print str(e) + "Skipping..."
                                sleep(60)
                                break

        except (HTTPError, Exception) as e:
            print str(e) + "Sleeping... trying again..."
            myBot.log_err(e)
            sleep(60)
            continue
