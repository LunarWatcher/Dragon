from stackapi import StackAPI

import regex as re
import random
import os

import Utils

randomNameCoefficient = str(random.randint(-1e6, 1e6))

# We introduce a tiny bit of randomness into the placeholders to reduce the probability of a false positive, i.e.
# anything related to the presence of this explicitly written in the post.
# Not that it's gonna be a common problem, but it's a problem I don't wanna have to think about.

# And because it's just adding a bit of randomness, it's unnecessary to generate a number for each of these.
# That's why a single random number is used for all the placeholders.
PLACEHOLDER_CODEBLOCK = "__dragonCodeBlockPlaceholder{}__".format(randomNameCoefficient)
PLACEHOLDER_LINK = "__dragonURLPlaceholder{}__".format(randomNameCoefficient)
PLACEHOLDER_INLINE_CODE = "__dragonInlineCodePlaceholder{}__".format(randomNameCoefficient)

# Contains various fields used to deal with weird API requirements,
# as well as to provide diffs where needed.
class Post():

    def __init__(self, apiResponse):
        self.placeholders = {
            # I fucking hate this.
            # C++ has spoiled me
            PLACEHOLDER_CODEBLOCK: [],
            PLACEHOLDER_LINK: []
        }

        # TODO: parse out the user
        self.postType = "answer_count" in apiResponse
        self.postID = apiResponse["question_id" if self.postType else "answer_id"]

        self.rawOldBody = Utils.cleanHTMLEntities(apiResponse["body_markdown"])
        self.oldBody = self.stripBody(self.rawOldBody)
        self.body = self.oldBody

        if self.postType:
            # Parse out titles and tags
            self.tags = apiResponse["tags"]
            self.title = Utils.cleanHTMLEntities(apiResponse["title"])

        else:
            self.tags = None
            self.title = None

        # Could've probably set these in the opposite order, but here we are
        self.oldTags = self.tags
        self.oldTitle = self.title

        self.lastUpdate = apiResponse["last_activity_date"]

        self.unpacked = False


    def isQuestion(self):
        return self.postType

    def publishUpdates(self, api: StackAPI, comment: str):
        self.unpackBody()

        print("Updating post...")
        if self.isQuestion():
            # We have a question
            resp = api.send_data("questions/{}/edit".format(self.postID),
                body = self.body, title = self.title, tags = ",".join(self.tags),
                comment = comment)
        else:
            resp = api.send_data("answers/{}/edit".format(self.postID),
                body = self.body, comment = comment)
        print(resp)
        if "last_activity_date" in resp:
            return resp["last_activity_date"]
        else:
            print(resp)
            pass
        return 0

    def stripBody(self, body: str):
        def onBlock(pat):
            self.placeholders[PLACEHOLDER_CODEBLOCK].append(pat.group(2))
            return pat.group(1) + PLACEHOLDER_CODEBLOCK + pat.group(3)

        def onBlockSpace(pat):
            self.placeholders[PLACEHOLDER_CODEBLOCK].append(pat.group(1))
            return PLACEHOLDER_CODEBLOCK

        def onLink(pat):
            self.placeholders[PLACEHOLDER_LINK].append(pat.group(0))
            return PLACEHOLDER_LINK

        # We wanna remove certain bits to make sure they don't interfere with other parts of the code.

        # Code blocks ignore quotes. These are handled separately.
        body = re.sub("(^```[^`]*?$\n)((?:.*?\n)+?)(^```$)", onBlock, body, flags = re.MULTILINE)
        body = re.sub("(^<code>$\n)((?:.*?\n)+?)(^</code>$)", onBlock, body, flags = re.MULTILINE)
        # This one has to be substantially more greedy
        body = re.sub("((?:^\s{4,}.*?(?:\n|$))+)", onBlockSpace, body, flags = re.MULTILINE)

        # And links
        body = re.sub(r"(?i)!?\[[^\]\n]+\](?:\([^\)\n]+\)|\[[^\]\n]+\])(?:\](?:\([^\)\n]+\)|\[[^\]\n]+\]))?|(?:/\w+/|.:\\|\w*://|\.+/[./\w\d]+|(?:\w+\.\w+){2,})[./\w\d:/?#\[\]@!$&'()*+,;=\-~%]*",
            onLink, body, flags = re.MULTILINE)
        body = re.sub(r"(?:^ *(?:[\r\n]|\r\n))?(?:  (?:\[\d\]): \w*:+\/\/.*\n*)+", onLink, body, flags = re.MULTILINE)
        return body

    def unpackBody(self):
        if self.unpacked:
            return
        # Iterate the placeholder type and the blocks replaced
        for placeholderKey, blocks in self.placeholders.items():
            # Then iterate for each substitution
            for repl in blocks:
                # And replace the first placeholder with the key.
                # Thanks to lists being linear containers, order is preserved.
                self.body = self.body.replace(placeholderKey, repl, 1)

        # Prevent several unpacks.
        # Purely used because we also unpack before we publish, which we do because we want to make sure
        # automatic edits are allowed to pass through without needing interference.
        self.unpacked = True

    # Browser access {{{
    def open(self):
        os.system(f"xdg-open https://stackoverflow.com/q/{self.postID}")

    def edit(self):
        os.system(f"xdg-open https://stackoverflow.com/posts/{self.postID}/edit")

    # }}}
