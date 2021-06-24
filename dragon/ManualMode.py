from difflib import ndiff as DiffEngine
import sys
from colorama import Fore, init

from Post import *
init()


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

def checkQuestion(post: Post):
    print("Title:")
    for line in colorDiff(DiffEngine([post.oldTitle], [post.title])):
        print(line)
    print("Body:")
    return checkAnswer(post)

def checkAnswer(post: Post):
    for line in colorDiff(DiffEngine(post.oldBody.split("\n"), post.body.split("\n"))):
        print(line)
    print("---------")
    return input("Allow edit (post: https://stackoverflow.com/q/{})? [Y/n] ".format(post.postID)).lower() in ["yes", "y", "1", "true"]


