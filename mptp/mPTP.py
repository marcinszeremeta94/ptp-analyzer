from scapy.utils import rdpcap

from appcommon.AppLogger.ILogger import ILogger
from appcommon.ConfigReader.ConfigReader import ConfigReader
from .PtpStream import PtpStream
from .Analyser import Analyser


def PcapToPtpStream(filename: str) -> PtpStream:
    return PtpStream(open_pcap_get_ptp(filename))


def CreatePtpAnalyser(config: ConfigReader, logger: ILogger, stream: PtpStream) -> Analyser:
    return Analyser(config, logger, stream)


def open_pcap_get_ptp(filename: str):
    try:
        pcap = rdpcap(filename)
    except FileNotFoundError:
        print("Provided file is invalid or does not exist!")
        quit()
    raw_ptp_list = [p for p in pcap if p.haslayer("PTPv2")]
    return raw_ptp_list
