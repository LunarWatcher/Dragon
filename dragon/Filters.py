import re

from Post import *

ALL_ADVANCE = "(?:advance|advancing|advantage)"

# Plain, body-only, context-free changes {{{
# Kill thanks with fire
def noThanks(post: Post):
    (post.body, count) = re.subn(
        "(?i)(^| )(thanks?|tanks)( ?(you )? "
        + "(a lot\s*|"
            + "in " + ALL_ADVANCE + "\s*(?:for any [a-z0-9,\\- /]+(?:.|$))?"
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
            + "(((kind(?:est)|best)?\s*regards|cheers|thanks),?\n+[0-9a-z.\\-,! /]{,40})|" # TODO: harden
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
        "(?i)(please\\W help( me)? ?(asap|urgently)?[.?!]|i? ?(this|need|help|urgently|asap|as soon as possible){2,}|i appreciate.{,20}help|any help.{,20}appreciated)",
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
    # This one needs priority over regular "thanks"
    # to properly erase "thanks,\n\nMyName"
    eraseSalutations,

    noThanks,
    noGreetings,
    noHelp,
    purgeGitMemory,
    unnecessaryApologies,

    expandCode,
]
