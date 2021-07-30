filterDict = {
    # Noise {{{
    r"(?i)^[*# ]*(edit|update) *[^ \n:]* *[:*]+": "", # Remove header and update taglines
    r"(?<=any? *ideas? *)please": "",
    r"(?i)my problem is (?=how)": "",
    # Problem complaining meta {{{
    r"I have been (stuck|strug+ling) (with|on) this for[^\n.!?]{,12}([.?!]|$)": r"",
    # }}}
    # }}}
    # Spelling/grammar {{{
    r"(?i)(u)dpate": r"\1pdate",
    r"(?i)\b(i)ts +(?=an?)": r"\1t's ", # Its a(b) => It's a(n)
    # }}}
    # Punctuation {{{
    r"([^.]|^)\.{2}(?!\.)": r"\1.", # Double periods
    # }}}
    # No category (should not be used - make new categories where possible) {{{
    # }}}
}