import os
from sys import platform

import html

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
API_FILTER = "!nL_HTxMBi6"
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
print("OAuth token loaded. Assuming valid...")
SO = StackAPI('meta', access_token=oauthToken, key=API_TOKEN)
SO.page_size = 100

# }}}
# Utility API {{{

def cleanHTMLEntities(rawString: str):
    return html.unescape(rawString)

def edit(answerID, newBody, comment):
    SO.send_data("answers/{}/edit".format(answerID), body=newBody, comment=comment)

def getAnswers(page = 1):
    return SO.fetch("answers", page=page, filter=API_FILTER)

# }}}
# Test code for editing
# body = html.unescape(SO.fetch("answers/364602", filter=API_FILTER)["items"][0]["body_markdown"])
# body += "\n\nThis is an edit from the API"
# print(body)
# SO.send_data("answers/364602/edit", body=body, comment="Testing API edits")

