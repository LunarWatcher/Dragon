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
PLACEHOLDER_CODE_BLOCK = "__dragonCodeBlock{{}}Placeholder{}__".format(randomNameCoefficient)
PLACEHOLDER_LINK = "__dragonURL{{}}Placeholder{}__".format(randomNameCoefficient)
PLACEHOLDER_INLINE_CODE = "__dragonInlineCode{{}}Placeholder{}__".format(randomNameCoefficient)
PLACEHOLDER_HTML_COMMENT = "___dragonHTMLComment{{}}Placeholder{}__".format(randomNameCoefficient)

# Contains various fields used to deal with weird API requirements,
# as well as to provide diffs where needed.
class Post():

    def __init__(self, apiResponse):
        self.placeholders = {
            # I fucking hate this.
            # C++ has spoiled me with lists that default-initialize themselves.
            # Fucking fantastic feature
            PLACEHOLDER_CODE_BLOCK: [],
            PLACEHOLDER_LINK: [],
            PLACEHOLDER_INLINE_CODE: [],
            PLACEHOLDER_HTML_COMMENT: [],
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
            self.oldTags = list(self.tags)
            self.title = Utils.cleanHTMLEntities(apiResponse["title"])

        else:
            self.tags = None
            self.oldTags = None
            self.title = None

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
        if "items" in resp and len(resp["items"]) != 0:
            return resp["items"][0]["last_activity_date"]
        else:
            print("Response: ", resp)
            pass
        return 0

    def stripBody(self, body: str):
        forceNewline = True
        def onHTMLBlock(pat):
            self.placeholders[PLACEHOLDER_CODE_BLOCK].append(pat.group(2))
            id = len(self.placeholders[PLACEHOLDER_CODE_BLOCK]) - 1
            return pat.group(1) + PLACEHOLDER_CODE_BLOCK.format(id) + pat.group(3)

        def onFence(pat):
            self.placeholders[PLACEHOLDER_CODE_BLOCK].append(pat.group(3) + pat.group(4))
            id = len(self.placeholders[PLACEHOLDER_CODE_BLOCK]) - 1
            return pat.group(1) + pat.group(2) + PLACEHOLDER_CODE_BLOCK.format(id) + pat.group(5)

        def onBlockSpace(pat):
            self.placeholders[PLACEHOLDER_CODE_BLOCK].append(pat.group(2))
            id = len(self.placeholders[PLACEHOLDER_CODE_BLOCK]) - 1
            return pat.group(1) + PLACEHOLDER_CODE_BLOCK.format(id)

        def onInline(pat):
            for key in self.placeholders.keys():
                if key in pat.group(0):
                    # Prevent stacking multiple.
                    # This regex covers some block cases, so we wanna make sure it, well, doesn't.
                    return pat.group(0)
            self.placeholders[PLACEHOLDER_INLINE_CODE].append(pat.group(2))
            id = len(self.placeholders[PLACEHOLDER_INLINE_CODE]) - 1
            return pat.group(1) + PLACEHOLDER_INLINE_CODE.format(id) + pat.group(3)

        def onLink(pat):
            self.placeholders[PLACEHOLDER_LINK].append(pat.group(0))
            id = len(self.placeholders[PLACEHOLDER_LINK]) - 1
            return PLACEHOLDER_LINK.format(id) + ("\n" if pat.group(0).endswith("\n") else "")

        def onComment(pat):
            self.placeholders[PLACEHOLDER_HTML_COMMENT].append(pat.group(0))
            id = len(self.placeholders[PLACEHOLDER_HTML_COMMENT]) - 1
            return PLACEHOLDER_HTML_COMMENT.format(id)

        def onSnippet(pat):
            self.placeholders[PLACEHOLDER_CODE_BLOCK].append(pat.group(0))
            id = len(self.placeholders[PLACEHOLDER_CODE_BLOCK]) - 1
            return PLACEHOLDER_CODE_BLOCK.format(id)

        # We wanna remove certain bits to make sure they don't interfere with other parts of the code.

        # We need to do snippets first, because these can be caught by the space filter and be bad
        body = re.sub(r"<!-- begin snippet: .* -->\n(?:^.*$\n)*?<!-- end snippet -->",
                      onSnippet, body, flags = re.MULTILINE)
        # Code blocks ignore quotes. These are handled separately.
        #                                                    vv gotta love regex, backreferencing group 1 to get the correct
        #                                                       close delimiter. This also helps delimit properly while editing.
        #                                                       While this does mean letting fences overflow, it prevents
        #                                                       damaging code.
        body = re.sub(r"^( *)([`~]{3,})([^`]*?$\n)((?:.*?\n?)+?)(\2[`~]*$|\Z)", onFence, body, flags = re.MULTILINE)
        body = re.sub("(^<code>$\n)((?:.*?\n)+?)(^</code>$)", onHTMLBlock, body, flags = re.MULTILINE)
        # This one has to be substantially more greedy
        # TODO: figure out how we deal with nested lists with four spaces as required by regular indentation.
        # State machine?
        body = re.sub("(^\s{1,}|\A)((?:^(?: {4,}|\t+)[^\n]*?(?:\n(?:^\n)*?|$))+)",
                onBlockSpace, body, flags = re.MULTILINE)

        # Inline code
        body = re.sub("(`{1,3})(?!__dragon)((?:[^`](?!\n\n))+?)(`{1,3})", onInline, body, flags = re.MULTILINE)

        # And links
        body = re.sub(r"(?:^ *\n)?(?: *(?:\[.*?\]): \w*:+\/\/.*\n*)+",
                onLink, body, flags = re.MULTILINE)
        body = re.sub(r"(?i)!?\[[^\]\n]+\](?:\([^\)\n]+\)|\[[^\]\n]+\])(?:\](?:\([^\)\n]+\)|\[[^\]\n]+\]))?|(?:/\w+/|.:\\|\w*://|\.+/[./\w\d]+|(?:\w+\.\w+){2,})[./\w\d:/?#\[\]@!$&'()*+,;=\-~%]*",
                onLink, body, flags = re.MULTILINE)
        body = re.sub(r"(?:^ *(?:[\r\n]|\r\n))?(?:  (?:\[\d\]): \w*:+//.*\n*)+", onLink, body, flags = re.MULTILINE)


        # And comments
        body = re.sub(r"<!--(?:.*?)-->", onComment, body, flags = re.S)
        return body

    def unpackBody(self):
        if self.unpacked:
            return
        # Iterate the placeholder type and the blocks replaced
        for placeholderKey, blocks in self.placeholders.items():
            # Then iterate for each substitution
            for i in range(0, len(blocks)):
                repl = blocks[i]

                # if placeholderKey == PLACEHOLDER_CODE_BLOCK and not re.search("\n *$"):
                    # repl += "\n"
                self.body = self.body.replace(placeholderKey.format(i), repl)

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
