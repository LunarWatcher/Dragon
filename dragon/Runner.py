import os
from sys import platform

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
QUESTION_FILTER = "!0WEuRgJEfkinT8j_w)24DURiZ"
# Filter for the /answers endpoint
ANSWER_FILTER   = "!nL_HTxMBi6"
# }}}
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

def processPost(post: Post):
    # Cache varaible to detect changes
    hasAltered: bool = False
    for filter in Filters.filters:
        result = filter(post)
        if result:
            hasAltered = True

    if hasAltered and checkQuestion(post):
        post.publishUpdates(SO, "Dragon::Supervised edit")

# Test code for editing
post = Post(SO.fetch("questions/68122810", filter = QUESTION_FILTER)["items"][0])
processPost(post)
