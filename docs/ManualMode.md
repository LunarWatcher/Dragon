# Manual mode

Manual mode is a way to approve/deny edits, as well as applying custom filters.<sup>not implemented at the time of writing</sup>

This mode allows a number of responses that do different things:

| Response | Action | Edit? |
| --- | --- | --- |
| y, yes, 1, true | Allows the edit | yes |
| o | Opens the post, re-prompts for further action | no |
| ye | Short for "yes, [and] edit" - confirms the automatic edit, and opens the edit link in your browser | Yes |
| ne | Short for "no, edit" - skips the automatic edit, but still opens the edit link in your browser | No |
| n, no | Disallows the edit | No |

Additionally, the following environment variables alter certain aspects of Dragon:

* `DRAGON_DEBUG`: Whether or not to enable some debug logging. Primarily whether or not to show what function was executed at the time of writing. Set to `1` to enable debug logging
* `DRAGON_EXPAND`: 0 by default. If 1, don't truncate the preview. By default, the preview hides blocks of identical lines to make it easier to see the actual changes.
  Setting to 1 is more or less only useful if you're looking for additional patterns. Most casual editors won't need this.

