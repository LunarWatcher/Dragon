import html

# Utility API {{{

def cleanHTMLEntities(rawString: str):
    return html.unescape(rawString).replace("\r", "")

def exportStrip(rawString: str):
    return re.sub(r"\n{3,}", "\n\n", rawString)

def export(rawString: str):
    return exportStrip(rawString).replace("\n", "\r\n")

def editAnswer(api, answerID, newBody, comment):
    api.send_data("answers/{}/edit".format(answerID), body=newBody, comment=comment)

def editQuestion(api, questionID, newBody, comment):
    api.send_data("questions/{}/edit".format(questionID), body = newBody, comment = comment)

def getAnswers(api, page = 1):
    return api.fetch("answers", page=page, filter=ANSWER_FILTER, pagesize=100)

def getQuestions(api, page = 1):
    return api.fetch("questions", page=page, filter=QUESTION_FILTER, pagesize=100)

# }}}
