from scapy.utils import rdpcap

from appcommon.AppLogger.ILogger import ILogger
from .PtpStream import PtpStream


def PcapToPtpStream(logger: ILogger, filename: str) -> PtpStream:
    return PtpStream(logger, open_pcap_get_ptp(filename))


def open_pcap_get_ptp(filename: str):
    try:
        pcap = rdpcap(filename)
    except FileNotFoundError:
        print("Provided file is invalid!")
        quit()
    raw_ptp_list = [p for p in pcap if p.haslayer("PTPv2")]
    return raw_ptp_list
