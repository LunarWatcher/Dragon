from stackapi import StackAPI

import Utils

# Contains various fields used to deal with weird API requirements,
# as well as to provide diffs where needed.
class Post():

    def __init__(self, apiResponse):
        # TODO: parse out the user
        self.postType = "answer_count" in apiResponse
        self.postID = apiResponse["question_id" if self.postType else "answer_id"]

        self.oldBody = Utils.cleanHTMLEntities(apiResponse["body_markdown"])
        self.body = self.oldBody

        if self.postType:
            # Parse out titles and tags
            self.tags = apiResponse["tags"]
            self.title = Utils.cleanHTMLEntities(apiResponse["title"])

        else:
            self.tags = None
            self.title = None

        # Could've probably set these in the opposite order, but here we are
        self.oldTags = self.tags
        self.oldTitle = self.title

        self.lastUpdate = apiResponse["last_activity_date"]


    def isQuestion(self):
        return self.postType

    def publishUpdates(self, api: StackAPI, comment: str):
        if self.postType:
            # We have a question
            resp = api.send_data("questions/{}/edit".format(self.postID),
                body = self.body, title = self.title, tags = ",".join(self.tags),
                comment = comment)
        else:
            resp = api.send_data("answers/{}/edit".format(self.postID),
                body = self.body, comment = comment)
        if "last_activity_date" in resp:
            return resp["last_activity_date"]
        else:
            # TODO: error handling
            pass
        return 0
