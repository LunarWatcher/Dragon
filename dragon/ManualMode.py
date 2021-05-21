from difflib import ndiff as DiffEngine
import sys
from colorama import Fore, init
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

def checkAnswer(oldBody: str, newBody: str, answerID):
    for line in colorDiff(DiffEngine(oldBody.split("\n"), newBody.split("\n"))):
        print(line)
    print("---------")
    return input("Allow edit (post: https://stackoverflow.com/q/{})? [Y/n] ".format(answerID)).lower() in ["yes", "y", "1", "true"]


