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
DRAGON_DEBUG = os.environ["DRAGON_DEBUG"] == "1"
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
SO = StackAPI('stackoverflow', access_token=oauthToken, key=API_TOKEN)
SO.page_size = 100

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
        # Skip posts that haven't been updated.
        # This should only be applicable to questions.
        # We may need to filter by the event type,
        # but that's a problem for later
        return
    # Cache varaible to detect changes
    hasAltered: bool = False
    for filter in Filters.filters:
        result = filter(post)
        if result != 0:
            hasAltered = True
            if DRAGON_DEBUG:
                print("Filter matched:", filter)

    #                 vvv ....            vvv makes sure the edit is semi-substantial.
    #                                         substantial being "meets the minimum requirement for suggested editors"
    #                                         though I think titles are exempt from that, but we'll require both to
    #                                         add up to over 6 changes. The diff engine should be able to detec this
    if hasAltered and countChanges(post) >= 6 and checkPost(post):
        response = post.publishUpdates(SO, "Dragon::Supervised edit (descriptions not implemented)")
        # If we get 0, there's no last activity field, meaning  there's probably an error
        if response != 0:
            idUpdateMap[post.postID] = response
        else:
            print("Failed to update")

def mainLoop():
    questions = []
    if len(argv) > 1:
        possible = argv[1:]

        for q in possible:
            try:
                questions.append(str(int(q)))
            except:
                continue

    # Primary loop
    # len(argv) == 1 is always true if there's no arguments supplied,
    # and false otherwise.
    # If it's false, we pop the questions array instead,
    # to get the next bit of the query.
    l = len(argv)
    while l == 1 or len(questions) > 0:
        # We search for questions
        # Test IDs can be inserted by appending /id1,id2,id3,... to the path.
        # Using questions instead of answers minimizes work
        baseRequest = SO.fetch("questions" + (("/" + (",".join(questions))) if len(questions) > 0 else ""), filter = QUESTION_FILTER)
        questions = []
        recentQuestions = baseRequest["items"]
        print("Remaining quota", baseRequest["quota_remaining"])
        # Then we process each question, which may or may not represent an update
        # to the question itself. We leave it up to the cache to determine what
        # needs a new sweep.
        for question in recentQuestions:
            if "closed_date" in question:
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
            for answer in question["answers"]:
                answerPost = Post(answer)
                processPost(answerPost)


mainLoop()
