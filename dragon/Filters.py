import re

from Post import *

# Plain, body-only, context-free changes {{{
# Kill thanks with fire
def noThanks(post: Post):
    (post.body, count) = re.subn(
        "(?i)(^| )(thanks?|tanks)( ?(you )? (a lot\s*|in (advance|advantage|advancing)\s*)+)?.?\s*$",
        "\n",
        post.body,
        flags = re.MULTILINE)
    return count != 0

def noGreetings(post: Post):
    (post.body, count) = re.subn(
        "(?i)^(hell?o|halo|hi(ya)?|hey+)\s*((?:\s*guys\s*|\s*and\s*|\s*g(?:a|ir)?s\s*)+|people|everyone|all)([.!?]*$)",
        "",
        post.body,
        flags = re.MULTILINE
    )
    return count != 0

def eraseSalutations(post: Post):
    (post.body, count) = re.subn(
        "(?i)(?:"
            + "happy coding\W*|"
            + "((kind(?:est)|best)?\s*regards,\n\n.{,40})" # TODO: harden
        + ")",
        "",
        post.body
    )
    return count != 0

def noHelp(post: Post):
    (post.body, count) = re.subn(
        "(?i)(please\\W help( me)? ?(asap|urgently)?[.?!]|i? ?(this|need|help|urgently|asap|as soon as possible){2,}|i appreciate.{,20}help|any help.{,20}appreciated)",
        "",
        post.body,
        flags = re.MULTILINE
    )
    return count != 0

# People need to learn to link directly to the source :rolling_eyes:
def purgeGitMemory(post: Post):
    (post.body, count) = re.subn(
        "https?://(?:www\.)?gitmemory\.com/issue/(.*?/.*?)/(\d+)/(\d+)",
        r"https://github.com/\1/issues/\2#issuecomment-\3",
        post.body
    )
    return count != 0
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
    return count != 0
# }}}

filters = [
    noThanks,
    noGreetings,
    eraseSalutations,
    noHelp,
    purgeGitMemory,

    expandCode,
]
