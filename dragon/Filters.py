import regex as re

from Dictionary import filterDict
from Post import *

ALL_ADVANCE = "(?:advance|advancing|advantage)"

# The filters have been loosely split into categories, separated by
# Vim-compatible folds. These read substantially better folded
# TODO: more, better categories

# Strict phrases {{{

def dictionaryAttack(post: Post):
    """
    Contains various phrases that aren't fully worthy of their own functions.
    Might be worth migrating a lot of the basic functions to a function like this. /shrug
    """
    for regex, repl in filterDict.items():
        post.body = re.sub(regex, repl, post.body, flags = re.MULTILINE)

    return post.oldBody != post.body

# }}}
# Plain, body-only, context-free changes {{{

# TODO: get rid of the overlap between noThanks and noHelp and this one
def problemSentences(post: Post):
    (post.body, count) = re.subn(
        "(?i)[^\n.!?:]*(?:thanks|thanks?[ -]you|please|pls|help|suggest(?:ions?)?(?: *any)?)\b(?:[ .?!]*$|[^\n.!?:]*\b(?:help|ap+reciat\w*|me|advan\w*|a ?lot|beforehand)\b[^\n.!?:]*)+[.!?_*]*(?!__dragon)",
        "",
        post.body,
        flags = re.MULTILINE
    )
    return count

# Kill thanks with fire
def noThanks(post: Post):
    (post.body, count) = re.subn(
        r"(?i)(^| |, *|- *)((I would appreciate)? *any *(body|one)'?s? (advice|help)[^.!?]{0,80}|(many|again)[ ,]*|kindly *(?:help|advi[szc]e|guide)[, \n]*)?(thanks?|tanks|tia|thx) *(?!to *)( *?(you *|for *|and *)*"
        + r"( *(a lot|"
            + r"in advan\w* *(?:for any [^.!\n:?]+(?:.|$))?|"
            + r"reading|"
            + r"and|" # Binding
            + r"I hope (?:for|you[re']*) (?:can)? help( me out)?.|"
            + r"(?:asap|urgentl?y?) *|"
            + r"best regards|"
            + r"every *(?:one|body)"
        #          vv allow a single comma after the known phrases
        + r") *)+)?"
        + r",?[^\n.!?:,]*"
        + r"[.,?!]*"
        + r" *([:;]-?\))?\)*" # Trailing smileys
        + r"(\n+.{,30}$)?",
        "\n",
        post.body,
        flags = re.MULTILINE)
    return count

def noSolutionMeta(post: Post):
    # This is primarily aimed at answers. If this is present in questions, the question has problems
    # and we don't wanna touch this part with a 10 meter pole
    if post.isQuestion():
        return 0

    def replace(pat):
        # See noHelp for documentation on this function
        introPunct = pat.group(1)
        endPunct = pat.group(2)
        if introPunct.startswith(","):
            return endPunct
        return introPunct

    # https://regex101.com/r/E3tkhU/1
    (post.body, count) = re.subn(
        r"(?i)(^|[.:!?] +)(?:(?:this *(?:will *)?|i(?:[' ]a?m)? +)?"
            + r"(?:solved?|f[io]u?nd(?:ed)?) *(?:my|the) *(?:problem|issue|error)s?|"
            + r"I gave up[^.!?\n]*solutions?[^.!?\n]*|"
            + r"(?:I )?hope(?:ful+y)? (?:this|it) (helps?|works?)? *(?:(?:others? (?:people *)?|some *(?:one|body)))? *(?:else)? *[^\n.,!?]{,45}([.?!,]*|$)|"
            + r"problem solved"
            + r")([.?!,:]+|$)",
        replace,
        post.body,
        flags = re.MULTILINE
    )
    return count

def noGreetings(post: Post):
    (post.body, count) = re.subn(
        r"(?i)^ *(hell?o|halo|hi(ya)?|he[yi]+)\b\s*(((?:\s*guys\s*|\s*and\s*|\s*g(?:a|ir)?s\s*)+|people|everyone|all)[.!? ,]*)?",
        "",
        post.body,
        flags = re.MULTILINE
    )
    return count

def eraseSalutations(post: Post):
    (post.body, count) = re.subn(
        "(?i)(?:(?:"
            + r"happy coding\W*(?:guy'?s)?|"
            + r"(((kind(?:est)|best)?\s*regards|cheers|thanks? *(?:you *)?(?: *in advance *)?).?\n+[0-9a-z.\-,! /]{,40}\Z)|" # TODO: harden
            + r"((can (?:any|some)\s*one|I need|please) +)+(help|hello)(?! +to) *(?:\s*me\s*|\s*please\s*|\s*out\s*|\s*here\s*|"
            + r"\s*with[^.!?]{,40}\s*)*[.?!]|" # TODO: harden fragment
            + r"good\s*(morning|day|afternoon|evening|weekend|night)(?: *to( *(?:all|everyone|you|guys|experts) *)+)?|"
            # This one needs to be hardened, because everyone does have good use cases elsewhere
            # We want to detect "Everyone!" as a standalone word. Otherwise, we glob it into other regexes
            + r"(^|(?<=[.!?] +))everyone[.!?]|"
            + r"(?i)(?:^|[.:!?]) *(?:is|have|has)(?: +(?:you|any *(?:one|body)|guy'?s?|) *)+.{,50}problem"
                + "( with.{,20}?)([.?,!]+|$)|"
            + r"(\b| )[:;]-?[D()8d]+(\b|$| )|" # Emojis
            + r"\\o/|"
            + r"I appreciate (?:your|the) (help|assistance)( in advance)[.?!]?|"
            + r"please(?= *what)|"
            + r"I? *(?:hope|wish|have) *(you)? *a? *(?:nice|productive|good|delightful+|great) (?:day|afternoon)[ .?!]*$"
        + ") *)+[.!?]*",
        "",
        post.body,
        flags = re.MULTILINE
    )
    return count

def firstQuestion(post: Post):
    # https://regex101.com/r/RTnIKW/1

    (post.body, count) = re.subn(
        "(?i)(?:P.?S[^ ]*\s*)?(?:I[' ]?a?m.{,50})?(?:this is|it.?s) (?:also +)?my +first +question(?: +(?:\s*(?:here|[io]n|stack\s*o[vw]erflow)\s*)+)?(?:[.?!]|, [^!?.\n]+[.?!]*)",
        "",
        post.body
    )
    return count

def unnecessaryApologies(post: Post):
    (post.body, count) = re.subn(
        # Start by dealing with the leading fragment
        r"(?i)([(])*(\s*(i'?m?\s*(am)?\s*|yeah)\s*)*(?:"
            + r"sorry|apologi[zse]{2}\s*(in " + ALL_ADVANCE + ")?"
        + ")"
        #  Then we worry about the bit that comes after it, if there is anything
        + " *("
            + "(for|to) [^!.?]{,40}|" # Handle short fragments in the same sentence
            + r"if I[^\n.?!)]*learning[^\n?!.)]*"
        + ")?"
        # End the match at a punctuation, to make sure "Apologies in advance, I'm not blah blah blah" doesn't leave ", I'm not blah ..."
        # as a stub.
        # This is potentially only relevant in some cases, so we allow matching nothing as well.
        # This might need hardening
        + "([.,?)!]+|$)",
        "",
        post.body,
        flags = re.MULTILINE
    )
    return count

def noHelp(post: Post):
    # We need to better determine what punctuation to remove, so we use a function.
    def replace(pat):
        # We have groups for the punctuation
        # For context, consider:
        #     This, please help me.
        # and
        #     This. please help me!
        # If we always remove the first one, the second one would be replaced with "This!".
        # If we always remove the second, the first one would be replaced with "This,", along with
        # some potentially unknown amount of spaces.
        # (note that the first example above would be removed in their entirety due to the {,15}.
        # disregarding that detail, the above example holds.)
        #
        # By checking for a comma, we can better determine which to use. It may not always be completely
        # correct, but it's a step in the right direction when we can't semantically fix punctuation.
        # That's substantially more complicated, and probably not regexable
        introPunct = pat.group(1)
        endPunct = pat.group(2)
        # If we have a comma, we respect the end punctuation
        if introPunct.startswith(","):
            return endPunct
        return introPunct

    (post.body, count) = re.subn(
        r"(?i)"
        + r"(?:"
            + r"(^|[.?!,] *)" # Start of line or punctuation, including commas to match fragments
            + r"(?:[^.?!\n]{,15}?|" # Then we match up to 15 characters prior to the next fragment
            + r"(?:I[fs]|doe?s?) (?:some|any)[^.?!\n]{,60})" # or certain requests, which we wanna expand substantially harder
                                                  # within the same sentence.
        + r"|^)" # we also wanna match the start of the line
        + r"(?:\s*(?:plea[sz]+e|(?:greatly *)?appreciated?|pli?[zs]+|any *(?:one|body)'?s?|(?:at *)all|could someone|suggest(?:ions?)?[^.,\n?!]{,30})\s*,?)*\s*"
        # Edge-case: "this will help you" may be appropriate. Or really not, because it's not guaranteed to.
        # Anyway, we'll let a different filter handle that clusterfuck :)
        + r"(?<!this *will *)"
        + r"(?:\s*(?:help|assist|teach|let me know|(?:and|or)? *guidance)\b\s*)+\s*"
        + r"(?:(?:[, ]*(?:me|fix|th?is|understand|urgently\s*|(?:will|would) be|greatly|direly|appreciated|at all|please)[, ]*)+"
            + r"[^!.?\n,]{,60} *|"
            + r"[^!.?\n,]{,15}|"
            + r"(?=.{,15} +thanks)" # This searches but doesn't match a trailing thanks. We wanna delete these fragments separately due to there being different checks.
        + ")?"
        + r"($|[!.?),]+)" # Trailing punctuation or EOL
        + r"(?: *[;:]-?[()]+)?",
        replace,
        post.body,
        flags = re.MULTILINE
    )
    return count

# People need to learn to link directly to the source :rolling_eyes:
def purgeGitMemory(post: Post):
    (post.body, count) = re.subn(
        "https?://(?:www\.)?gitmemory\.com/issue/(.*?/.*?)/(\d+)/(\d+)",
        r"https://github.com/\1/issues/\2#issuecomment-\3",
        post.body
    )
    return count

def newTo(post: Post):
    (post.body, count) = re.subn(
        "(?i)(P.?S.?|also|btw|^)[ ,]*(I.{,3}|a)m.{,15}?(brand|very|pretty) *new *(?:with|on|to|for|in)[^\n,.!?]{,30}((and) *,?|[.!?,]+)?",
        "",
        post.body,
        flags = re.MULTILINE
    )
    return count

# Grammar {{{
def missingAbbrevQuote(post: Post):
    totCount = 0
    for regex, repl in [
            (r"(?i)\b(?:i\"m|i *m(?: am)?|i'am)\b", "I'm"),
            (r"(?i)\b(d)oesnt\b", r"\1oesn't"),
            (r"(?i)\b(c)ant\b", r"\1an't"),
            (r"(?i)\b(w|d)ont\b", r"\1on't"),
            (r"(?i)\bi[\" ]?ve\b", r"I've")
    ]:
        (post.body, count) = re.subn(
            regex,
            repl,
            post.body
        )
        totCount += count
    return totCount

def i(post: Post):
    (post.body, count) = re.subn(
        # v2: https://regex101.com/r/lennhz/2
        # lookaheads and lookbehinds instead of capture groups to avoid needing to re-insert
        # a back-reference to a good group. Also means we can get more fancy with
        # the regex.
        # At this point, we've fixed I'm and I've to be at least i'm and i've, which means we
        # don't need to worry about typos.
        # This means that anything capitalized
        # See the regex101 for examples.
        # This is meant to be less greedy by eliminating eliminating further problem characters.
        #                                                vvvvvvvvv This for an instance
        # is meant to find word bounded "i"'s that are then followed by a space or a number of
        # characters used to recognize words.            |       |
        # Essentially, it excludes "i" as well as 'i' and other delimiters.
        #                                          v we admittedly have to exclude that manually
        # because it's one of many lovely edge-cases.    |       |
        #                                          v     v       v
        r"(?:(?<= |^)i(?='|\b(?:[.,!? ]|$))|(?<!<|')\bi(?=[' .,!?]|$))(?!\.e\.?|\/?>)",
        r"I",
        post.body
    )
    return count

def so(post: Post):
    (post.body, count) = re.subn(
        #                                                                 vv god damn adaptive regex. We need to forcibly match a null space to make the regex match.
        #                                                                    otherwise, the regex matches "so" because "so " means "that" is matched, which is
        #                                                                    bad for the regex.
        #                                                                    logic.
        r"(?i)(^|(?<=[.!?] ))(?:[ \t,-]*(ye(ah?|s)?\b|ok[iay]*\b|so\b)[ \t-]*)+,(?! ?that| ?far)",
        "",
        post.body,
        flags = re.MULTILINE
    )
    return count

def fixPunctuationSpacing(post: Post):
    # Bad: aggressive capitalization triggered u(whatever, I don't remember): https://stackoverflow.com/posts/51479419/revisions
    # Introducing spacing after punctuation causes problems with unformatted file names.
    # Pre
    (post.body, count) = re.subn(
        r"(?<!^ *)[ ]+?([,?!:)]+|[.]+(?!\S))",
        r"\1",
        post.body,
        flags = re.MULTILINE
    )
    return count

# }}}
# Legal names {{{
def legalNames(post: Post):
    def internalReplace(string: str):
        # This is a function that collects all legal name changes.
        # They're all in a single function because re.subn() doesn't
        # fully work in cases like these.
        # We _need_ string comparison to check for changes, so to
        # avoid a ton of unnecessary checks, we run all the legal
        # name fixes, _then_ compare the string to notify about
        # edits to the body.
        # This reduces the amount of string comparisons from len(names)
        # to 1. Potentially insignificant, but reduces a substantial amount
        # of operations. I consider that a win
        names = {
            # websites
            "Stack Overflow": r"\bstack[\s-]*overflow\b(?!com)",
            "GitHub": r"\bgit[\s-]*hub\b(?!com)",
            # Generic trademarks
            "React Native": r"\breact[\s-]native\b",
            "jQuery": r"\bjquery\b",
            "CSS": r"\bcss\b", "HTML": r"\bhtml\b", "Node.JS": "\bnode.?js\b",
            # We're not matching java script because it could be a writer with poor technical understanding
            # Who doesn't know that Java doesn't have scripts. This does mean we miss the typo of JavaScript,
            # but we don't have enough context to make an informed decision.
            "JavaScript": r"\b(?<!\.|-+)(js|javascript)\b",
            ".NET": r"\b.net\b",
        }

        for repl, regex in names.items():
            string = re.sub("(?i)" + regex, repl, string)
        return string
    oldBody = post.body
    post.body = internalReplace(post.body)
    if post.isQuestion():
        oldTitle = post.title
        post.title = internalReplace(post.title)
        return oldBody != post.body or oldTitle != post.title

    return oldBody != post.body
# }}}
# }}}
# Contextual body edits {{{
# }}}
# Title edits {{{
# }}}
# Tag edits {{{

def addTags(post: Post):
    if not post.isQuestion() or len(post.tags) >= 5:
        return 0

    tags = {
        "^python-[23]\.?[x0-9]+$": "python",
    }
    count = 0
    for regex, addition in tags.items():
        if len(post.tags) >= 5:
            return count
        for tag in post.tags:
            if tag not in post.tags and re.search(regex, tag):
                post.tags.append(addition)
                count += 1

    return count

# }}}
# Hybrid edits (questions and answers, but contains bits specific to questions) {{{
def capitalizeSentences(post: Post):
    def internalReplace(string: str):
        explode = list(string)
        position = 0
        hasPunctuation = True
        while position < len(string):
            nPos = re.search(r"[ \n]+|$", string, pos = position)
            if nPos is None:
                break

            # Int conversion
            nPos = nPos.end(0)

            startOfLine = string[position - 1] == '\n'
            word = string[position:nPos]
            if hasPunctuation and not re.search("[.?!]+(?![.?!]*$)", word):
                # And finally...
                while explode[position] in ['"', "'", " "]:
                    position += 1
                explode[position] = string[position].upper()



            if re.search(r"(?<!\d)[.!?] *$|\n{2,}(?! *\*)", word) and not re.search(r"(?i)\b(e.?g.?|i.?e.?|v.?s.?|etc.?)(\b| *$)", word):
                hasPunctuation = True
            else:
                hasPunctuation = False


            position = nPos
        return "".join(explode)

    oldBody = post.body
    post.body = internalReplace(post.body.strip())
    if post.isQuestion():
        oldTitle = post.title
        post.title = internalReplace(post.title)
        return post.body != oldBody or post.title != oldTitle
    return post.body != oldBody
# }}}
# Style edits{{{
def expandCode(post: Post):
    # Bad: https://stackoverflow.com/posts/68446681/revisions @ rev2
    (post.body, count) = re.subn(
        "^`([^`]+)`$",
        "```\n\\1\n```",
        post.body,
        flags = re.MULTILINE
    )
    return count
# }}}

filters = [
    dictionaryAttack,
    # Salutations {{{
    # And this one needs to come before help
    noSolutionMeta,
    problemSentences,
    firstQuestion,
    noHelp,
    # This one needs priority over regular "thanks"
    # to properly erase "thanks,\n\nMyName"
    eraseSalutations,
    noThanks,
    noGreetings,
    unnecessaryApologies,
    newTo,
    # }}}
    # Meta {{{
    purgeGitMemory,
    # }}}
    # Grammar {{{
    missingAbbrevQuote,
    i,
    so,
    # }}}
    # Stylistic {{{
    # We wanna do this fairly late, to make sure otehr changes don't break capitalization
    fixPunctuationSpacing,
    capitalizeSentences,
    # }}}
    legalNames, # Needs to be after capitalizeSentences, to make sure trademarks aren't incorrectly capitalized due to their sentence position

    # And this doesn't give two shits about capitalization, so might as well do it here
    expandCode,

    # Tags, woo!
    addTags,
]
