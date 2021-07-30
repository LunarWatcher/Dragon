from difflib import ndiff as DiffEngine
import sys
import os
from colorama import Fore, Back, init

from Post import *
init()

# These responses are well-defined exit conditions
exitConditions = [
    "y", "yes", "1", "true",
    "n", "no", "ye", "ne",
    "q"
]

DRAGON_EXPAND = 0 if "DRAGON_EXPAND" not in os.environ else os.environ["DRAGON_EXPAND"] == "1"
count: int = -2

def colorDiff(diff):
    global count
    for line in diff:
        if count > 0:
            frag = Fore.MAGENTA + "\n" + (" " * 5) + str(count) + " unchanged lines skipped.\n\n" + Fore.RESET
        else:
            frag = ""
        if line.startswith('+'):
            count = -2
            yield frag + Fore.GREEN + line + Fore.RESET
        elif line.startswith('-'):
            count = -2
            yield frag + Fore.RED + line + Fore.RESET
        elif line.startswith('?'):
            count = -2
            yield frag + Fore.BLUE + line + Fore.RESET
        else:
            if not DRAGON_EXPAND:
                count += 1
                if count >= 0:
                    yield "__DRAGON_IGN__"
                else:
                    yield line
            else:
                yield line


# Counts the number of changes made to a string by aboosing ndiff and doing a character comparison
# to count the real number of changes.
# This should line up with how SE's built-in editor counts changes for <2k users.
# Either way, it should substantially reduce bare minimum edits.
def countChanges(post: Post):
    if post.isQuestion() and post.tags != post.oldTags:
        # Tags are generally always fine.
        return 600
    # Note: we CANNOT unpack the post yet, because it'll diff the packed oldPost, which we
    # don't unpack. But that's fine, the changes potentially introduced from format unpacking
    # should be non-existent.
    count = 0
    if post.isQuestion():
        for pos, string in enumerate(DiffEngine(post.oldTitle, post.title)):
            if string.startswith("-") or string.startswith("+"):
                count += 1
    for pos, string in enumerate(DiffEngine(post.oldBody, post.body)):
        if string.startswith("-") or string.startswith("+"):
            count += 1
    return count

def checkPost(post: Post):
    if post.isQuestion():
        return checkQuestion(post)
    else:
        return checkAnswer(post)

def checkQuestion(post: Post):
    global count
    count = -2
    print("Title:")

    for line in colorDiff(DiffEngine([post.oldTitle], [post.title])):
        if line == "__DRAGON_IGN__":
            continue
        print(line)
    print("Tags:")
    for line in colorDiff(DiffEngine(post.oldTags, post.tags)):
        print(line)
    print("Body:")
    return checkAnswer(post)

def checkAnswer(post: Post):
    global count
    count = -2

    post.unpackBody()
    for line in colorDiff(DiffEngine(post.rawOldBody.split("\n"), post.body.split("\n"))):
        if line == "__DRAGON_IGN__":
            continue
        print(line)
    print(Fore.CYAN, Back.CYAN, "-------------------------------------------", Fore.RESET, Back.RESET)


    while (response := input(Fore.YELLOW + "Allow edit (post: https://stackoverflow.com/q/{})? [Y/n/o/ye/ne] ".format(post.postID) + Fore.RESET).lower()) not in exitConditions:
        if response == 'o':
            post.open()
    if response in ["yes", "y", "1", "true"]:
        return True
    elif response == "ye":
        post.edit()
        return True
    elif response == "ne":
        post.edit()
    elif response == "q":
        print("Exiting...")
        exit(0)
    return False
