#!/usr/bin/env python3
import sys
import re
import time
from mptp import PcapTpPtp
from mptp.Logger import Logger, LogsSeverity
from matplotlib import pyplot as plt


def main():
    start_time = time.time()
    print('Starting PTP pcap Analyser\n-----\n')
    try:
        file_name = sys.argv[1]
    except IndexError:
        file_name = 'ptp_example_ok.pcap'

    try:
        log_severity = LogsSeverity.Regular if sys.argv[2] == '-v' else LogsSeverity.InfoOnly
    except IndexError:
        log_severity = LogsSeverity.InfoOnly

    logger = Logger(re.search('[\w-]+\.', file_name).group(0)[:-1], log_severity)

    ptp = PcapTpPtp.PcapToPtpStream(logger, file_name)
    ptp.analyse()

    # plt.plot(ptp_filtered._sync_timing.msg_rate)
    # plt.show()

    print(f'\n-----\nLog file location: {logger.log_dir_and_name}\nPTP analysis took approx.: {time.time() - start_time:.3f} seconds\nDone!')


if __name__ == '__main__':
    main()
