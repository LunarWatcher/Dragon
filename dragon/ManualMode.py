from difflib import ndiff as DiffEngine
import sys
from colorama import Fore, Back, init

from Post import *
init()

# These responses are well-defined exit conditions
exitConditions = [
    "y", "yes", "1", "true",
    "n", "no", "ye", "ne",
    "q"
]

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
            count += 1
            if count >= 0:
                yield "__DRAGON_IGN__"
            else:
                yield line


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
