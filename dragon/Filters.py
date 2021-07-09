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
        "(?i)(^| )((many)\s*)?(thanks?|tanks)(?!\s*to\s*)(\s*?(you\s*|for\s*|and\s*)*"
        + "(\s*a lot\s*|"
            + "\s*in advan\w*\s*(?:for any [^.!\n:?]+(?:.|$))?|"
            + "\s*reading\s*|"
            + "\s*and\s*|" # Binding
            + "\s*I hope (?:for|you[re']*) (?:can)? help( me out)?.\s*|"
            + "\s*(?:asap|urgentl?y?)\s*|"
            + "\s*best regards\s*"
        + ")+)?[^\n.!?:]*[.,?!]*\s*$",
        "\n",
        post.body,
        flags = re.MULTILINE)
    return count

def noGreetings(post: Post):
    (post.body, count) = re.subn(
        "(?i)^(hell?o|halo|hi(ya)?|hey+)\s*((?:\s*guys\s*|\s*and\s*|\s*g(?:a|ir)?s\s*)+|people|everyone|all)([.!?]*$)",
        "",
        post.body,
        flags = re.MULTILINE
    )
    return count

def eraseSalutations(post: Post):
    (post.body, count) = re.subn(
        "(?i)(?:"
            + "happy coding\W*|"
            + "(((kind(?:est)|best)?\s*regards|cheers|thanks),?\n+[0-9a-z.\\-,! /]{,40})|" # TODO: harden
            + "can (?:any|some)\s*one help\s*(?:\s*me\s*|\s*please\s*|\s*out\s*|\s*here\s*)*|"
            + "good\s*(morning|day|afternoon|evening|weekend|night)"
        + ")[.!?]*",
        "",
        post.body
    )
    return count

def unnecessaryApologies(post: Post):
    (post.body, count) = re.subn(
        # Start by dealing with the leading fragment
        "(?i)(i'?m?\s*(am)?\s*)?(?:"
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
    (post.body, count) = re.subn(
        "(?i)((\s*can\s*|\s*some\s*(?:one|body)\s*|\s*please\s*|\s*kindly\s*)*,* help( me)? ?(asap|urgently)?[.?!,]|i? ?"
        + "(this|need|help|much|greatly appreciated|urgently|asap|as soon as possible){2,}|i appreciate.{,20}help|any help.{,20}appreciated.)",
        "",
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

    )

# Grammar {{{
def missingAbbrevQuote(post: Post):
    totCount = 0
    for regex, repl in [
            (r"(?i)\b(?:i *m(?: am)?|i'am|iam)\b", "I'm"),
            (r"(?i)\b(d)oesnt\b", r"\1oesn't"),
            (r"(?i)\b(c)ant\b", r"\1an't"),
            (r"(?i)\b(w|d)ont\b", r"\1on't"),
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
    # to 1. Potentially insignificant
    names = {
        # websites
        "Stack Overflow": r"\bstack[\s-]*overflow\b(?!com)",
        "GitHub": r"\bgit[\s-]*hub\b(?!com)",
        # Generic trademarks
        "React Native": r"\breact[\s-]native\b",
        "jQuery": r"\bjquery\b",
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
        return re.sub(r"(?i)(^|(?<!vs|etc|i.e|e.g)[.?!]\s+)([^\w,]*)(.+?)( |$)", lambda pat : pat.group(1)
                      # \zs and \ze...
                      + pat.group(2)
                      # .capitalize() resets other capitalization, making it incredibly inappropriate
                      + pat.group(3)[0].upper()
                      + ("" if len(pat.group(3)) == 1 else pat.group(3)[1:])
                      + pat.group(4), string, flags = re.MULTILINE)

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
    # This one needs priority over regular "thanks"
    # to properly erase "thanks,\n\nMyName"
    eraseSalutations,
    noThanks,
    noGreetings,
    noHelp,
    unnecessaryApologies,
    # }}}
    # Meta {{{
    purgeGitMemory,
    # }}}
    # Grammar {{{
    missingAbbrevQuote,
    i,
    # }}}
    # Stylistic {{{
    # We wanna do this fairly late, to make sure otehr changes don't break capitalization
    capitalizeSentences,
    # }}}
    legalNames, # Needs to be after capitalizeSentences, to make sure trademarks aren't incorrectly capitalized due to their sentence position

    # And this doesn't give two shits about capitalization, so might as well do it here
    expandCode,
]
