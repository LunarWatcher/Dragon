# Note that these edits are body-only.
# There's nothing done with the replace value, so a function or a lambda can be used if needed.
filterDict = {
    # Noise {{{
    r"(?i)^[*# ]*(edit|update) *[^ \n:]* *[:*]+": "", # Remove header and update taglines
    r"(?i)(?<=any? *ideas? *)please": "",
    r"(?i)my problem is (?=how)": "",
    r"(?i)^ *hugs *$": "", # TODO: make more permissive
    # Problem complaining meta {{{
    r"(?i)I have been (stuck|strug+ling) (with|on) this for[^\n.!?]{,12}([.?!]|$)": r"",
    # }}}
    # }}}
    # Spelling/grammar {{{
    r"(?i)(u)dpate": r"\1pdate", # 2k+ results
    r"(?i)\b(i)ts +(?=an?)": r"\1t's ", # Its a(b) => It's a(n)
    # }}}
    # Punctuation {{{
    r"([^.]|^)\.{2}(?!\.)": r"\1.", # Double periods
    # }}}
    # No category (should not be used - make new categories where possible) {{{
    # }}}
}
