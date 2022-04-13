import sys
import re
import time
import cmdapp.help as hlp
from mptp.Logger import Logger, LogsSeverity, PrintOption
from mptp.PtpStream import PtpStream


def analyse_ptp(ptp: PtpStream, analyse_depth: tuple):
    if "--full" in analyse_depth:
        ptp.analyse()
    else:
        if "--announce" in analyse_depth:
            ptp.analyse_announce()
        if "--ports" in analyse_depth:
            ptp.analyse_ports()
        if "--sequenceId" in analyse_depth:
            ptp.analyse_sequence_id()
        if "--timing" in analyse_depth:
            ptp.analyse_timings()
        if "--match" in analyse_depth:
            ptp.analyse_if_stream_match_sequence_of_sync_dreq_dreq_pattern()


def dispatch_args() -> tuple[str, LogsSeverity, PrintOption, tuple[str]]:
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
    log_severity = LogsSeverity.InfoOnly
    print_option = PrintOption.PrintToConsole
    for a in sys.argv[2:]:
        if a in ("-v", "--verbose"):
            log_severity = LogsSeverity.Regular
        elif a in ("--no-logs", "-l"):
            log_severity = LogsSeverity.NoLogs
        elif a in ("--debug", "-d"):
            log_severity = LogsSeverity.Debug
        elif a in ("--no-prints", "-p"):
            print_option = PrintOption.NoPrints
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
    return (file_path, log_severity, print_option, analyse_depth)


def get_file_name_from_path(file_path: str) -> str:
    return re.search("[\w-]+\.", file_path).group(0)[:-1]


def print_greeting():
    print("Starting PTP pcap Analyser\n-----\n")


def print_footer(logger: Logger, start_time: float):
    print(
        f"\n-----\nLog file location: {logger.log_dir_and_name}\n"
        f"PTP analysis took approx.: {time.time() - start_time:.3f} seconds\nDone!"
    )


def print_help():
    print(hlp.get_help())
