# Dragon

2k tool meant to automate editing on Stack Overflow, because there's too much crap to do it all manually.

**Disclaimer:** There's going to be false positives. All use of this tool is at your own risk.

## Requirements
* Python 3 (because there's few languages with good API interfaces, and C++ isn't one of them)
* Various dependencies: `pip3 install -r requirements.txt`
* 2k+ reputation on Stack Overflow (this tool actively blocks non-moderators with &lt;2k reputation to avoid review queue flooding)
* A terminal that supports colorama

## OAuth

Because Dragon requires write access, it has to use the client-side OAuth flow. It's set up to redirect to [a simple page](https://lunarwatcher.github.io/Dragon/token_echo.html) ([source code](https://github.com/LunarWatcher/Dragon/blob/master/docs/token_echo.html)) that echos and copies the token. The page itself doesn't save your token (or, as the page source also says, I don't save it. I have no idea if GitHub saves URLs for security purposes) - copy it, or it'll be lost

You can save this token into `.oauth.txt` manually, or paste it into the program when prompted. If you use Stack Overflow in a container tab in Firefox, the URL is also explicitly printed so it's copy-pastable. (reopening in the appropriate tab doesn't work - blame Stack Overflow for not following the redirect URL if you're already logged in)
