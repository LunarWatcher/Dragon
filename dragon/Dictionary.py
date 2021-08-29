# Helper variables {{{
# General {{{
inSentence = r"[^\n.!?]"
inSentenceStrict = r"[^\n,.!?]"
punctuation = r"[.!,?]"
# }}}
# Thanks {{{
thanksPreFragment = rf"(?i)(^ *|{punctuation} *|- *) *"
thanksPostFragment = (
    r"( *?(you *|for *|and *)*"
    + r"( *(a lot|many|"
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
    + rf"{punctuation}*"
    + r" *([:;]-?\))?\)*" # Trailing smileys
    + r"(\n+(?! *__dragon).{,30}$)?"
)
# }}}
# }}}
# Note that these edits are body-only.
# There's nothing done with the replace value, so a function or a lambda can be used if needed.
filterDict = {
    # Noise {{{
    r"(?i)^[*# ]*(edit|update) *[^ \n:]* *[:*]+": "", # Remove header and update taglines
    r"(?i)(?<=any? *ideas? *)please": "",
    r"(?i)my problem is (?=how)": "",
    r"(?i)^ *hugs *$": "", # TODO: make more permissive
    # Problem complaining meta {{{
    rf"(?i)I have been (stuck|strug+ling) (with|on) this for{inSentence}{{,12}}([.?!]|$)": r"",
    # }}}
    # }}}
    # Spelling/grammar {{{
    r"(?i)(u)dpate": r"\1pdate", # 2k+ results
    r"(?i)\b(i)ts +(?=an?)": r"\1t's ", # Its a(b) => It's a(n)
    # }}}
    # Punctuation {{{
    r"([^.]|^)\.{2}(?!\.)": r"\1.", # Double periods
    # }}}
    # Thanks {{{
    thanksPreFragment + r"(thanks|tha?n?x|tia) *(?! *to *)" + thanksPostFragment: "",
    # This one has to be separate because regex fucking sucks
    # if the thank is thanks? in the other regex, it'll only match "thank", and
    # thanksPostFragment then takes the rest.
    # Pretty fucking shit, but hey, that's regex for you. No way to say "if there is an s,
    # you always match it".
    # ? is even greedy by default.
    thanksPreFragment + r"(?i)thank *(?! *to *)" + thanksPostFragment: "",
    # }}}
    # No category (should not be used - make new categories where possible) {{{
    # }}}
}

# We want to filter certain links.
# This is to avoid link rot in a pattern-based way.
# An example of this is https://facebook.github.io/react-native/docs/text.html#limited-style-inheritance,
# which has been moved to https://reactnative.dev/docs/text#limited-style-inheritance.
# We can regex-replace the link and avoid link rot when facebook axes facebook.github.io/react-native/docs
# This also lets us remove certain links for when we inevitably stumble over link shorteners.
# We can unpack the link shorteners automatically.
# Unfortunately, link rot is complex and may be impossible to do automatically.
# When we're already editing, it may be worth checking for dead links on posts >= 6 months (?),
# but that extends beyond link filters. Would need to be done when unpacking,
# but that's another can of worms.
linkFilters = {
    "facebook\.github\.io/react-native/docs": "reactnative.dev/docs",
}
