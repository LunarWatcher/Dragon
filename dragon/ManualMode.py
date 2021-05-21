from difflib import unified_diff

def checkAnswer(oldBody: str, newBody: str):
    for line in unified_diff(oldBody, newBody):
        print(line)
    print("---------")
    return input("Allow edit? [Y/n]").lower() in ["yes", "y", "1", "true"]

