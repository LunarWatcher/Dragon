# Avoiding damage

A fully unsupervised computer editor does come with a massive caveat: It _has_ to be completely bullet-proof to not cause unsupervised damage.

The obvious thing to do is massively test everything prior to letting it go on its own, which at the time of writing is why the automatic running hasn't been implemented yet.

## Limiting editing speed

We have 10000 API requests per day. Huge page sizes means one GET theoretically results in ~101 API requests: 100 edits, and 1 GET. This gives a theoretical max capacity of 9900 posts edited in a single day<sup>1</sup>. While Dragon is going to push towards that, that cannot be done so fast that it's only limited by the speed of the SE API, and the internet of the host machine.


If something then is faulty in Dragon, there could be 10000 edits in a couple hours while the runner doesn't have time to notice until an obscene amount of edits have been made. This is obviously not desirable. My current plan is to make one edit every 3-5 seconds<sup>exact time not determined</sup>. At 4 seconds, there's roughly 1000 edits per hour. This is still _substantially_ higher than any human (or wolf :p) editor can do. And trust me, I've manually edited with manually triggered tools and capped out at 5-10 posts per minute. At 4 seconds between edits, Dragon is consistently 3-10 times faster regardless of the posts involved. 5-10 posts is on super trivial edits. On the level of edit quality Dragon is currently at, I've only ever done 5 per minute, purely limited by the speed of the input tools at my disposal, as well as the response time of the UI.

The fluctuating average of a humanoid editor means Dragon is faster in the long run. That's why it's such a huge advantage to have an automated editor, at least when it misbehaves. There's stuff that still requires humanoid intervention, however, but Dragon does the grunt work so we don't have to.

1: This assumes each GET only consumes one API call. I'm reasonably certain this isn't the case, since we also get answers for every single question. I believe each call to GET is about 2-4 API requests, but this request can vary massively in size. Depending on the questions, there's at least 100 posts. If everything has three answers, the request returns 400 posts. Consequentially, it's hard to estimate how much exactly can be edited on the quota, but it's unrealistic that more than 9900 posts can be edited. This figure may still be way too high, however.

## Future plan: Limiting edits

A plan of mine is to add an environment variable that specifies an amount of posts to edit. Essentially, a runner can `DRAGON_COUNT=500 ./dragon/Runner.py` to edit 500 posts, and then terminate.

This isn't meant to be required to run Dragon, but an optional way to better control the edits and reduce damage if the runner is uncertain or for whatever reason feels like reducing the amount of edits. This is essentially controlling the quantity.

## Future plan: supervised rollback

At some point:tm:, I'm going to implement a supervised rollback system that searches for dragon edits and offers to revert them. This is exclusively for a quick and easy way to track down potentially bad edits if Dragon at any point ends up doing something bad on a big scale.
