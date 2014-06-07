# known issues:
# Some submissions produce 'NoneType' object has no attribute '__getitem__'. 
# The bot currently just skips over those.
from sys import exit, stderr
from time import sleep
import praw
from requests import HTTPError


class trdbot(object):


    def __init__(self):
        """
        Initialize the bot with some basic info.
        """

        self.userAgent = "/r/MirrorNetwork xposting bot"

        # list of subreddits to crawl
        self.subredditList = set(["SubredditDrama"])

        # subreddit flairs
        self.flairList = {
                "SubredditDrama": "SRD", "Drama": "MILEY"
            }

        # list of threads already done
        self.alreadyDone = set()

        # post to this subreddit
        self.post_to = "redditanalysis"

        # scan no more than this number of threads
        self.scrapeLimit = 25


    def login(self, username, password):
        """
        Login to the bot's Reddit account. Give it the username
        and the password.
        """

        self.client = praw.Reddit(user_agent=self.userAgent)
        print "Logging in as %s..." % username

        self.client.login(username, password)
        print "Login was successful."


    def get_content(self, submission):
        """
        Gets data from the desired submission. Feed it the 
        submission. It returns a tuple containing the title,
        the post content, and the link to the source.
        """

        try:
            postID = submission.id
            subName = submission.subreddit
            postScore = submission.score
            title = submission.title
            permalink = submission.permalink.replace("www.reddit.com", "np.reddit.com")

        except AttributeError:
            raise Exception("Couldn't get submission attribute.")

        if postID not in self.alreadyDone:
            self.alreadyDone.add(postID)
            
            # only submit posts that have at least +5 karma
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

    try:
        trdBot.login(username, password)

    except (praw.errors.InvalidUser, praw.errors.InvalidUserPass, HTTPError) as e:
        print e
        logging.debug(str(e) + "\n\n")
        exit(1)

    while True:
        # keep the list from getting too big
        if len(trdBot.alreadyDone) >= 1000:
            for i, element in enumerate(trdBot.alreadyDone):
                if i < 900:
                    trdBot.alreadyDone.remove(element)

        for subreddit in trdBot.subredditList:
            try:
                submissions = trdBot.client.get_subreddit(subreddit).get_new(limit=trdBot.scrapeLimit)

            except HTTPError, e:
                print e
                logging.debug(str(e) + "\n\n")
                # wait a minute and try again
                sleep(60)
                continue

            except (praw.errors.APIException, Exception) as e:
                print e
                logging.debug(str(e) + "\n\n")
                continue

            for i, submission in enumerate(submissions):
                print "Scanning thread (%d / %d)..." % (i + 1, trdBot.scrapeLimit)

                try:
                    print "Getting content from submission..."
                    result = trdBot.get_content(submission)

                except HTTPError, e:
                    print e
                    logging.debug(str(e) + "\n\n")
                    sleep(60)
                    continue

                except praw.errors.APIException, e:
                    print e
                    logging.debug(str(e) + "\n\n")
                    continue

                try:
                    # concatenate elements from the 
                    # tuple to strings for submission
                    title = "".join(str(result[0]))
                    content = "".join(str(result[1]))
                    permalink = "".join(str(result[2]))

                except Exception, e:
                    print e
                    logging.debug(str(e) + "\n\n")
                    continue

                # try to submit the post 3 times before skipping
                for i in range(0, 2):
                    try:
                        print "Submitting post..."
                        if(submission.is_self):
                            post = trdBot.submit_selfpost(title, content)

                        else:
                            post = trdBot.submit_url(title, content)

                        print "Setting flair..."
                        trdBot.client.set_flair(trdBot.post_to, post, flair_text=trdBot.flairList[subreddit])

                        print "Adding source comment..."
                        post.add_comment("[Link to source](" + permalink + ").")
                        break

                    except HTTPError, e:
                        trdBot.retry += 1
                        print e
                        logging.debug(str(e) + "\n\n")
                        sleep(60)
                        continue

                    except (praw.errors.APIException, Exception) as e:
                        trdBot.retry += 1
                        print e
                        logging.debug(str(e) + "\n\n")
                        continue

                    except KeyboardInterrupt:
                        print "Skipping thread..."
                        break
