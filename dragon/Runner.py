#!/usr/bin/python3
import os
from sys import platform, argv

import html
import re

import Filters
import Utils

from ManualMode import *
from Post import *

from stackapi import StackAPI

# Static validation {{{
if platform != "linux":
    print(platform, "isn't supported")
    exit(-1)
# }}}
# Static {{{
CLIENT_ID = "20280"
# This token isn't considered a secret by the API
API_TOKEN = "qXwVVNIDCIX7LpUEoDHIpA(("

OAUTH_VERIFICATION_URL = "https://lunarwatcher.github.io/Dragon/token_echo.html"
# Endpoint filters {{{
# Filter for the /questions endpoint
QUESTION_FILTER = "!3xr(P-20tB)GfFE5r"
# }}}
# }}}
# User interface {{{
DRAGON_DEBUG = False if "DRAGON_DEBUG" not in os.environ else os.environ["DRAGON_DEBUG"] == "1"
# }}}
# Token management {{{
oauthToken = ""

if not os.path.isfile(".oauth.txt"):
    oauthURL = f"https://stackoverflow.com/oauth/dialog?client_id={CLIENT_ID}&scope=write_access,no_expiry&redirect_uri={OAUTH_VERIFICATION_URL}"
    print("Opening", oauthURL)
    oauthURL = oauthURL.replace("&", "\&")
    os.system(f"xdg-open {oauthURL}")
    print("Client-side OAuth flow launched")
    oauthToken = input("Paste your token here: ")
    with open(".oauth.txt", "w") as f:
        f.write(oauthToken)

else:
    with open(".oauth.txt", "r") as f:
        oauthToken = f.readlines()[0]

if (oauthToken == ""):
    print("Failed to find a token")
    exit(-2)
# }}}
# Init API interface {{{
print("OAuth token loaded.")
SO = StackAPI('stackoverflow', access_token=oauthToken, key=API_TOKEN, version="2.3")
SO.page_size = 100
SO.max_pages = 1

# User validation {{{
user = SO.fetch("me")["items"][0]
# This 2k requirement blocks access for editing on beta sites or sites where the privilege for whatever
# reason isn't earned at 2k, but at some other milestone.
# The editing privilege is to make sure the review queues aren't flooded with automated edits that
# may or may not be very, very minor.
# Also, accounting for <2k users means there have to be additional checks to make sure
# the edit is big enough to be allowed.
if (user["reputation"] < 2000 and user["is_employee"] == False and user["user_type"] != "moderator"):
    print("You don't have enough reputation to use this tool - 2k is required.")
    exit(-1)
elif user["user_type"] not in ["registered", "moderator"]:
    print("This tool doesn't allow unregistered users.")
    exit(-1)
# }}}

# }}}
# Cache management {{{
idUpdateMap = {}

def hasPostBeenUpdated(post: Post):
    if post.postID not in idUpdateMap:
        return True
    # If the post has been updated more recently than what we have stored,
    # return true.
    # Then, and only then, will the post be checked
    return idUpdateMap[post.postID] > post.lastUpdate

# }}}

def processPost(post: Post):
    if not hasPostBeenUpdated(post):
        # We don't wanna re-check posts that haven't been updated since the last time
        # Dragon edited it.
        # Note that this is limited to each session.
        #
        # This is necessary for when we eventually implement proper paging, and actually
        # burn through entire pages.
        # A post on page 1 or 2 could recur on a later page, and we want to skip those.
        # This largely saves time on regex processing, which may or may not slow down
        # as the regex stack grows.
        # So to avoid unnecessary work, we don't process posts we know haven't changed.
        # Might be a good idea to make the update list persistent.
        return
    for filter in Filters.filters:
        result = filter(post)
        if result != 0 and DRAGON_DEBUG:
            # We only use the count for checking if the filter matches for the time being.
            print("Filter matched:", filter)

    #                 vvv ....            vvv makes sure the edit is semi-substantial.
    #                                         substantial being "meets the minimum requirement for suggested editors"
    #                                         though I think titles are exempt from that, but we'll require both to
    #                                         add up to over 6 changes. The diff engine should be able to detect this
    if countChanges(post) >= 6 and checkPost(post):
        response = post.publishUpdates(SO, post.generateEditSummary())
        # If we get 0, there's no last activity field, meaning  there's probably an error
        if type(response) is Post:
            if response.count > 1:
                # Avoid StackOverflowException and useless API calls
                print("Update failed: two sequential conflicts.")
                return
            processPost(response)
            return # Future-proofing
        elif response != 0:
            idUpdateMap[post.postID] = response
        else:
            print("Failed to update")
    elif DRAGON_DEBUG:
        print("Post https://stackoverflow.com/q/{} not approved, or not enough changes.".format(post.postID))
        print()

def processQuestions(questions):
    # Primary loop
    # len(argv) == 1 is always true if there's no arguments supplied,
    # and false otherwise.
    # If it's false, we pop the questions array instead,
    # to get the next bit of the query.
    l = len(argv)
    page = 2
    alt = False
    while l == 1 or len(questions) > 0:
        # We search for questions
        # Test IDs can be inserted by appending /id1,id2,id3,... to the path.
        # Using questions instead of answers minimizes work
        baseRequest = SO.fetch("questions" + (("/" + (";".join(questions))) if len(questions) > 0 else ""), page if alt else 1, filter = QUESTION_FILTER)
        if alt:
            page += 1
        alt = not alt
        questions = []
        recentQuestions = baseRequest["items"]
        print("Remaining quota", baseRequest["quota_remaining"])
        # Then we process each question, which may or may not represent an update
        # to the question itself. We leave it up to the cache to determine what
        # needs a new sweep.
        for question in recentQuestions:
            #                            vvv Allow closed edits if we're supplying the IDs.
            #                                These are fine because we may wanna edit them.
            #                                This is largely defensible from a debug POV.
            if "closed_date" in question and l == 1:
                # Skip closed questions; editing these are unnecessary
                # Also causes unnecessary bumping. Might as well try
                # to reduce what we edit at least a little.
                continue
            elif "locked_date" in question:
                # We cannot edit locked posts, so it's not a question of
                # whether bumping is worth it or not.
                continue
            # Convert to a post
            questionPost = Post(question)
            # Then we check the question
            processPost(questionPost)

            # The answers key isn't present if there are no answers.
            if question["answer_count"] == 0:
                # So if the answer count is 0, we continue the loop
                continue

            # Otherwise, we also scan the answers.
            #                      vvvvvvvvv this being the answer key, if that wasn't obvious
            for answer in question["answers"]:
                answerPost = Post(answer)
                processPost(answerPost)

def mainLoop():
    questions = []
    command = ""
    if len(argv) > 1:
        command = argv[1]
        possible = argv[2:]

        if command == "search":
            print("Running search mode")
        elif command == "target":
            print("Running target mode")
            for q in possible:
                try:
                    questions.append(str(int(q)))
                except:
                    continue
        elif command == "help":
            print("The valid commands are: search, target")
            exit(0)
        else:
            print("No such command: {}".format(command))
            exit(0)
    if command == "":
        processQuestions([])
    elif command == "target":
        processQuestions(questions)
    elif command == "search":
        args = {b[0]: b[1] for b in [ a.split("=") for a in argv[2:] ]}
        while True:
            questions.clear()
            # Search loop
            print(args)
            posts = SO.fetch("search/excerpts", 1, **args)["items"]
            print(len(posts))
            questions = [str(a["question_id"]) for a in posts]
            print("Search returned: {}".format(len(questions)))
            if len(questions) == 0:
                break

            processQuestions(questions)

mainLoop()
