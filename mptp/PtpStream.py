import time
from dataclasses import dataclass
from typing import List
from mptp.PtpPacket.PTPv2 import PTPv2, PtpType


@dataclass
class PtpStream:
    def __init__(self, packets: List[PTPv2]):
        self._time_offset: float = 0.0
        self._pcap_start_date: float = 0.0 
        self._packets: List[PTPv2] = packets
        self._announce: List[PTPv2] = []
        self._signalling: List[PTPv2] = []
        self._sync: List[PTPv2] = []
        self._follow_up: List[PTPv2] = []
        self._delay_req: List[PTPv2] = []
        self._delay_resp: List[PTPv2] = []
        self._delay_resp_fup: List[PTPv2] = []
        self._other_ptp_msgs: List[PTPv2] = []
        self._ptp_msgs_total: List[PTPv2] = []
        self._get_time_offset_from_packets(packets)
        self._add(self._cut_boundaries(packets))

    def _add(self, pkt: List[PTPv2]):
        if type(pkt) == PTPv2:
            self._add_dispatch(pkt)
        elif iter(pkt):
            for p in pkt:
                self._add_dispatch(p)

    def _get_time_offset_from_packets(self, pkt):
        if len(pkt) > 0:
            self._add_time_data(pkt)

    def _add_dispatch(self, p: PTPv2):
        if PtpType.is_sync(p):
            self._sync.append(p)
        elif PtpType.is_delay_req(p) or PtpType.is_pdelay_req(p):
            self.delay_req.append(p)
        elif PtpType.is_delay_resp(p) or PtpType.is_pdelay_resp(p):
            self._delay_resp.append(p)
        elif PtpType.is_followup(p):
            self._follow_up.append(p)
        elif PtpType.is_delay_resp_followup(p):
            self._delay_resp_fup.append(p)
        elif PtpType.is_announce:
            self._announce.append(p)
        elif PtpType.is_signalling(p):
            self._signalling.append(p)
        else:
            self._other_ptp_msgs.append(p)
        self._ptp_msgs_total.append(p)

    def _add_time_data(self, pkt: PTPv2):
        self._time_offset = pkt[0].time
        self._pcap_start_date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(pkt[0].time))

    @staticmethod
    def _cut_boundaries(raw_ptp_list: List[PTPv2]):
        for ptp_msg in raw_ptp_list:
            if PtpType.is_sync(ptp_msg):
                break
            elif PtpType.is_announce(ptp_msg):
                continue
            else:
                raw_ptp_list.remove(ptp_msg)
        for ptp_msg in reversed(raw_ptp_list):
            if PtpType.is_delay_resp_followup(ptp_msg) or PtpType.is_delay_resp(
                ptp_msg
            ):
                break
            else:
                raw_ptp_list.remove(ptp_msg)
        return raw_ptp_list

    @property
    def sync(self):
        return self._sync

    @property
    def announce(self):
        return self._announce

    @property
    def follow_up(self):
        return self._follow_up

    @property
    def delay_req(self):
        return self._delay_req

    @property
    def delay_resp(self):
        return self._delay_resp

    @property
    def delay_resp_fup(self):
        return self._delay_resp_fup

    @property
    def signalling(self):
        return self._signalling

    @property
    def other_ptp(self):
        return self._other_ptp_msgs

    @property
    def ptp_total(self):
        return self._ptp_msgs_total

    @property
    def packets_total(self):
        return self._packets
    
    @property
    def time_offset(self):
        return self._time_offset
    
    @property
    def stream_start_time(self):
        return self._pcap_start_date

    def __repr__(self) -> str:
        return (
            f"PTP Filtered Messages:\n\tAnnounce: {len(self.announce)},\n\tSync: {len(self.sync)},"
            f"\n\tFollow-up: {len(self.follow_up)}, \n\tDelay Request: {len(self.delay_req)},"
            f"\n\tDelay Response: {len(self.delay_resp)},\n\tDelay Response Follow-up:"
            f"{len(self.delay_resp_fup)}\n\tSignalling: {len(self.signalling)},\n\t"
            f"Other PTP Messages: {len(self.other_ptp)}\n\tPTP Messages Total: "
            f"{len(self.ptp_total)}"
        )
