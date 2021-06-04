import re


# Kill thanks with fire
def noThanks(body: str):
    return re.subn(
        "(?i)(^| )(thanks?|tanks)( (you )?in (advance|advantage|advancing))?.?\s*$", "\n", body, flags = re.MULTILINE)

def noGreetings(body: str):
    return re.subn(
        "(?i)^(hello|hi(ya)?|hey)(guys|people|everyone)(.$)",
        "",
        body,
        flags = re.MULTILINE
    )

def noHelp(body: str):
    return re.subn(
        "(?i)(please help( me)? ?(asap|urgently)?[.?!]|i? ?(this|need|help|urgently|asap|as soon as possible){2,}|i appreciate.{,20}help|any help.{,20}appreciated)",
        "",
        body,
        flags = re.MULTILINE
    )

# People need to learn to link directly to the source :rolling_eyes:
def purgeGitMemory(body: str):
    return re.subn(
        "https?://(?:www\.)?gitmemory\.com/issue/(.*?/.*?)/(\d+)/(\d+)",
        r"https://github.com/\1/issues/\2#issuecomment-\3",
        body
    )

filters = [
    noThanks,
    noGreetings,
    noHelp,
    purgeGitMemory,
]
