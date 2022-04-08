from .PTPv2 import PTPv2, PtpType
from .PtpTiming import PtpTiming, MsgInterval
from .PtpMatched import PtpMatched
from .PtpSequenceId import PtpSequenceId
import time

class FilteredPtp:
    
    def __init__(self, logger, packets=[]):
        self._logger = logger
        self._packets = packets
        self._announce = []
        self._signalling = []
        self._sync = []
        self._follow_up = []
        self._delay_req = []
        self._delay_resp = []
        self._delay_resp_fup = []
        self._other_ptp_msgs = []
        if len(packets) > 0:
            self.time_offset = packets[0].time
            self.pcap_start_date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(packets[0].time))
            self._logger.info(f'Pcap started at {self.pcap_start_date}')
        else:
            self._logger.info(f'Provided packets empty!')
            return
        self._add(packets)

    def analyse(self):
        seq_check = PtpSequenceId(self._logger, self.time_offset)
        seq_check.check_sync_followup_sequence(self.sync, self.follow_up)
        seq_check.check_delay_req_resp_sequence(self.delay_req, self.delay_resp)
        seq_check.check_dresp_dresp_fup_sequence(self.delay_resp, self.delay_resp_fup)
        self._announce_timing = PtpTiming(self._logger, self._announce, self.time_offset, MsgInterval.Rate_8)
        self._sync_timing = PtpTiming(self._logger, self._sync, self.time_offset)
        self._followup_timing = PtpTiming(self._logger, self._follow_up, self.time_offset)
        self._sync_dreq_dresp_match = PtpMatched(self._logger, self._packets, self.time_offset)
        self._logger.info(self.__repr__())
    
    def _add(self, pkt):
        if type(pkt) == PTPv2:
            self._add_dispatch(pkt)
        elif iter(pkt):
            for p in pkt:
                self._add_dispatch(p)

    def _add_dispatch(self, p):
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
        else: self._other_ptp_msgs.append(p)
    
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

    def __repr__(self):
        return f'Ptp Filtered Messages:\n\tannounce: {len(self.announce)}, \n\tsync: {len(self.sync)},'\
            f'\n\tfollow-up: {len(self.follow_up)}, \n\tdelay req: {len(self.delay_req)},'\
            f'\n\tdelay resp: {len(self.delay_resp)},\n\tdelay resp follow-up: {len(self.delay_resp_fup)}'\
            f'\n\tsignalling: {len(self.signalling)},\n\tother ptp msgs: {len(self.other_ptp)}'
