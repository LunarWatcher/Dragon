import re

from Post import *

ALL_ADVANCE = "(?:advance|advancing|advantage)"

# The filters have been loosely split into categories, separated by
# Vim-compatible folds. These read substantially better folded
# TODO: more, better categories

# Plain, body-only, context-free changes {{{
# Kill thanks with fire
def noThanks(post: Post):
    (post.body, count) = re.subn(
        "(?i)(^| )(thanks?|tanks)(?!\s*to\s*)(\s*?(you |for )* "
        + "(\s*a lot\s*|"
            + "in " + ALL_ADVANCE + "\s*(?:for any [a-z0-9,\\- /]+(?:.|$))?|"
            + "\s*reading\s*|"
            + "\s*and\s*|" # Binding
            + "\s*I hope (?:for|you[re']*) (?:can)? help( me out)?.\s*|"
        + "\s*(?:asap|urgentl?y?)\s*"
        + ")+)?.?\s*$",
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
            + "(((kind(?:est)|best)?\s*regards|cheers|thanks),?\n+[0-9a-z.\\-,! /]{,40})" # TODO: harden
        + ")",
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
            + "for [a-z0-9/-]{,40}" # Handle short fragments in the same sentence
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
        "(?i)(please\\W help( me)? ?(asap|urgently)?[.?!]|i? ?"
        + "(this|need|help|urgently|asap|as soon as possible){2,}|i appreciate.{,20}help|any help.{,20}appreciated.)",
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

# Grammar {{{
def im(post: Post):
    (post.body, count) = re.subn(
        r"(?i)\b(?:i *m(?: am)?|i'am|iam)\b",
        "I'm",
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
    names = {
        "Stack Overflow": r"\bstack\s*overflow\b",
        "GitHub": r"\bgit\s*hub\b"
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
    # This one needs priority over regular "thanks"
    # to properly erase "thanks,\n\nMyName"
    eraseSalutations,
    noThanks,
    noGreetings,
    noHelp,
    unnecessaryApologies,
    # }}}
    # Stylistic {{{
    purgeGitMemory,
    # }}}

    # Grammar {{{
    im,
    # }}}

    expandCode,
]
