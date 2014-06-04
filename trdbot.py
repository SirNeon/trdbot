# these imports are of bad style
# native modules get declared first
# don't use commas unless you're importing multiple
# things from ONE module
# 3rd party modules get declared last
import sqlite3
import praw
import sys, os
from time import sleep

# this is weird and might not work; why not use tuples in a list?
SUBREDDIT_PROFILE = {'subredditdrama': ['SRD', 10],
                   'drama': ['MILEY', 3]}
#insert a comma after each new penultimate line if you modify the above to have more subs.
#the number is the vote threshold for xposting. An SRD post must have 10 to trigger xposting.
print '  Logging in as Mirrorbot'
r = praw.Reddit(user_agent='/r/MirrorNetwork xposting bot instance')
r.login('username', 'password')

# I think doing all of this in multiple functions in a class
# would make it easier to maintain as well as add flexibility
def main():
    trd = r.get_subreddit('mirrornetworktest') #this is the subreddit it will POST INTO
    multireddit = r.get_subreddit('+'.join(SUBREDDIT_PROFILE.keys()))
    # why?
    path_to_db = os.path.abspath(os.path.dirname(sys.argv[0]))
    path_to_db = os.path.join(path_to_db, 'examplebot.db')
    con = sqlite3.connect(path_to_db)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    # check for new posts
    cur.execute("SELECT * FROM data WHERE type = 'last_submission'")
    row = cur.fetchone()
    last_submission = int(row['value'])
    new_last_submission = None
    print '  Checking for new drama submissions to cross-post'
#    for post in multireddit.get_new_by_date(limit=None):        ##commented out, outdated praw feature, changed below
    for post in multireddit.get_new(limit=100): #limit=None was scraping lots more than it needed to, this reduces CPU use.
        # passing these absurdly long names to variable to conserve
        # space would be nice
        if int(post.created_utc) <= last_submission or post.score < SUBREDDIT_PROFILE[post.subreddit.display_name.lower()][1]:
            break
        try:
            #print '  Cross-posting "{0}" from /r/{1}'.format(post.title, post.subreddit.display_name).encode('ascii', 'ignore')
            if (post.is_self):
                submission = trd.submit(title=post.title, text=post.selftext.replace('np.reddit.com', 'www.reddit.com'))
            else:
                submission = trd.submit(title=post.title, url=post.url.replace('np.reddit.com', 'www.reddit.com'))
            if not new_last_submission:
                new_last_submission = int(post.created_utc)
                # for what this bot does it probably won't matter,
                # but this is vulnerable to SQLInjection I think
                # unless format() is different from %s
                cur.execute("UPDATE data "
                            "SET value = '{0}' "
                            "WHERE type = 'last_submission'".format(new_last_submission))
                con.commit()
            submission.set_flair('[{0}]'.format(SUBREDDIT_PROFILE[post.subreddit.display_name.lower()][0]))
            submission.add_comment('[Comments in source subreddit]({0})'.format(post.permalink))
        # could use more HTTPError handling
        except praw.errors.APIException:
            pass
if __name__ == '__main__':
     while 1:
        try:
            # wat; one infinite loop is enough
            while 1:
                # one try/except should be enough as well
                try:
                    main()
                    print 'try...sleeping...'
                    sleep(60)
                except Exception, e:
                    print str(e)
                    print 'exception...retrying...'
                    main()
                    print 'except...sleeping...'
                    sleep(60)
        except Exception, e:
            print str(e)
            # yet another? These will prevent the first loop from
            # iterating, so it may as well not exist
            while 1:
                print 'MAJOR exception...retrying...'
                main()
                print 'MAJOR except...sleeping...'
                sleep(60)
#this try/except thing is my own, but i have NO IDEA what im doing. It still crashed and terminates despite the except/retry thing. Any ideas?
