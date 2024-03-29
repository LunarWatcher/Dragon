from stackapi import StackAPI, StackAPIError
from colorama import Fore, Back

import regex as re
import random
import os
import PostFilters as PF
import Dictionary

import Reasons

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
PLACEHOLDER_QUOTE = "__dragonQuote{{}}Placeholder{}__".format(randomNameCoefficient)

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
STATE_IN_QUOTE       = 8

# Edit summaries can be 300 characters. This leaves us with 50 characters for Dragon meta, as well as a solid margin
MAX_REASON_LENGTH = 250

# Contains various fields used to deal with weird API requirements,
# as well as to provide diffs where needed.
class Post():

    def __init__(self, apiResponse, count = 0):
        self.count = count
        self.changes = set()

        self.placeholders = {
            # I fucking hate this.
            # C++ has spoiled me with lists that default-initialize themselves.
            # Fucking fantastic feature
            PLACEHOLDER_CODE_BLOCK: [],
            PLACEHOLDER_LINK: [],
            PLACEHOLDER_INLINE_CODE: [],
            PLACEHOLDER_HTML_COMMENT: [],
            PLACEHOLDER_QUOTE: []
        }

        # TODO: parse out the user
        self.postType = "answer_count" in apiResponse
        self.postID = apiResponse["question_id" if self.postType else "answer_id"]

        self.htmlResponse = apiResponse["body_markdown"]
        self.rawOldBody = Utils.cleanHTMLEntities(apiResponse["body_markdown"])
        self.oldBody = self.stripBody(self.rawOldBody)
        self.body = self.oldBody

        # Whether or not an edit is _so important_, that regardless of how many changes,
        # it has to be allowed.
        self.critical = False

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
        if (checkPost["items"][0]["last_activity_date"] > self.lastUpdate
            # We need to verify the contents of the post as well, because grace period edits
            or checkPost["items"][0]["body_markdown"] != self.htmlResponse):
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
        def onInline(pat):
            self.placeholders[PLACEHOLDER_INLINE_CODE].append(pat.group(0))
            id = len(self.placeholders[PLACEHOLDER_INLINE_CODE]) - 1
            return PLACEHOLDER_INLINE_CODE.format(id)
        def determineSpaces(levels):
            #                         vvv tabs are why we can't have nice things. Fuck you, tabs
            return "(?: {" + str(4 * (1 + levels)) + "}|\t+)"

        # And let's tank these too
        body = re.sub(r"<!-- begin snippet: .* -->\n(?:^.*$\n)*?<!-- end snippet -->",
                      onSnippet, body, flags = re.MULTILINE)
        body = re.sub(r"<!--(?:.*?)-->", onComment, body, flags = re.S)

        modBod = ""
        cache = ""

        state = STATE_NEWLINE
        levelMultiplier = 0

        openSize = -1

        i = 0

        while i < len(body):
            if i < 0:
                raise RuntimeError("Edge-case on post " + str(self.postID) + "\n---\n" + self.rawOldBody)
            if state == STATE_NEWLINE or state == STATE_BLANK_LINE:
                if body[i] == "\n":
                    modBod += body[i]
                    state = STATE_BLANK_LINE
                    i += 1
                    continue
                if ((i == 0 or state == STATE_BLANK_LINE) and body[i:i + 4 * (levelMultiplier + 1)] == " " * (4 * (levelMultiplier + 1))):
                    state = STATE_IN_SPACE_BLOCK

                    modBod += PLACEHOLDER_CODE_BLOCK.format(len(self.placeholders[PLACEHOLDER_CODE_BLOCK]))
                    findNewline = body.find('\n', i)
                    if findNewline == -1:
                        findNewline = len(body)
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
                    if newlineTarget == -1:
                        newlineTarget = len(body) - 1
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
                        i = newlineTarget
                        # We have a fence, or a "fence" - i.e. invalid single-quote
                        state = STATE_IN_FENCE

                        # We add the entire line to our cache
                        # We add the backticks to the resulting body
                        cache += line
                        # And of course the placeholder.
                        # This may result in false positives for two-line blocks wrt. the code expansion filter.
                        modBod += PLACEHOLDER_CODE_BLOCK.format(len(self.placeholders[PLACEHOLDER_CODE_BLOCK]))
                    else:
                        # We'll leave inline code processing to regex for the time being
                        state = STATE_IN_LINE
                        continue

                else:
                    eol = body.find("\n", i + 1)
                    if (eol == -1):
                        eol = len(body)
                    # Quotes
                    if re.search("^ *>", body[i:eol]):
                        # We could use a state here, but fuck that shit
                        state = STATE_IN_QUOTE
                        modBod += PLACEHOLDER_QUOTE.format(len(self.placeholders[PLACEHOLDER_QUOTE]))
                        continue
                    # Lists 
                    if re.search("^ {" + str(4 * levelMultiplier) + "," + str(4 * (levelMultiplier + 1) - 1) + "}[0-9*\-]+[.)]", body[i:eol]):
                        # print(levelMultiplier, body[i:eol])
                        levelMultiplier += 1
                        modBod += body[i:eol]
                        i = eol
                        continue
                    elif levelMultiplier > 0 and re.search("^ {" + str(4 * (levelMultiplier - 1)) + "," + str(4 * levelMultiplier - 1) + "}[0-9*\-]+[.)]", body[i:eol]):
                        # print(levelMultiplier, body[i:eol])
                        modBod += body[i:eol]
                        i = eol
                        continue
                    elif levelMultiplier > 0:
                        # This is to avoid accidental space globbing
                        dirty = False
                        # We need to make sure we account for several levels disappearing at once
                        while (levelMultiplier > 0 and not re.search("^( {" + str(levelMultiplier * 4) + "}.*$| *$)", body[i:eol])):
                            # I fucking hate markdown some times
                            # Fun fact, you can use a mix of 3 and 4 levels. Code blocks unfortunately work the same way
                            # That said, we only look for four multipliers, because god fucking damn it's annoying to deal with varying levels
                            levelMultiplier -= 1
                            dirty = True
                        if dirty:
                            continue
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
                if findNewline == -1:
                    findNewline = len(body) - 1
                line = body[i:findNewline + 1]

                if re.search(f"^{determineSpaces(levelMultiplier)}.*$", line):
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
                        if re.search(f"^{determineSpaces(levelMultiplier)}.*$", body[off:body.find('\n', off) + 1]):
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
                #                                         v apparently, three open four close is valid?
                if re.match('^ *[`~]{' + str(openSize) + ',}$', line):
                    state = STATE_NEWLINE
                    if cache.endswith("\n"):
                        modBod += "\n"
                        cache = cache[:-1]
                    self.placeholders[PLACEHOLDER_CODE_BLOCK].append(cache)

                    cache = ""
                    openSize = -1

                i = findNewline + 1
                continue
            elif state == STATE_IN_QUOTE:
                eol = body.find('\n', i + 1)
                if (eol == -1):
                    eol = len(body)

                # Code has been eliminated at this point, so we're good to glob up all spaces
                # If code suddenly starts, it has to be fully covered in > to be valid, 
                # or has to have a preceeding newline.
                #
                # Largely just means less list fuckery for us 
                if (re.search("^ *>.*$", body[i:eol])):
                    cache += body[i:eol + 1]
                    i = eol + 1
                    continue
                else:
                    self.placeholders[PLACEHOLDER_QUOTE].append(cache)
                    cache = ""
                    state = STATE_NEWLINE
                    continue

            i += 1
        if cache != "":
            if state == STATE_IN_FENCE or state == STATE_IN_SPACE_BLOCK:
                self.placeholders[PLACEHOLDER_CODE_BLOCK].append(cache)
            elif state == STATE_IN_QUOTE:
                self.placeholders[PLACEHOLDER_QUOTE].append(cache)
            else:
                raise RuntimeError("unpack received \n---\n" + cache + "\n---\nfor unexpected state " + str(state))

        # Then we can do other code at the end. Brilliant!
        modBod = re.sub("(`{1,3})(?!__dragon)((?:[^`](?!\n\n))+?)(`{1,3})", onInline, modBod, flags = re.MULTILINE)
        # Links are insanely simple. We can regex these.
        modBod = re.sub(r"^ *(?: *(?:\[.*?\]): \w*:+\/\/.*\n*)+",
                onLink, modBod, flags = re.MULTILINE)
        modBod = re.sub(r"(?i)!?\[[^\]\n]+\](?:\([^\)\n]+\)|\[[^\]\n]+\])(?:\](?:\([^\)\n]+\)|\[[^\]\n]+\]))?|(?:/\w+/|.:\\|\w*://|\.+/[./\w\d]+|(?:\w+\.\w+){2,})[./\w\d:/?#\[\]@!$&'()*+,;=\-~%]*",
                onLink, modBod, flags = re.MULTILINE)
        modBod = re.sub(r"(?:^ *(?:[\r\n]|\r\n))?(?:  (?:\[\d\]): \w*:+//.*\n*)+", onLink, modBod, flags = re.MULTILINE)

        return modBod

    def unpackBody(self, count = 0):
        if self.unpacked:
            return
        deeper = False
        # Iterate the placeholder type and the blocks replaced
        for placeholderKey, blocks in self.placeholders.items():
            # Then iterate for each substitution
            for i in range(0, len(blocks)):
                repl = blocks[i]
                if (placeholderKey.startswith("__dragonURL")):
                    for regex, target in Dictionary.linkFilters.items():
                        (repl, replCnt) = re.subn(regex, target, repl)
                        if (replCnt != 0):
                            self.critical = True

                # if placeholderKey == PLACEHOLDER_CODE_BLOCK and not re.search("\n *$"):
                    # repl += "\n"
                self.body = self.body.replace(placeholderKey.format(i), repl)
                if "__dragon" in repl:
                    deeper = True
        #             vvvvvvvvv avoid StackOverflowException
        if deeper and count < 3:
            self.unpackBody(count + 1)
            return

        # Prevent several unpacks.
        # Purely used because we also unpack before we publish, which we do because we want to make sure
        # automatic edits are allowed to pass through without needing interference.
        self.unpacked = True
        self.body = PF.filterUnpacked(self.body)

    def convertToFile(self, useModified):
        result = ""
        if self.isQuestion():
            sTags = "\n".join(self.tags)
            result = f"Title:\n{self.title}\nTags:\n{sTags}\n\n"

        result += "Body:\n" + (self.body if useModified else self.rawOldBody)
        return result

    def fromFile(self, content: list):
        c = 0 if self.isQuestion() else 1
        if not c:
            self.tags = []
        self.body = None

        for i in range(0, len(content)):
            if (i == 1 and c == 0):
                self.title = content[i]
            elif i > 2 and c == 0:
                if content[i] == "":
                    c += 1
                else:
                    self.tags.append(content[i])

            elif content[i] == "Body:" and c == 1:
                self.body = "\n".join(content[i + 1:])
                break
        if (self.body == None):
            raise RuntimeError("Failed to set body")

    def generateEditSummary(self):
        def expand(base, reason):
            fullReason = Reasons.reasons[reason] if reason in Reasons.reasons else reason
            if (len(base) + 2 + len(fullReason) > MAX_REASON_LENGTH):
                return base
            return base + (", " if len(base) != 0 else "") + fullReason

        def prioExpand(base, reasons, reason):
            if reason in reasons:
                reasons.remove(reason)
                return expand(base, reason)
            return base

        reasons = self.changes

        reasonString = ""

        reasonString = prioExpand(reasonString, reasons, "supervised")
        reasonString = prioExpand(reasonString, reasons, "auto")

        for reason in reasons:
            reasonString = expand(reasonString, reason)

        return "Dragon::[" + reasonString + "]"

    # Browser access {{{
    def open(self):
        os.system(f"xdg-open https://stackoverflow.com/q/{self.postID}")

    def edit(self):
        os.system(f"xdg-open https://stackoverflow.com/posts/{self.postID}/edit")
    # }}}
