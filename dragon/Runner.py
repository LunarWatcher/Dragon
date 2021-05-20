import os

import StackAPI

# Static {{{
CLIENT_ID = "20280"
# This token isn't considered a secret by the API
API_TOKEN = "qXwVVNIDCIX7LpUEoDHIpA(("

OAUTH_VERIFICATION_URL = "https://lunarwatcher.github.io/Dragon/token_echo.html"
# }}}

# Token management {{{
oauthToken = ""

if !os.path.isfile(".oauth.txt"):
    pass
else:
    with open(".oauth.txt", "r") as f:
        oauthToken = f.readlines()[0]

if (oauthToken == ""):
    print("Failed to find a token")
    exit(-2)
# }}}
# Token verification {{{
print("OAuth token loaded. Testing a dry run against the API...")

oauthURL = f"https://stackoverflow.com/oauth?client_id={CLIENT_ID}"

# }}}

