import re


# Kill thanks with fire
def noThanks(body: str):
    (newBody, matches) = re.subn(
        "(?i)(^| )(thanks?|tanks)( (you )?in (advance|advantage|advancing))?.?\s*$", "\n", body, flags = re.MULTILINE)
    return (newBody, matches != 0)

# People need to learn to link directly to the source :rolling_eyes:
def purgeGitMemory(body: str):
    (newBody, matches) = re.subn(
        "https?://(?:www\.)?gitmemory\.com/issue/(.*?/.*?)/(\d+)/(\d+)",
        r"https://github.com/\1/issues/\2#issuecomment-\3",
        body
    )
    return (newBody, matches != 0)

filters = [
    noThanks,
    purgeGitMemory
]

def getFiltersBecausePythonIsDumbAndCantExportBasicArraysWithoutRequiringGoatSacrifices():
    return filters
