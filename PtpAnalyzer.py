#!/usr/bin/env python3
import sys
import re
import time
import help
from mptp.Logger import Logger, LogsSeverity, PrintOption
from mptp.PtpStream import PtpStream
from mptp import PcapTpPtp


def main():
    start_time = time.time()
    file_name, log_severity, analyse_depth, print_option = dispatch_args()
    
    print('Starting PTP pcap Analyser\n-----\n')
    logger = Logger(re.search('[\w-]+\.', file_name).group(0)[:-1], log_severity, print_option)
    ptp = PcapTpPtp.PcapToPtpStream(logger, file_name)
    analyse_ptp(ptp, analyse_depth)

    print(f'\n-----\nLog file location: {logger.log_dir_and_name}\n'
          f'PTP analysis took approx.: {time.time() - start_time:.3f} seconds\nDone!')


def analyse_ptp(ptp: PtpStream, analyse_depth):
    if '--full' in analyse_depth:
        ptp.analyse()
    else:
        if '--announce' in analyse_depth:
            ptp.analyse_announce()
        if '--ports' in analyse_depth:
            ptp.analyse_ports()
        if '--sequenceId' in analyse_depth:
            ptp.analyse_sequence_id()
        if '--timing' in analyse_depth:
            ptp.analyse_timings()
        if '--match' in analyse_depth:
            ptp.analyse_if_stream_match_sequence_of_sync_dreq_dreq_pattern()


def dispatch_args():
    if '--help' in sys.argv or '-h' in sys.argv:
        print_help()
        quit()
    try:
        file_name = sys.argv[1]
    except IndexError:
        print('No file name was provided. provide pcap file name or path. For more info use --help')
        quit()
    log_severity = LogsSeverity.InfoOnly
    print_option = PrintOption.PrintToConsole
    for a in sys.argv[2:]:
        if a in ('-v', '--verbose'):
            log_severity = LogsSeverity.Regular
        elif a in ('--no-logs', '-l'):
            log_severity = LogsSeverity.NoLogs
        elif a in ('--no-prints', '-p'):
            print_option = PrintOption.NoPrints
        elif a in ('--full', '--announce', '--ports', '--sequenceId', '--timing', '--match'):
            if not 'analyse_depth' in locals():
                analyse_depth = ()
            analyse_depth = analyse_depth + (a,)
        else:
            print(f'Unknown arg: {a}')
    if not 'analyse_depth' in locals():
        analyse_depth = ('-full',)
    try:
        re.search('[\w-]+\.', file_name).group(0)[:-1]
    except AttributeError:
        print('Wrong file name format provided')
        quit()
    return (file_name, log_severity, analyse_depth, print_option)


def print_help():
    print(help.get_help())


if __name__ == '__main__':
    main()
