import re
import time
from .Help import get_help
from appcommon.AppLogger import ILogger


def get_file_name_from_path(file_path: str) -> str:
    return re.search("[\w-]+\.", file_path).group(0)[:-1]


def print_greeting():
    print("Starting PTP pcap Analyser\n-----\n")


def print_footer(logger: ILogger, start_time: float):
    print(
        f"\n-----\nLog file location: {logger.get_log_dir_and_name()}\n"
        f"PTP analysis took approx.: {time.time() - start_time:.3f} seconds\nDone!"
    )


def print_help():
    print(get_help())
