# v0.5.0

## Added
* Post-unpack filters

## Fixed
* Grace period edits causing accidental removal. Mitigated with a post body check in addition to the date check, because grace period edits don't cause a bump in the `last_activity_date`
* The code expansion filter now works again.
* Parse lists properly (note: currently disregards how 3-indent is valid for list continuation, because I cannot be arsed to deal with that garbage).

## Changed
* The runner checks for changes to the markdown body, instead of changes to the packed body. This is necessary to make post-unpack filters possible, because they're handled separately.
* `ye` now has a slight delay before opening the post in the browser, to make sure Dragon finishes up editing before opening the browser to let the user manually edit.

# v0.4.0

## Fixed
* Prevent deletion of placeholders by thanks (primarily a problem with links)

## Added
* Further expansion of `Dictionary.py`

## Changed
* The placeholder system is now a regex/state machine hybrid, using a state machine for code blocks. May be expanded in the future, though that's probably gonna be when I'm not tired of state machines
* Tweak thanks filter to avoid unnecessary space and punctuation globbing
* Various regex changes


# v0.3.0

* New file for basic replacements that don't need a separate function. Primarily meant for simple rules, but also a lot more rules.
* Handle conflicts, admittedly at the cost of API quota. May need to reduce edit frequency when automatic to compensate.
* Preserve placeholder order by introducing a number into the placeholders
* Truncate diffs
* ... and add option to not truncate diffs
* Fix bug related to tag edits
* Add first tag edit: tag combinations.
* Bump API to 2.3.
* Prevent submission of tiny edits. Edits now require 6 or more characters changed (as counted by Python's diff engine)
* Further regex expansion and hardening; see the diff for details.
