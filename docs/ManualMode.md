# Manual mode

Manual mode is a way to approve/deny edits, as well as applying custom filters<sup>not implemented at the time of writing</sup> and manually editing posts without actually loading Stack in its entirety.

This mode allows a number of responses that do different things:

| Response | Action | Submits the edit? |
| --- | --- | --- |
| y, yes, 1, true | Allows the edit | yes |
| yo | Allows the edit, and opens to the post. Equivalent to `o` and then `y` | Yes |
| o | Opens the post, re-prompts for further action | no |
| ye | Short for "yes, [and] edit" - confirms the automatic edit, and opens the edit link in your browser. To edit locally, use `e` instead. | Yes |
| n, no, s, skip | Disallows the edit | No |
| e | Opens the post, starting with Dragon's suggestion, in Your Favorite Editor | no |
| ne | Equivalent to `e`, but discards Dragon's suggestion and starts from the source post. Doesn't immediately commit the edit | No |

Additionally, the following environment variables alter certain aspects of Dragon:

* `DRAGON_DEBUG`: Whether or not to enable some debug logging. Primarily whether or not to show what function was executed at the time of writing. Set to `1` to enable debug logging
* `DRAGON_EXPAND`: 0 by default. If 1, don't truncate the preview. By default, the preview hides blocks of identical lines to make it easier to see the actual changes.
  Setting to 1 is more or less only useful if you're looking for additional patterns. Most casual editors won't need this.
* `DRAGON_EDITOR`: By default, this is set to `EDITOR`, or `vim` if neither `EDITOR` nor `DRAGON_EDITOR` is set. Defines what editor to use for the `e` and `ne` actions.

