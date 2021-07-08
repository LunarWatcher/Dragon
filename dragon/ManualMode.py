from difflib import ndiff as DiffEngine
import sys
from colorama import Fore, Back, init

from Post import *
init()

# These responses are well-defined exit conditions
exitConditions = [
    "y", "yes", "1", "true",
    "n", "no", "ye", "ne",
]

def colorDiff(diff):
    for line in diff:
        if line.startswith('+'):
            yield Fore.GREEN + line + Fore.RESET
        elif line.startswith('-'):
            yield Fore.RED + line + Fore.RESET
        elif line.startswith('^'):
            yield Fore.BLUE + line + Fore.RESET
        else:
            yield line

def checkPost(post: Post):
    if post.isQuestion():
        return checkQuestion(post)
    else:
        return checkAnswer(post)

def checkQuestion(post: Post):
    print("Title:")
    for line in colorDiff(DiffEngine([post.oldTitle], [post.title])):
        print(line)
    print("Body:")
    return checkAnswer(post)

def checkAnswer(post: Post):
    post.unpackBody()
    for line in colorDiff(DiffEngine(post.rawOldBody.split("\n"), post.body.split("\n"))):
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
    return False
