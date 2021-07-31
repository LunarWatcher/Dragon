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