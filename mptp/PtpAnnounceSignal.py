from .PTPv2 import PTPv2, PtpType, PTP_MSG_TYPE
import time

class AnnounceData:
    clock_id =   0
    origin_utc_offset =   0
    priority_1 =   0
    grandmaster_clock_class =   0
    grandmaster_clock_accuracy =   0
    grandmaster_clock_variance =   0
    priority_2 =   0
    grandmaster_clock_id =   0
    local_steps_removed =   0
    time_source =   0

    def __eq__(self, other):
        if self.clock_id == other.clock_id and self.origin_utc_offset and other.origin_utc_offset \
            and self.priority_1 == other.priority_1 and self.grandmaster_clock_class == other.grandmaster_clock_class \
            and self.grandmaster_clock_accuracy == other.grandmaster_clock_accuracy and self.grandmaster_clock_variance \
            == other.grandmaster_clock_variance and self.priority_2 == other.priority_2 and self.grandmaster_clock_id \
            == other.grandmaster_clock_id and self.local_steps_removed == other.local_steps_removed and self.time_source \
            == other.time_source:
                return True
        return False
    
    def get_status_str(self):    
        return f'Ptp signal source data from announce msg:\n\tClock ID: {self.clock_id},\n\tUTC Offset: '\
                f'{self.origin_utc_offset},\n\tpriority1: {self.priority_1},\n\tgrandmasterClockClass: '\
                f'{self.grandmaster_clock_class},\n\tgrandmasterClockAccuracy: {PTPv2.CLK_ACCURACY[self.grandmaster_clock_accuracy]},'\
                f'\n\tgrandmasterClockVariance: {self.grandmaster_clock_variance},\n\tpriority2: {self.priority_2},'\
                f'\n\tgrandmasterClockIdentity: 0x{self.grandmaster_clock_id.hex()},\n\tlocalStepsRemoved: '\
                f'{self.local_steps_removed},\n\tTimeSource: {PTPv2.TIME_SOURCE[self.time_source]}'
                
    def __repr__(self):
            return self.get_status_str()

class PtpAnnounceSignal:

    def __init__(self, logger, time_offset = 0):
        self.time_offset = time_offset
        self._logger = logger
        self.announce_data = AnnounceData()
        
    def check_announce_consistency(self, announce = []):
        if not self._is_input_valid(announce):
            self._logger.error('Announce check not valid input!')
            return
        self._get_ptp_source_info(announce)
        self._check_stream_consistency(announce)
        self._logger.info(self.announce_data.get_status_str())
     
    def _check_stream_consistency(self, announce):
        inconsistent_counter = 0
        for msg in announce:
            if msg == self.announce_data:
                inconsistent_counter += 1
                self._logger.warning(f'Announce msg data inconsistent with first announce data' \
                    + self._msg_sequence_and_time_info(msg))
        if inconsistent_counter > 0:
            self._logger.warning(f'Number of inconsistencies: {inconsistent_counter}')
        else:
            self._logger.info(f'Ptp announce stream: OK')
        
    def _get_ptp_source_info(self, announce):
        self.announce_data.clock_id = announce[0].sourcePortIdentity
        self.announce_data.origin_utc_offset = announce[0].utcOffset
        self.announce_data.priority_1 = announce[0].priority1
        self.announce_data.grandmaster_clock_class = announce[0].grandmasterClockClass
        self.announce_data.grandmaster_clock_accuracy = announce[0].grandmasterClockAccuracy
        self.announce_data.grandmaster_clock_variance = announce[0].grandmasterClockVariance
        self.announce_data.priority_2 = announce[0].priority2
        self.announce_data.grandmaster_clock_id = announce[0].grandmasterClockId
        self.announce_data.local_steps_removed = announce[0].localStepsRemoved
        self.announce_data.origin_utc_offset = announce[0].timeSource
    
    def _is_input_valid(self, msgs):
        if len(msgs) == 0:
            return False
        for msg in msgs:
            if PtpType.get_ptp_msg_type(msg) != PTP_MSG_TYPE.ANNOUNCE_MSG:
                return False
        return True

    def _msg_sequence_and_time_info(self, msg):
        t = time.strftime('%H:%M:%S', time.localtime(msg.time))
        return f'    \tCapture time: {t},\tCapture offset: {msg.time-self.time_offset:.9f},\tSequence ID: {msg.sequenceId}'

    def __repr__(self):
        return self.announce_data.get_status_str()
