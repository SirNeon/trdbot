trdbot
=================

**For maintaining the source code of /u/TRDbot**

Requirements
------------
* Python 2.7
* Praw
* Requests

###Install Dependencies
In order to run the bot, you must install some necessary packages. To do so, run this command:

    pip install -r requirements.txt
    
Linux users may need to use:
    
    sudo pip install -r requirements.txt
    
Commandline Flags
-----------------

* **-p (--postHere)** *SubredditName* **(don't include "/r/") - Posts the results to this subreddit. Defaults to /r/TrueRedditDramaTest.** 

* **-v (--verbosity)** *on|off* **- Turn off extra terminal messages. Off by default.**

* **-u (--userCreds)** *username,password* **- Log the bot into this Reddit account.**
