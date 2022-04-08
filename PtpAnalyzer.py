#!/usr/bin/env python3
import sys
import re
from mptp import PcapTpPtp
from mptp.Logger import Logger, LogsSeverity 
from matplotlib import pyplot as plt

print('Starting PTP pcap Analyser')
try: 
    file_name = sys.argv[1]
except IndexError:
    file_name = 'ptp_example_ok.pcap'

try: 
    log_severity = LogsSeverity.Regular if sys.argv[2] == '-v' else LogsSeverity.InfoOnly
except IndexError:
    log_severity = LogsSeverity.InfoOnly

logger = Logger(re.search('[\w-]+\.', file_name).group(0)[:-1], log_severity)

ptp = PcapTpPtp.PtpRatesMsgs(logger, file_name)
ptp.analyse()

#plt.plot(ptp_filtered._sync_timing.msg_rate)
#plt.show()

print("Done!")
