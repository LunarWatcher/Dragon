import unittest

import random
# Manipulate the seed for random consistency
random.seed(69)

import Post
from Post import Post


def mockAnswer(bodyMarkdown):
    return {
        "body_markdown": bodyMarkdown,
        "answer_id": 69621,
        "last_activity_date": 1234321
    }

class TestMarkdownParsing(unittest.TestCase):
    def __init__(self, obj):
        super().__init__(obj)
        self.maxDiff = None

    # We only test "everything" for now.
    # In the future, adding edge-cases here may be necessary.
    def testAllTypes(self):
        mPost = """This is a test for a crude markdown "parser" (which is really more of an identifier `than anything else`, but I have a lot of edge-cases to test)

This is plain text.
This is plain text after a newline.

This is plain text after a blank line.
    This is not a code block

    This is a code block

And here's some text

    and another block
Followed by text

And here's even more text

     ... and (you guessed it)
    another block
```lang-cpp
std::cout << "Followed by backticks" << std::endl;
```
```lang-python
print("Immediately followed by another block")
```
```With an inline triple start```, followed by ``double`` and `single`, and some random **bold**, because why not?

also a [link](https://www.youtube.com/watch?v=dQw4w9WgXcQ) (inline), and another [link][never-gonna-give-you-up] that's named.

![This is not an image](https://www.youtube.com/watch?v=dQw4w9WgXcQ)

[![And neither is this](https://www.youtube.com/watch?v=dQw4w9WgXcQ)](https://www.youtube.com/watch?v=dQw4w9WgXcQ)

... but pretends to be one on a TV show.:tm:

<!--
Hi btw
-->

[never-gonna-give-you-up]: https://www.youtube.com/watch?v=dQw4w9WgXcQ"""

        post = Post(mockAnswer(mPost))
        self.assertEqual("""This is a test for a crude markdown "parser" (which is really more of an identifier __dragonInlineCode0Placeholder434957__, but I have a lot of edge-cases to test)

This is plain text.
This is plain text after a newline.

This is plain text after a blank line.
    This is not a code block

__dragonCodeBlock0Placeholder434957__

And here's some text

__dragonCodeBlock1Placeholder434957__
Followed by text

And here's even more text

__dragonCodeBlock2Placeholder434957__
__dragonCodeBlock3Placeholder434957__
__dragonCodeBlock4Placeholder434957__
__dragonInlineCode1Placeholder434957__, followed by __dragonInlineCode2Placeholder434957__ and __dragonInlineCode3Placeholder434957__, and some random **bold**, because why not?

also a __dragonURL1Placeholder434957__ (inline), and another __dragonURL2Placeholder434957__ that's named.

__dragonURL3Placeholder434957__

__dragonURL4Placeholder434957__

... but pretends to be one on a TV show.:tm:

___dragonHTMLComment0Placeholder434957__

__dragonURL0Placeholder434957__""", post.body)
        post.unpackBody()
        self.assertEqual(mPost, post.body)

    def testStartBlock(self):
        mPost = """    this is a block
    Though it shouldn't trick the code
Then we have some text
```
and fuck it, a trailing code block
"""
        post = Post(mockAnswer(mPost))
        self.assertEqual(
            """__dragonCodeBlock0Placeholder434957__
Then we have some text
__dragonCodeBlock1Placeholder434957__""", post.body)

        post.unpackBody()
        self.assertEqual(post.body, mPost)

    def testShittyLists(self):
        mPost = """Oh no.

We have a list:
1. This is a list

    2. This is a list as well

    3. So is this
        1. This is a nested list

                While _this_ is code
"""
        post = Post(mockAnswer(mPost))
        self.assertEqual("""Oh no.

We have a list:
1. This is a list

    2. This is a list as well

    3. So is this
        1. This is a nested list

__dragonCodeBlock0Placeholder434957__
""", post.body)

if __name__ == "__main__":
    unittest.main()
