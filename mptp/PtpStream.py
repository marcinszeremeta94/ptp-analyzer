import time
from .Logger import Logger
from .PTPv2 import PTPv2, PtpType
from .PtpTiming import PtpTiming
from .PtpMatched import PtpMatched
from .PtpSequenceId import PtpSequenceId
from .PtpAnnounceSignal import PtpAnnounceSignal
from .PtpPortCheck import PtpPortCheck


class PtpStream:
    def __init__(self, logger: Logger, packets: list[PTPv2]):
        self._logger = logger
        self.time_offset = 0
        self._packets = packets
        self._announce = []
        self._signalling = []
        self._sync = []
        self._follow_up = []
        self._delay_req = []
        self._delay_resp = []
        self._delay_resp_fup = []
        self._other_ptp_msgs = []
        self._ptp_msgs_total = []
        self._add(self._cut_boundaries(packets))
        self._logger.banner_small("counted messages")
        self._logger.info(self.__repr__())

    def analyse(self):
        if len(self._ptp_msgs_total) == 0:
            self._logger.error("PTP stream empty")
            return
        self.analyse_announce()
        self.analyse_ports()
        self.analyse_sequence_id()
        self.analyse_timings()
        self.analyse_if_stream_match_sequence_of_sync_dreq_dreq_pattern()

    def analyse_announce(self):
        self._announce_sig = PtpAnnounceSignal(self._logger, self.time_offset)
        self._announce_sig.check_announce_consistency(self.announce)

    def analyse_ports(self):
        port_check = PtpPortCheck(self._logger, self.time_offset)
        port_check.check_ports(self._ptp_msgs_total)

    def analyse_sequence_id(self):
        if len(self._ptp_msgs_total) == 0:
            self._logger.error("PTP stream empty")
            return
        self._logger.banner_large("ptp messages sequence id analysis")
        seq_check = PtpSequenceId(self._logger, self.time_offset)
        seq_check.check_sync_followup_sequence(self.sync, self.follow_up)
        seq_check.check_delay_req_resp_sequence(self.delay_req, self.delay_resp)
        seq_check.check_dresp_dresp_fup_sequence(self.delay_resp, self.delay_resp_fup)

    def analyse_timings(self):
        if len(self._ptp_msgs_total) == 0:
            self._logger.error("PTP stream empty")
            return
        self._logger.banner_large("ptp timing and rate")
        self._announce_timing = PtpTiming(self._logger, self._announce, self.time_offset)
        self._sync_timing = PtpTiming(self._logger, self._sync, self.time_offset)
        self._followup_timing = PtpTiming(self._logger, self._follow_up, self.time_offset)

    def analyse_if_stream_match_sequence_of_sync_dreq_dreq_pattern(self):
        if len(self._sync) == 0:
            self._logger.error("No PTP Sync messages")
            return
        self._sync_dreq_dresp_match = PtpMatched(self._logger, self._packets, self.time_offset)

    def _add(self, pkt: list[PTPv2]):
        if len(pkt) > 0:
            self._add_time_data(pkt)
        else:
            self._logger.info(f"Provided stream empty!")
            return
        if type(pkt) == PTPv2:
            self._add_dispatch(pkt)
        elif iter(pkt):
            for p in pkt:
                self._add_dispatch(p)

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
        self.time_offset = pkt[0].time
        self.pcap_start_date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(pkt[0].time))
        self._logger.info(f"Pcap started at {self.pcap_start_date}")

    @staticmethod
    def _cut_boundaries(raw_ptp_list: list[PTPv2]):
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
    def announce_data(self):
        if hasattr(self, "_announce_sig"):
            self._announce_sig._announce_data
        else:
            None

    @property
    def announce_timing(self):
        if hasattr(self, "_announce_timing"):
            self._announce_timing
        else:
            None

    @property
    def sync_timing(self):
        if hasattr(self, "_sync_timing"):
            self._sync_timing
        else:
            None

    @property
    def followup_timing(self):
        if hasattr(self, "_followup_timing"):
            self._followup_timing
        else:
            None

    @property
    def sync_dreq_dresp_matc(self):
        if hasattr(self, "_sync_dreq_dresp_match"):
            self._sync_dreq_dresp_match
        else:
            None

    def __repr__(self) -> str:
        return (
            f"PTP Filtered Messages:\n\tAnnounce: {len(self.announce)},\n\tSync: {len(self.sync)},"
            f"\n\tFollow-up: {len(self.follow_up)}, \n\tDelay Request: {len(self.delay_req)},"
            f"\n\tDelay Response: {len(self.delay_resp)},\n\tDelay Response Follow-up:"
            f"{len(self.delay_resp_fup)}\n\tSignalling: {len(self.signalling)},\n\t"
            f"Other PTP Messages: {len(self.other_ptp)}\n\tPTP Messages Total: "
            f"{len(self.ptp_total)}"
        )
