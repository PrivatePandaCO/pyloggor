# pyloggor

The easiest and perhaps the most versatile logger for Python.

## Table of Contents
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
  - [Format](#format)
  - [Levels](#levels)
  - [Colouring](#colouring)
  - [Initialization options](#initialization-options)
  - [Logging options](#logging-options)
- [Appendix](#appendix)

## Installation

```
pip install pyloggor
```

Requires Python 3.9+.

## Usage

```python
from pyloggor import pyloggor

logger = pyloggor(fn="log.txt")

logger.log(level="debug", msg="Booting up.", topic="Internal")
logger.log(level="info", msg="This is an info message", topic="Info", file_output=False)
logger.log(level="warning", msg="Something is not right here.", topic="Listener",
           extras={"clientId": "1c7c36d3", "clientName": "Joe"})
logger.log(level="error", msg="I caught an error.", topic="Error Handling")
logger.log(level="critical", msg="Unhandled exception.", topic="MAIN", console_output=False)
logger.log(level="custom", msg="This is a custom level", topic="Customized")
```

1. Import the class: `from pyloggor import pyloggor`
2. Instantiate it: `logger = pyloggor()`
3. Log something: `logger.log(level="ERROR", msg="JSON config is corrupt.")`

## Configuration

### Format

The base format is not customizable, but you can toggle individual fields on/off and
pass arbitrary `extras` per log, which are appended to the end.

```
[S] DATE_TIME | LEVEL | FILE | TOPIC | MSG | EXTRAS
```

`S` is the level symbol, and `|` is the (configurable) delimiter.

### Levels

- The default hierarchy is `DEBUG` -> `INFO` -> `WARNING` -> `ERROR` -> `CRITICAL`.
  - A threshold of `WARNING` logs `WARNING`, `ERROR` and `CRITICAL`, but not `DEBUG`
    or `INFO`.
- Any other string is treated as a custom level: it does not participate in the
  hierarchy and is always printed and written to file.

### Colouring

- Pass colours as `level_colours={"LEVEL": "ANSI_ESCAPE_CODE"}`.
- Values are raw ANSI SGR escape codes, e.g. `"\033[1;36m"` for bold cyan — `pyloggor`
  writes them directly, so any ANSI sequence works.

### Initialization options

| Option | Default | Description |
| --- | --- | --- |
| `fn` | `False` | File to write logs to. Falsy means no file output. Created if missing. |
| `file_output_level` | `"DEBUG"` | Minimum level written to file. |
| `console_output_level` | `"DEBUG"` | Minimum level printed to console. |
| `console_output` | `True` | Set `False` to disable console printing entirely. |
| `auto_filename` | `True` | Auto-detect the caller's file and line number for the `FILE` field. When on, the per-log `file=` argument is ignored. |
| `project_root` | `""` | Directory name to anchor `auto_filename` paths to. Empty means paths are shown relative to the working directory. |
| `topic_adjustment_space`, `file_adjustment_space`, `level_adjustment_space` | `15`, `15`, `10` | Column widths the fields are padded to. Use `0` for no padding. |
| `level_align`, `topic_align`, `file_align` | `"left"` | Alignment within the padded column: `left`, `right`, or `center`/`centre`. |
| `level_colours` | built-in | ANSI colour per level (see [Colouring](#colouring)). |
| `default_colour` | `"\033[1;37m"` | Colour used for custom levels. |
| `level_symbols` | `D`/`I`/`W`/`E`/`C` | Single-character symbol per level; custom levels default to `*`. |
| `delim` | `"\|"` | Field delimiter (wrapped with a space on each side). |
| `datefmt` | `"%d-%b-%y, %H:%M:%S:%f"` | UTC timestamp format, e.g. `01-Oct-22, 10:35:21:300273`. |
| `show_symbol`, `show_time`, `show_file`, `show_topic` | `True` | Toggle individual fields on/off. |
| `title_level` | `False` | Display levels in `Title` case instead of `UPPER`. |
| `file_log_freq` | `3` | Times per second the background writer flushes to disk. Must be positive. |
| `encoding` | `"utf-8"` | Encoding of the log file. |

### Logging options

`logger.log(...)` accepts:

| Option | Default | Description |
| --- | --- | --- |
| `level` | `"DEBUG"` | Log level (built-in or custom). |
| `topic` | `"NoTopic"` | Topic of the entry. |
| `file` | `"NoFile"` | Source file label. Ignored when `auto_filename=True` (the default). |
| `msg` | `"NoMessage"` | The log message. |
| `extras` | `None` | A dict appended to the entry, rendered as `key=value` pairs. |
| `console_output` | logger default | Per-call override for console output. |
| `file_output` | logger default | Per-call override for file output. |

Other methods:

- `logger.set_level(file_output_level=..., console_output_level=...)` — change levels at
  runtime; either argument left unset keeps its current value.
- `logger.close()` — flush buffered file logs and stop the background writer. Also runs
  automatically on interpreter exit; `CRITICAL` logs are flushed immediately.

## Appendix

**Find this incomplete?** Open an [issue](https://github.com/PrivatePandaCO/pyloggor/issues).
Check out my [profile](https://github.com/ThePrivatePanda) — and leave a star if you found this useful!
