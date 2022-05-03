import sys
import re
from typing import Tuple
from appcommon.AppLogger import LoggerOptions
from cmdapp.utils import print_help, print_greeting


def dispatch_args() -> Tuple[
    str, LoggerOptions.LogsSeverity, LoggerOptions.PrintOption, Tuple[str]
]:
    if "--help" in sys.argv or "-h" in sys.argv:
        print_help()
        quit()
    try:
        file_path = sys.argv[1]
    except IndexError:
        print(
            "No file name was provided. provide pcap file name or path. For more info use --help"
        )
        quit()
    log_severity = LoggerOptions.LogsSeverity.InfoOnly
    print_option = LoggerOptions.PrintOption.PrintToConsole
    plotter_off = False
    for a in sys.argv[2:]:
        if a in ("-v", "--verbose"):
            log_severity = LoggerOptions.LogsSeverity.Regular
        elif a in ("--no-logs", "-l"):
            log_severity = LoggerOptions.LogsSeverity.NoLogs
        elif a in ("--debug", "-d"):
            log_severity = LoggerOptions.LogsSeverity.Debug
        elif a in ("--no-prints", "-p"):
            print_option = LoggerOptions.PrintOption.NoPrints
        elif a in ("--no-plots", "-t"):
            plotter_off = True
        elif a in (
            "--full",
            "--announce",
            "--ports",
            "--sequenceId",
            "--timing",
            "--match",
        ):
            if not "analyse_depth" in locals():
                analyse_depth = ()
            analyse_depth = analyse_depth + (a,)
        else:
            print(f"Unknown arg: {a}")
    if not "analyse_depth" in locals():
        analyse_depth = ("--full",)
    try:
        re.search("[\w-]+\.", file_path).group(0)[:-1]
    except AttributeError:
        print("Wrong file name format provided")
        quit()
    print_greeting()
    return (file_path, log_severity, print_option, analyse_depth, plotter_off)
