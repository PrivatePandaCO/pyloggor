import inspect
import os
import threading
import time
from datetime import datetime
from typing import Literal, Optional
import os


class FileHandler:
    def __init__(self, fn, log_freq):
        self.log_freq = log_freq
        self.fn = fn
        self.cache = []
        self.lock = threading.Lock()
        open(fn, "w") if not os.path.exists(fn) else ...
        threading.Thread(target=self._log, daemon=True).start()

    def write(self, msg):
        with self.lock:
            self.cache.append(msg)

    def _log(self):
        while True:
            time.sleep(1 / self.log_freq)
            with self.lock:
                if self.cache:
                    with open(self.fn, "a") as f:
                        f.write("\n".join(self.cache) + "\n")
                self.cache = []


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
        file_output_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "DEBUG",
        console_output_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "DEBUG",
        topic_adjustment_space: int = 15,
        file_adjustment_space: int = 15,
        level_adjustment_space: int = 10,
        level_align: Literal["left", "center", "centre", "right"] = "left",
        topic_align: Literal["left", "center", "centre", "right"] = "left",
        file_align: Literal["left", "center", "centre", "right"] = "left",
        fn=False,
        console_output: bool = True,
        level_colours: dict = default_level_colours,
        default_colour: str = "\033[1;37m",
        delim: str = "|",
        datefmt: str = r"%d-%b-%y, %H:%M:%S:%f",
        level_symbols: dict[str, str] = default_level_symbols,
        auto_filename: bool = True,
        project_root: str = "",
        show_file: bool = True,
        show_symbol: bool = True,
        show_time: bool = True,
        show_topic: bool = True,
        title_level: bool = False,
        file_log_freq: str = 3,
    ):
        self.file = FileHandler(fn, file_log_freq) if fn else False
        self.file_output_level = file_output_level if self.file else "NOLOG"
        self.console_output_level = console_output_level
        self.topic_adjustment_space = topic_adjustment_space
        self.file_adjustment_space = file_adjustment_space
        self.level_adjustment_space = level_adjustment_space
        self.center_level = level_align
        self.center_file = file_align
        self.center_topic = topic_align
        self.console_output = console_output
        self.level_symbols = level_symbols

        self.level_colours = level_colours
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

    def extras_builder(self, extras):
        h = []
        for key, value in extras.items():
            h.append(f"{key}={value}")
        return f" {self.delim} ".join(h)

    def beautify(self, _str, space, alignment):
        space = space if space > 0 else 0
        if space == 0:
            return _str + " "
        if alignment == "left":
            return _str.ljust(space)
        elif alignment == "right":
            return _str.rjust(space)
        elif alignment == "center" or alignment == "centre":
            return _str.center(space)

    def log(
        self,
        level: str = "DEBUG",
        topic="NoTopic",
        file="NoFile",
        msg="NoMessage",  # I don't know why people do this
        extras: Optional[dict] = None,
        console_output_override: bool = None,
        file_output_override: bool = None,
    ):
        level = level.title() if self.title_level else level.upper()

        time_str = datetime.utcfromtimestamp(time.time()).strftime(self.datefmt)

        extras_str = f" {self.delim} {self.extras_builder(extras)}" if extras else ""
        level_symbol = self.level_symbols[level] if level in self.level_symbols.keys() else ""

        _msg = ""
        if self.show_symbol:
            _msg += f"[{level_symbol}] "

        if self.show_time:
            _msg += f"{time_str} {self.delim} "

        _msg += f"{self.beautify(level, self.level_adjustment_space, self.center_level)} {self.delim} "
        if self.show_file:
            if self.auto_filename:
                # a very weird way of finding the right rel path given project root
                frame = inspect.currentframe().f_back
                filename = frame.f_code.co_filename
                current_dir = os.path.dirname(filename)

                while True:
                    if os.path.basename(current_dir) == self.project_root:
                        break
                    parent_dir = os.path.dirname(current_dir)
                    if parent_dir == current_dir:  # Reached the filesystem root
                        break
                    current_dir = parent_dir

                file = f"{os.path.join(os.path.basename(current_dir), os.path.relpath(filename, start=current_dir))}:{frame.f_lineno}"

            _msg += f"{self.beautify(file, self.file_adjustment_space, self.center_file)} {self.delim} "

        if self.show_topic:
            _msg += f"{self.beautify(topic, self.topic_adjustment_space, self.center_topic)} {self.delim} "

        _msg += f"{msg}{extras_str}"

        if level.upper() in self.level_colours.keys():
            level_colour = self.level_colours[level.upper()]
        else:
            level_colour = self.default_colour

        if self._result_handler(self.console_output, console_output_override, self.console_output_level, level):
            print(f"{level_colour}{_msg}\033[0m")

        if self._result_handler(self.file, file_output_override, self.file_output_level, level):
            self.file.write(_msg)

    def _result_handler(self, default, override, default_level, level):
        if override:
            return True
        if override is False or default is False:
            return False
        if level not in self.default_levels.keys() or self.default_levels.get(level, float("inf")) >= self.default_levels.get(
            default_level, 0
        ):
            return True
