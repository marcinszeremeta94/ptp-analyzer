from scapy.utils import rdpcap
from .PTPv2 import PtpType
from .FilteredPtp import FilteredPtp
    
def PtpRatesMsgs(logger, filename):
    return FilteredPtp(logger, _raw_ptp(filename))
    
def _raw_ptp(filename):
    try:
        pcap = rdpcap(filename)
    except FileNotFoundError:
        print('Provided file is invalid!')
        quit()
    raw_ptp_list = [p for p in pcap if p.haslayer('PTPv2')]
    return _cutboundaries(raw_ptp_list)

def _cutboundaries(raw_ptp_list):
    for ptp_msg in raw_ptp_list:
        if PtpType.is_sync(ptp_msg):
            break
        elif PtpType.is_announce(ptp_msg):
            continue
        else:
            raw_ptp_list.remove(ptp_msg)
            
    for ptp_msg in reversed(raw_ptp_list):
        if PtpType.is_delay_resp_followup(ptp_msg) or PtpType.is_delay_resp(ptp_msg):
            break
        else:
            raw_ptp_list.remove(ptp_msg)
    return raw_ptp_list
