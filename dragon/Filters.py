import regex as re

from Post import *

ALL_ADVANCE = "(?:advance|advancing|advantage)"

# The filters have been loosely split into categories, separated by
# Vim-compatible folds. These read substantially better folded
# TODO: more, better categories

# Plain, body-only, context-free changes {{{

# TODO: get rid of the overlap between noThanks and noHelp and this one
def problemSentences(post: Post):
    (post.body, count) = re.subn(
        "(?i)[^\n.!?:]*(?:thanks|thanks?[ -]you|please|pls|help|suggest(?:ions))\b(?:[ .?!]*$|[^\n.!?:]*\b(?:help|ap+reciat\w*|me|advan\w*|a ?lot|beforehand)\b[^\n.!?:]*)[.!?_*]*(?!__dragon)",
        "",
        post.body,
        flags = re.MULTILINE
    )
    return count

# Kill thanks with fire
def noThanks(post: Post):
    (post.body, count) = re.subn(
        "(?i)(^| |, *|- *)(any advice[^.!?]{0,80}|(many|again)[ ,]*)?(thanks?|tanks|tia) *(?!to *)( *?(you *|for *|and *)*"
        + r"( *(a lot|"
            + "in advan\w* *(?:for any [^.!\n:?]+(?:.|$))?|"
            + "reading|"
            + "and|" # Binding
            + "I hope (?:for|you[re']*) (?:can)? help( me out)?.|"
            + "(?:asap|urgentl?y?) *|"
            + "best regards|"
            + "every *(?:one|body)"
        #          vv allow a single comma after the known phrases
        + ") *)+)?"
        + ",?[^\n.!?:,]*"
        + "[.,?!]*"
        + " *([:;]-?\))?\)*", # Trailing smileys
        "\n",
        post.body,
        flags = re.MULTILINE)
    return count

def noSolutionMeta(post: Post):
    # This is primarily aimed at answers. If this is present in questions, the question has problems
    # and we don't wanna touch this part with a 10 meter pole
    if post.isQuestion():
        return 0
    # https://regex101.com/r/E3tkhU/1
    (post.body, count) = re.subn(
        "(?i)(?<=^|[.:!?] +)(?:(?:this *|i(?:[' ]a?m)? +)?"
            + "(solved?|f[io]u?nd(?:ed)?) *(?:my|the) *(?:problem|issue|error)s?|"
            + "I gave up[^.!?\n]*solutions?[^.!?\n]*)[.?!]*|"
            + "I hope this helps",
        "",
        post.body,
        flags = re.MULTILINE
    )
    return count

def noGreetings(post: Post):
    (post.body, count) = re.subn(
        "(?i)^(hell?o|halo|hi(ya)?|he[yi]+)\s*(((?:\s*guys\s*|\s*and\s*|\s*g(?:a|ir)?s\s*)+|people|everyone|all)([.!?]*$)|(?=i.?(ha)?ve))?",
        "",
        post.body,
        flags = re.MULTILINE
    )
    return count

def eraseSalutations(post: Post):
    (post.body, count) = re.subn(
        "(?i)(?:"
            + r"happy coding\W*|"
            + r"(((kind(?:est)|best)?\s*regards|cheers|thanks? *(you *)?).?\n+[0-9a-z.\-,! /]{,40}\Z)|" # TODO: harden
            + r"((can (?:any|some)\s*one|I need|please) +)+(help|hello)(?! +to) *(?:\s*me\s*|\s*please\s*|\s*out\s*|\s*here\s*|"
            + r"\s*with[^.!?]{,40}\s*)*|" # TODO: harden fragment
            + r"good\s*(morning|day|afternoon|evening|weekend|night)|"
            # This one needs to be hardened, because everyone does have good use cases elsewhere
            # We want to detect "Everyone!" as a standalone word. Otherwise, we glob it into other regexes
            + r"(^|(?<=[.!?] +))everyone[.!?]|"
            + r"(?i)(?:^|[.:!?]) *(?:is|have|has)(?: +(?:you|any *(?:one|body)|guy'?s?|) *)+.{,50}problem"
                + "( with.{,20}?)([.?,!]+|$)|"
            + r"(\b| )[:;]-?[D()8d]+(\b|$| )|\\o/|"
            + r"I appreciate (?:your|the) (help|assistance)( in advance)[.?!]?"
        + ")[.!?]*",
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
        "(?i)(\s*(i'?m?\s*(am)?\s*|yeah)\s*)*(?:"
            + "sorry|apologi[zse]{2}\s*(in " + ALL_ADVANCE + ")?"
        + ")"
        #  Then we worry about the bit that comes after it, if there is anything
        + "("
        #              v bad grammar alternative
            + "\s*(for|to) [^!.?]{,40}" # Handle short fragments in the same sentence
        + ")?"
        # End the match at a punctuation, to make sure "Apologies in advance, I'm not blah blah blah" doesn't leave ", I'm not blah ..."
        # as a stub.
        # This is potentially only relevant in some cases, so we allow matching nothing as well.
        # This might need hardening
        + "([.,?!]*|$)",
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
        r"(?i)(?:(^|[.?!,]\s*)[^.?!\n]{,15}?|^)"
        + r"(?:\s*(?:please|pl[zs]+|any)\s*)*\s*"
        + r"(?:\s*(?:help|assist|teach|let me know)\b\s*)+\s*"
        + r"(?:me\s*(?:fix th?is|understand)|urgently\s*)?"
        + r"[^!.?\n,]{,60} *"
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
        "(?i)(I.{,3}|a)m.{,15}?new *(?:with|on|to|for).{,30}?(and) *,?",
        "",
        post.body,
        flags = re.MULTILINE
    )
    return count

# Grammar {{{
def missingAbbrevQuote(post: Post):
    totCount = 0
    for regex, repl in [
            (r"(?i)\b(?:i\"m|i *m(?: am)?|i'am|iam)\b", "I'm"),
            (r"(?i)\b(d)oesnt\b", r"\1oesn't"),
            (r"(?i)\b(c)ant\b", r"\1an't"),
            (r"(?i)\b(w|d)ont\b", r"\1on't"),
            (r"(?i)\bi[\" ]?ve", r"I've")
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
        r"(?<!<)\bi('|\b)(?!\.e\.?|/?>)",
        r"I\1",
        post.body
    )
    return count

def so(post: Post):
    (post.body, count) = re.subn(
        r"(?i)^(?:ye(ah?|s)?\b|ok[iay]*\b|so\b|[ \t,-])+",
        "",
        post.body
    )
    return count

def fixPunctuationSpacing(post: Post):
    # Bad: aggressive capitalization triggered u(whatever, I don't remember): https://stackoverflow.com/posts/51479419/revisions
    # Introducing spacing after punctuation causes problems with unformatted file names.
    # Pre
    (post.body, count) = re.subn(
        #                                                 vvvvv avoid matching ", ..." (or the 'typo', ", ..")
        "(?<![0-9]|^ *- |^> *|(?:the|an?) *(?:file *)?) +([.!?,:])(?!\.|[0-9]|\))",
        "\\1",
        post.body,
        flags = re.MULTILINE
    )
    return count

# }}}
# Legal names {{{
def legalNames(post: Post):
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
        "JavaScript": r"\b(?<!\.)(js|javascript)\b",
    }

    oldBody = post.body

    for repl, regex in names.items():
        post.body = re.sub("(?i)" + regex, repl, post.body)

    return oldBody != post.body
# }}}
# }}}
# Contextual body edits {{{
# }}}
# Title edits {{{
# }}}
# Tag edits {{{
# }}}
# Hybrid edits (questions and answers, but contains bits specific to questions) {{{
def capitalizeSentences(post: Post):
    # Internal function that does the replacement to avoid copy-pasta for the body and title.
    def internalReplace(string):
        # Gotta love how lambdas are supported.
        # We need to re-insert the first and third groups to make sure the text isn't
        # out of place, and then we need to make the second group title-case.
        # The second group is a single word of length >= 1, but that's guaranteed
        # to be a single word
        return re.sub(r"(?i)((?<!vs|etc|i.e|e.g)[.?!] +|\A|^\n^)((?!<)[^\w,]*)([^.!?]+?)((?=[.!? ]|$))", lambda pat : pat.group(1)
                      # \zs and \ze...
                      + pat.group(2)
                      # .capitalize() resets other capitalization, making it incredibly inappropriate
                      + pat.group(3)[0].upper()
                      + ("" if len(pat.group(3)) == 1 else pat.group(3)[1:]),
                      string, flags = re.MULTILINE)

    oldBody = post.body
    oldTitle = post.title

    post.body = internalReplace(post.body)

    # And we do the same with the title if the post is a question
    if post.isQuestion():
        post.title = internalReplace(post.title)

    return post.body != oldBody or post.title != oldTitle
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
    # Salutations {{{
    problemSentences,
    firstQuestion,
    noHelp,
    # This one needs priority over regular "thanks"
    # to properly erase "thanks,\n\nMyName"
    eraseSalutations,
    noThanks,
    noGreetings,
    noSolutionMeta,
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
]
