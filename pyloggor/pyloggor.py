import atexit
import os
import sys
import threading
import time
from datetime import datetime, timezone
from typing import Literal, Optional


class FileHandler:
    def __init__(self, fn, log_freq, encoding: str = "utf-8"):
        if not log_freq or log_freq <= 0:
            raise ValueError("file_log_freq must be a positive number")
        self.log_freq = log_freq
        self.fn = fn
        self.encoding = encoding
        self.cache = []
        self.lock = threading.Lock()
        # Create the file if it doesn't exist, without leaking the handle.
        if not os.path.exists(fn):
            open(fn, "w", encoding=encoding).close()
        self._stop = threading.Event()
        self.thread = threading.Thread(target=self._log, daemon=True)
        self.thread.start()
        # Guarantee a final flush on interpreter shutdown so the last logs
        # (the ones you usually care about) are never lost.
        atexit.register(self.close)

    def write(self, msg):
        with self.lock:
            self.cache.append(msg)

    def flush(self):
        with self.lock:
            if self.cache:
                with open(self.fn, "a", encoding=self.encoding) as f:
                    f.write("\n".join(self.cache) + "\n")
                self.cache = []

    def _log(self):
        while not self._stop.is_set():
            # Event.wait doubles as the sleep and lets close() wake us instantly.
            self._stop.wait(1 / self.log_freq)
            try:
                self.flush()
            except Exception:
                # Never let the writer thread die silently; retry next cycle.
                pass

    def close(self):
        self._stop.set()
        try:
            self.flush()
        except Exception:
            pass


class pyloggor:
    default_level_colours = {
        "DEBUG": "\033[1;36m",
        "INFO": "\033[1;32m",
        "WARNING": "\033[1;33m",
        "ERROR": "\033[1;31m",
        "CRITICAL": "\033[1;35m",
    }

    default_level_symbols = {
        "DEBUG": "D",
        "INFO": "I",
        "WARNING": "W",
        "ERROR": "E",
        "CRITICAL": "C",
    }

    def __init__(
        self,
        *,
        file_output_level: Literal[
            "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
        ] = "DEBUG",
        console_output_level: Literal[
            "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
        ] = "DEBUG",
        topic_adjustment_space: int = 15,
        file_adjustment_space: int = 15,
        level_adjustment_space: int = 10,
        level_align: Literal["left", "center", "centre", "right"] = "left",
        topic_align: Literal["left", "center", "centre", "right"] = "left",
        file_align: Literal["left", "center", "centre", "right"] = "left",
        fn=False,
        console_output: bool = True,
        level_colours: Optional[dict] = None,
        default_colour: str = "\033[1;37m",
        delim: str = "|",
        datefmt: str = r"%d-%b-%y, %H:%M:%S:%f",
        level_symbols: Optional[dict[str, str]] = None,
        auto_filename: bool = True,
        project_root: str = "",
        show_file: bool = True,
        show_symbol: bool = True,
        show_time: bool = True,
        show_topic: bool = True,
        title_level: bool = False,
        file_log_freq: float = 3,
        encoding: str = "utf-8",
    ):
        self.file = FileHandler(fn, file_log_freq, encoding) if fn else False
        self.file_output_level = file_output_level if self.file else "NOLOG"
        self.console_output_level = console_output_level
        self.topic_adjustment_space = topic_adjustment_space
        self.file_adjustment_space = file_adjustment_space
        self.level_adjustment_space = level_adjustment_space
        self.center_level = level_align
        self.center_file = file_align
        self.center_topic = topic_align
        self.console_output = console_output
        # Copy the class defaults so per-instance overrides never mutate them.
        self.level_symbols = (
            level_symbols if level_symbols is not None else dict(self.default_level_symbols)
        )

        self.level_colours = (
            level_colours if level_colours is not None else dict(self.default_level_colours)
        )
        self.default_colour = default_colour
        self.delim = delim
        self.datefmt = datefmt

        self.project_root = project_root
        self.auto_filename = auto_filename
        self.show_file = show_file
        self.show_symbol = show_symbol
        self.show_time = show_time
        self.show_topic = show_topic
        self.title_level = title_level

        # Cache of resolved file-path prefixes keyed by caller filename, so we
        # don't re-walk the directory tree on every single log call.
        self._file_cache: dict[str, str] = {}

        self.default_levels = {
            "DEBUG": 0,
            "INFO": 1,
            "WARNING": 2,
            "ERROR": 3,
            "CRITICAL": 4,
            "NOLOG": 5,
        }
        if os.name == "nt":
            import ctypes

            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

    def set_level(self, file_output_level: str = None, console_output_level: str = None):
        """Change the logger's output levels at runtime.

        Either argument left as ``None`` keeps the current value.
        """
        if file_output_level is not None:
            self.file_output_level = file_output_level
        if console_output_level is not None:
            self.console_output_level = console_output_level

    def close(self):
        """Flush and stop the background file writer, if any."""
        if self.file:
            self.file.close()

    def extras_builder(self, extras):
        h = []
        for key, value in extras.items():
            h.append(f"{key}={value}")
        return f" {self.delim} ".join(h)

    def beautify(self, _str, space, alignment):
        space = space if space > 0 else 0
        if space == 0:
            return _str + " "
        if alignment == "right":
            return _str.rjust(space)
        elif alignment == "center" or alignment == "centre":
            return _str.center(space)
        # Default (and "left") alignment.
        return _str.ljust(space)

    def _resolve_file(self, filename: str, lineno: int) -> str:
        prefix = self._file_cache.get(filename)
        if prefix is None:
            if self.project_root:
                # Walk up until we hit the directory named ``project_root`` and
                # render the path relative to its parent.
                current_dir = os.path.dirname(filename)
                while True:
                    if os.path.basename(current_dir) == self.project_root:
                        break
                    parent_dir = os.path.dirname(current_dir)
                    if parent_dir == current_dir:  # Reached the filesystem root
                        break
                    current_dir = parent_dir
                prefix = os.path.join(
                    os.path.basename(current_dir),
                    os.path.relpath(filename, start=current_dir),
                )
            else:
                # No project root configured: show a path relative to the cwd
                # rather than climbing all the way to the filesystem root.
                try:
                    prefix = os.path.relpath(filename)
                except ValueError:  # e.g. different drive on Windows
                    prefix = filename
            self._file_cache[filename] = prefix
        return f"{prefix}:{lineno}"

    def log(
        self,
        level: str = "DEBUG",
        topic="NoTopic",
        file="NoFile",
        msg="NoMessage",  # I don't know why people do this
        extras: Optional[dict] = None,
        console_output: bool = None,
        file_output: bool = None,
    ):
        # Canonical (upper) key drives all lookups/filtering; display may differ.
        canonical = level.upper()
        display_level = level.title() if self.title_level else canonical

        time_str = datetime.now(timezone.utc).strftime(self.datefmt)

        extras_str = f" {self.delim} {self.extras_builder(extras)}" if extras else ""
        level_symbol = self.level_symbols.get(canonical, "*")

        _msg = ""
        if self.show_symbol:
            _msg += f"[{level_symbol}] "

        if self.show_time:
            _msg += f"{time_str} {self.delim} "

        _msg += f"{self.beautify(display_level, self.level_adjustment_space, self.center_level)} {self.delim} "
        if self.show_file:
            if self.auto_filename:
                frame = sys._getframe(1)
                file = self._resolve_file(frame.f_code.co_filename, frame.f_lineno)

            _msg += f"{self.beautify(file, self.file_adjustment_space, self.center_file)} {self.delim} "

        if self.show_topic:
            _msg += f"{self.beautify(topic, self.topic_adjustment_space, self.center_topic)} {self.delim} "

        _msg += f"{msg}{extras_str}"

        level_colour = self.level_colours.get(canonical, self.default_colour)

        if self._result_handler(
            self.console_output,
            console_output,
            self.console_output_level,
            canonical,
        ):
            print(f"{level_colour}{_msg}\033[0m")

        if self._result_handler(
            self.file, file_output, self.file_output_level, canonical
        ):
            self.file.write(_msg)
            # Flush immediately for critical logs so they survive a crash.
            if canonical == "CRITICAL":
                self.file.flush()

    def _result_handler(self, default, override, default_level, level):
        if override:
            return True
        if override is False or default is False:
            return False
        if level not in self.default_levels.keys() or self.default_levels.get(
            level, float("inf")
        ) >= self.default_levels.get(default_level, 0):
            return True
        return False
