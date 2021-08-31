from stackapi import StackAPI, StackAPIError
from colorama import Fore, Back

import regex as re
import random
import os

from . import Utils

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
STATE_INLINE_CODE    = 7

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
        # Tabs are converted to spaces anyway, and this makes processing substantially easier.
        body = body.replace("\t", "    ");
        modBod = ""
        cache = ""

        state = STATE_NEWLINE
        levelMultiplier = 1

        openSize = -1

        i = 0

        while i < len(body):
            if state == STATE_NEWLINE or state == STATE_BLANK_LINE:
                if body[i] == "\n":
                    modBod += body[i]
                    state = STATE_BLANK_LINE
                    i += 1
                    continue

                if ((i == 0 or state == STATE_BLANK_LINE) and body[i:i + 4 * levelMultiplier] == " " * 4 * levelMultiplier):
                    state = STATE_IN_SPACE_BLOCK

                    modBod += PLACEHOLDER_CODE_BLOCK.format(len(self.placeholders[PLACEHOLDER_CODE_BLOCK]))
                    findNewline = body.find('\n', i)
                    # We don't wanna glob the newline here.
                    cache += body[i:findNewline]
                    i = findNewline
                    continue
                elif body[i] in ['`', '~']:

                    # Code fencies are a lot tricker, unfortunately.
                    # ` at the start of a line may in fact be referring to inline code instead of a proper fence.
                    # ``` isn't enough to filter it out, because ```this is still valid inline code```.
                    # So here's what we'll do:
                    # We'll get the line
                    newlineTarget = body.find('\n', i)
                    line = body[i:newlineTarget + 1]
                    # We set this to 0 either way, because we do have some type of open.
                    openSize = 0
                    # Counting is then the same thing.
                    # What we use for it is then not our problem.
                    for char in line:
                        if char in ['`', '~']:
                            openSize += 1;
                        else:
                            break
                    # We then match this to regex
                    # Note that we've eliminated spaces by now.
                    if re.search("^[`~]+[^`~]*$", line):
                        i = newlineTarget + 1
                        print(line)
                        # We have a fence, or a "fence" - i.e. invalid single-quote
                        state = STATE_IN_FENCE

                        # We add the entire line to our cache
                        # We add the backticks to the resulting body
                        cache += line
                        # And of course the placeholder.
                        # This may result in false positives for two-line blocks wrt. the code expansion filter.
                        modBod += PLACEHOLDER_CODE_BLOCK.format(len(self.placeholders[PLACEHOLDER_CODE_BLOCK]))
                    else:
                        state = STATE_INLINE_CODE
                        # We don't need to do anything else. We leave processing to the appropriate
                        # state to avoid repetition.
                    continue

                else:
                    modBod += body[i]
                    #                                                       vvv we preserve the newline state if we only get spaces
                    # There's not gonna be a code block at this point anyway, thanks to our previous conversion of tabs to spaces.
                    state = STATE_NEWLINE if body[i] == " " and state == STATE_NEWLINE else STATE_BLANK_LINE if body[i] == '\n' else STATE_IN_LINE
            elif state == STATE_IN_LINE:
                char = body[i]
                if char == "\n":
                    state = STATE_NEWLINE
                modBod += char
            elif state == STATE_IN_SPACE_BLOCK:
                findNewline = body.find('\n', i)
                line = body[i:findNewline + 1]

                if re.search("^ {" + str(4 * levelMultiplier) + "}.*$", line):
                    if line == "\n":
                        raise RuntimeError("HOW?!")
                    i = findNewline + 1
                    cache += line
                    continue

                else:
                    if line == "\n":
                        off = i
                        intrm = ""
                        while off < len(body) and body[off] == "\n":
                            intrm += "\n"
                            off += 1
                        if re.search("^ {" + str(4 * levelMultiplier) + "}.*$", body[off:body.find('\n', off) + 1]):
                            i = off
                            cache += intrm
                            continue
                    # Trim \n
                    if cache.endswith("\n"):
                        modBod += "\n"
                        cache = cache[:-1]

                    self.placeholders[PLACEHOLDER_CODE_BLOCK].append(cache)

                    cache = ""
                    state = STATE_NEWLINE
                    continue
            elif state == STATE_IN_FENCE:
                findNewline = body.find('\n', i)
                if findNewline == -1:
                    findNewline = len(body)
                line = body[i:findNewline + 1]
                cache += line
                if re.match('^ *[`~]{' + str(openSize) + '}$', line):
                    state = STATE_NEWLINE
                    modBod += "\n"
                    self.placeholders[PLACEHOLDER_CODE_BLOCK].append(cache[:-1])

                    cache = ""
                    openSize = -1

                i = findNewline + 1
                continue
            elif state == STATE_INLINE_CODE:
                modBod += body[i]
                i += 1
                continue
                # This is really fucking easy.
                # We already have the count, so:
                newIdx = body.find('`' * openSize, i + openSize)
                #                                           vvv avoid matching the open as the close
                fragment = body[i:newIdx]
                state = STATE_IN_LINE
                # Seems about right
                i = newIdx + openSize + 1
                openSize = -1

            i += 1

        return modBod

    def unpackBody(self):
        if self.unpacked:
            return
        # Iterate the placeholder type and the blocks replaced
        for placeholderKey, blocks in self.placeholders.items():
            # Then iterate for each substitution
            for i in range(0, len(blocks)):
                repl = blocks[i]

                # TODO: hook up link filters here
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
