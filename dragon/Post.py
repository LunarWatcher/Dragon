from stackapi import StackAPI, StackAPIError
from colorama import Fore, Back

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

STANDALONE_Q_FILTER = "!nKzQUR30W7"
STANDALONE_A_FILTER = "!-)rKGgZWpB1r"

STATE_NEWLINE        = 0
STATE_BLANK_LINE     = 1
STATE_IN_LINE        = 2
STATE_IN_CODE_TAG    = 3
STATE_IN_FENCE       = 4
STATE_IN_SPACE_BLOCK = 5
STATE_HAS_BLANK      = 6

# Contains various fields used to deal with weird API requirements,
# as well as to provide diffs where needed.
class Post():

    def __init__(self, apiResponse, count = 0):
        self.count = count
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

        print("Checking for conflicts...")
        checkPost = api.fetch("{}/{}".format("questions" if self.isQuestion() else "answers", self.postID),
                              filter = STANDALONE_Q_FILTER if self.isQuestion() else STANDALONE_A_FILTER
        )
        if "items" not in checkPost:
            print("API failed to return the post.")
            return 0
        if checkPost["items"][0]["last_activity_date"] > self.lastUpdate:
            print("Edit conflict. Retrying question")
            #                                             vvv Avoid StackOverflowException. The count is checked elsewhere.
            return Post(checkPost["items"][0], self.count + 1)
        print("Updating post...")
        try:
            if self.isQuestion():

                # We have a question
                resp = api.send_data("questions/{}/edit".format(self.postID),
                    body = self.body, title = self.title, tags = ",".join(self.tags),
                    comment = comment)
            else:

                resp = api.send_data("answers/{}/edit".format(self.postID),
                    body = self.body, comment = comment)
        except StackAPIError as e:
            if "Title cannot contain" in e.message:
                print(Fore.RED + "Error from the API: invalid title. Human edit required" + Fore.RESET)

            return 0
        if "items" in resp and len(resp["items"]) != 0:
            return resp["items"][0]["last_activity_date"]
        else:
            print("Response: ", resp)
            pass
        return 0

    def stripBody(self, body: str):
        modBod = ""
        cache = ""

        state = STATE_NEWLINE
        levelMultiplier = 1

        i = 0
        while i < len(body):
            if state == STATE_NEWLINE or state == STATE_BLANK_LINE:
                if body[i] == "\n":
                    modBod += body[i]
                    state = STATE_BLANK_LINE
                    i += 1
                    continue

                if (body[i:i + 4 * levelMultiplier] == " " * 4 * levelMultiplier
                        and (i == 0 or STATE_BLANK_LINE)):
                    state = STATE_IN_SPACE_BLOCK

                    modBod += PLACEHOLDER_CODE_BLOCK.format(len(self.placeholders[PLACEHOLDER_CODE_BLOCK]))
                    findNewline = body.find('\n', i)
                    cache += body[i:findNewline ]
                    i = findNewline
                    continue
                else:
                    modBod += body[i]
                    state = STATE_IN_LINE if body[i] != '\n' else STATE_NEWLINE
            elif state == STATE_IN_LINE:
                char = body[i]
                if char == "\n":
                    state = STATE_NEWLINE
                modBod += char
            elif state == STATE_IN_SPACE_BLOCK:
                findNewline = body.find('\n', i)
                line = body[i:findNewline + 1]

                if re.search("^ {" + str(4 * levelMultiplier) + "}.*$", line):
                    i = findNewline + 1
                    cache += line
                    continue

                else:
                    if line == "\n":
                        off = i
                        intrm = "\n"
                        while off < len(body) and body[off] == "\n":
                            intrm += "\n"
                            off += 1
                        if re.search("^" + (" " * 4 * levelMultiplier) + ".*$", body[off:body.find('\n', off)]):
                            i = off
                            cache += intrm
                            continue
                    self.placeholders[PLACEHOLDER_CODE_BLOCK].append(cache)
                    print("---")
                    print(cache)
                    print("---")
                    cache = ""
                    modBod += line
                    state = STATE_NEWLINE
                    continue

            i += 1

        print (modBod)
        self.body = modBod
        self.unpacked = False
        self.unpackBody()
        print(self.body)
        exit()

        return modBod

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
