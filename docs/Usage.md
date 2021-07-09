# Usage

General command:
```
python3 dragon/Runner.py
```

See [manual mode](ManualMode.md) for usage of manual mode.


## CLI - input

Dragon supports command line input in the form of numeric question IDs. If supplied, only the supplied questions will be edited, before dragon stops running. The IDs must be supplied as space-separated, i.e. in the form:

```
python3 dragon/Runner.py 12345 67890 2876363 263718 467832 54768931 ...
```

Again, all IDs **must** be question IDs. Post type isn't checked aside through a potential API call error.

This is potentially primarily useful for verifying edits when debugging Dragon, but it can also be used if you want to run it on a specific set of questions for any reason.
