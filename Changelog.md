v2.0.0

Reliability and correctness overhaul. Contains breaking changes.

- **Breaking:** `log()` override arguments are now named `console_output` and `file_output` (previously the mismatched `console_output_override` / `file_output_override`), matching the documentation.
- **Breaking:** unknown/custom log levels now render their symbol as `*` (as documented) instead of an empty string.
- Guarantee logs are never lost on exit: the background writer now flushes on interpreter shutdown (`atexit`), `CRITICAL` logs flush immediately, and a new `close()` method flushes and stops the writer on demand.
- Fix `title_level=True` silently bypassing level filtering and blanking level symbols/colours (lookups are now case-normalised).
- Implement the documented `set_level()` method.
- The background writer thread no longer dies silently: `flush` errors are swallowed and retried, and `file_log_freq` is validated (must be positive).
- Fix a leaked file handle when creating a fresh log file.
- Log files are now written as UTF-8 by default (configurable via `encoding=`); fixes `UnicodeEncodeError` on Windows.
- With no `project_root` set, `auto_filename` now emits a path relative to the working directory instead of a near-absolute path.
- Replace the deprecated `datetime.utcfromtimestamp` with `datetime.now(timezone.utc)`.
- `beautify()` no longer returns `None` (prints literal `"None"`) for an unrecognised alignment; it falls back to left alignment.
- Per-instance `level_colours` / `level_symbols` overrides no longer mutate the shared class defaults.
- Cache resolved caller file paths so `auto_filename` doesn't re-walk the directory tree on every log call.
- Migrate packaging from the removed `distutils` to a PEP 621 `pyproject.toml`; ship a `py.typed` marker so type hints are usable by consumers.

v1.2
- Make file-logging thread-safe. Negligible delay due to thread locking. Performance degraded from 2ms/100k to 300ms/100k, but allows much more due to threading.

v1.1.6

- Clear message cache after writing to file to fix repeat writing and memory leak.

v1.1.5

- Implement usage of `SetConsoleMode` to make the text appear coloured by default on windows terminal as well, without user having to enable it manually.

v1.1.4

- Update how timestamp is handled; marginally faster now
  - Technical: `utcfromtimestamp` is somehow 5 times faster than `fromtimestamp(..., tz=pytz.utc)`

v1.1.3

- Add `'project_root` parameter:
  - Automatically shortens to full path to the project root.

v1.1.2

- Add `autofile` parameter:
  - Automatically fetches the file name and line number of the caller.
- Add `file_log_freq` parameter:
  - Time frequency to write to file. Useful to reduce disk IO stress during heavy logging.

v1.1.1

- Slightly optimize speed and memory by better usage of beautify.
- Fix datefmt not being used.

v1.1.0

- Use ANSI sequences instead of `rich`. Takes 0.05 ms / log instead of 50 ms / log.
