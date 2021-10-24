# ... I just realized what a shitty name this is. It's meant to be post (= after),
# but is easily confusable with Post (the class).
import regex as re

def filterUnpacked(body):
    # Bad: https://stackoverflow.com/posts/68446681/revisions @ rev2
    body = re.sub(
        r"^(`{1,3})([^`\n]+)\1$",
        r"```\n\2\n```",
        body,
        flags = re.MULTILINE
    )

    return body
