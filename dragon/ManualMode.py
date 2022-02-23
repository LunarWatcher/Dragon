from difflib import ndiff as DiffEngine
import sys
import os
import tempfile

from colorama import Fore, Back, init
from threading import Timer

from Post import *

init()

# These responses are well-defined exit conditions
exitConditions = [
    "y", "yes", "1", "true",
    "n", "no", "ye", "q",
    "yo", "s", "skip"
]

editorCommandMap = {
    "gvim": "gvim -f",
    "vscode": "vscode --wait"
}

DRAGON_EXPAND = 0 if "DRAGON_EXPAND" not in os.environ else os.environ["DRAGON_EXPAND"] == "1"
DRAGON_EDITOR = ""

if "DRAGON_EDITOR" not in os.environ:
    if "EDITOR" not in os.environ:
        print("WARNING: no EDITOR or DRAGON_EDITOR found. Defaulting to Vim.")
        rawEditor = "vim"
    else:
        rawEditor = os.environ["EDITOR"]
else:
    rawEditor = os.environ["DRAGON_EDITOR"]

DRAGON_EDITOR = rawEditor if rawEditor not in editorCommandMap else editorCommandMap[rawEditor]

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
        # Tags are generally always fine. Tag-related issues outweigh other stuff hard.
        return 600
    post.unpackBody()
    # Checking for critical edits has to be done after unpacking, to make sure post-unpack filters are included.
    if (post.critical):
        return 600
    count = 0
    if post.isQuestion():
        for pos, string in enumerate(DiffEngine(post.oldTitle, post.title)):
            if string.startswith("-") or string.startswith("+"):
                count += 1
    for pos, string in enumerate(DiffEngine(post.rawOldBody, post.body)):
        if string.startswith("-") or string.startswith("+"):
            count += 1

    return count

def checkPost(post: Post):
    post.changes.add("supervised")
    def render(post: Post):
        if post.isQuestion():

            print("Title:")

            for line in colorDiff(DiffEngine([post.oldTitle], [post.title])):
                if line == "__DRAGON_IGN__":
                    continue
                print(line)
            print("Tags:")
            for line in colorDiff(DiffEngine(post.oldTags, post.tags)):
                print(line)
        print("Body:")
        for line in colorDiff(DiffEngine(post.rawOldBody.split("\n"), post.body.split("\n"))):
            if line == "__DRAGON_IGN__":
                continue
            print(line)
        print(Fore.CYAN, Back.CYAN, "-------------------------------------------", Fore.RESET, Back.RESET)

    global count
    count = -2

    render(post)

    # The loop makes sure that certain responses are preserved.
    while (response := input(Fore.YELLOW + "Allow edit (post: https://stackoverflow.com/q/{})? [Y/n/yo/o/ye/ne/e] ".format(post.postID) + Fore.RESET).lower()) not in exitConditions:
        if response == 'o':
            post.open()
        elif response == "e" or response == "ne":
            post.changes.add("manual")
            fileContent = post.convertToFile(response == "e")
            with tempfile.NamedTemporaryFile(mode="w+", suffix=".dragon.md") as f:
                f.write(fileContent)
                f.flush()
                os.system(DRAGON_EDITOR + " " + f.name);

                f.seek(0)
                # Fucking Python
                post.fromFile([x[:-1] if x.endswith("\n") else x for x in f.readlines()])
            # Re-render the diff
            render(post)

    if response in ["yes", "y", "1", "true"]:
        return True
    elif response == "yo":
        post.open()
        return True
    elif response == "ye":
        Timer(1.0, post.edit).start()
        return True
    elif response == "q":
        print("Exiting...")
        exit(0)
    return False
