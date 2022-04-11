from tkinter.messagebox import NO
from .PTPv2 import PtpType
from enum import Enum
import time
import statistics
import numpy as np

# ERROR_THRESHOLD = 1000000 # 1/4 of 1/15 - 1/16 p sec rates, 1 ms
# ERROR_THRESHOLD = 625000 # 1%
ERROR_THRESHOLD = 1250000 # 2%
# ERROR_THRESHOLD = 3125000 # 5%
# ERROR_THRESHOLD = 6250000 #10%
ONE_SEC_IN_NS = 1000000000

class MsgInterval(Enum):
    # Value is time diff between msgs in ns
    Rate_16 = 62500000
    Rate_8 = 125000000
    Rate_4 = 250000000
    Rate_2 = 500000000
    Rate_1 = 1000000000

# This analysis makes sense for ptp msgs like announce, sync and follow-up
class PtpTiming:
    
    def __init__(self, logger, packets=[], timeOffset = 0, interval = MsgInterval.Rate_16):
        self._msgs = packets
        self._time_offset = timeOffset
        self._logger = logger
        self._msg_interval = interval
        self._status_ok = True
        self.error_over_threshold = []
        self.msg_rates = []
        self.capture_error_over_threshold = []
        self.capture_rates = []
        self.processed_ptp_type =  PtpType.get_ptp_msg_type(self._msgs[0]) if len(packets) > 0 else None
        if self.processed_ptp_type == None:
            return
        if self._is_input_valid():
            self._status_ok &= self._analyse_timestamp_regularity()
            self._status_ok &= self._analyse_capture_time_regularity()
            self._logger.info(self.__repr__())
        else:
            self._logger.error('Provided input packets does not contain PTP msgs of one type!')
            self._status_ok = False
    
    def _analyse_capture_time_regularity(self):
        irregularities_counter = 0 
        self._logger.debug(f'Analyse capture time regularity of {self.processed_ptp_type}:'\
                        f'\n\tExpected time diff for {self._msg_interval} is: {self._msg_interval.value/1000} us., '\
                        f'allowed delta set to: {ERROR_THRESHOLD/1000} us.')
        for i, msg in enumerate(self._msgs[:-1]):
            ns, ns_next = self._get_capture_time_diff(msg, self._msgs[i+1])
            err, rate, diff = self._get_msg_rate_and_error(ns, ns_next)
            self.msg_rates.append(rate)
            if abs(err) > ERROR_THRESHOLD:
                self.error_over_threshold.append(err)
                irregularities_counter += 1
                self._logger.warning(f'{PtpType.get_ptp_type_str(self._msgs[i+1])} msg capture time is irregular with '\
                    f'time difference above delta, msg rate: {rate:.3f}, Time diff: {diff} ns, '\
                    f'Time err: {err/1000} us\n\t' + self._msg_sequence_and_time_info(self._msgs[i+1]))
        if irregularities_counter == 0:
            self._logger.info(f'All {self.processed_ptp_type} msgs within threshold. Capture time regularity: OK')
            return True
        else:
            self._logger.warning(f'Number of capture time irregularities of {self.processed_ptp_type}: {irregularities_counter}')
            return False
            
    def _analyse_timestamp_regularity(self):
        irregularities_counter = 0 
        self._logger.debug(f'Analyse Timestamp regularity of {self.processed_ptp_type}:'\
                        f'\n\tExpected time diff for {self._msg_interval} is: {self._msg_interval.value/1000} us., '\
                        f'allowed delta set to: {ERROR_THRESHOLD/1000} us.')
        for i, msg in enumerate(self._msgs[:-1]): 
            if PtpType.is_sync(msg) or PtpType.is_announce(msg):
                if msg.originTimestamp["s"] == 0:
                    return False   
                ns, ns_next = self._get_sync_timestamp_diff(msg, self._msgs[i+1])
            if  PtpType.is_followup(msg):
                ns, ns_next = self._get_followup__timestamp_diff(msg, self._msgs[i+1])
            err, rate, diff = self._get_msg_rate_and_error(ns, ns_next)
            self.capture_rates.append(rate)
            if abs(err) > ERROR_THRESHOLD:
                self.capture_error_over_threshold.append(err)
                irregularities_counter += 1
                self._logger.warning(f'{PtpType.get_ptp_type_str(self._msgs[i+1])} msg timestamp is irregular with '\
                    f'time difference above delta, msg rate: {rate:.3f}, Time diff: {diff} ns, '\
                    f'Time err: {err/1000} us\n\t' + self._msg_sequence_and_time_info(self._msgs[i+1]))
        if irregularities_counter == 0 :
            self._logger.info(f'All {self.processed_ptp_type} msgs within threshold. Timestamp regularity: OK')
            return True
        else:
            self._logger.warning(f'Number of timestamp time irregularities of {self.processed_ptp_type}: {irregularities_counter}')
            return False
    
    def _get_capture_time_diff(self, msg, msg_n):
        ns = msg.time * ONE_SEC_IN_NS
        ns_next = msg_n.time * ONE_SEC_IN_NS
        return (int(ns), int(ns_next))
                
    def _get_msg_rate_and_error(self, ns, ns_next):
        t1_diff = ns_next - ns
        if t1_diff < 0: 
            t1_diff = ONE_SEC_IN_NS - ns + ns_next
        rate = ONE_SEC_IN_NS / t1_diff
        err = t1_diff - self._msg_interval.value
        return (err, rate, t1_diff)
        
    def _get_sync_timestamp_diff(self, msg, msg_n):
        ns = msg.originTimestamp["ns"]  
        ns_next = msg_n.originTimestamp["ns"]
        return (ns, ns_next)
    
    def _get_followup__timestamp_diff(self, msg, msg_n):
        ns = msg.preciseOriginTimestamp["ns"]  
        ns_next = msg_n.preciseOriginTimestamp["ns"]
        return (ns, ns_next)
        
    def _msg_sequence_and_time_info(self, msg):
        t = time.strftime('%H:%M:%S', time.localtime(msg.time))
        return f'Capture time: {t},\tCapture offset: {msg.time-self._time_offset:.9f},\tSequence ID: {msg.sequenceId}'
    
    def _is_input_valid(self):
        ptp_type = PtpType.get_ptp_msg_type(self._msgs[0])
        for msg in self._msgs:
            if PtpType.get_ptp_msg_type(msg) != ptp_type:
                return False
        return True
    
    @property
    def msgs(self):
        return self._msgs
    
    @property
    def success(self):
        return self._status_ok

    def __repr__(self):
        if len(self.msg_rates) == 0 or len(self._msgs) == 0 or len(self.capture_rates) == 0:
            return 'Ptp Timing: not enough data'
        return f'Ptp Timing of {PtpType.get_ptp_type_str(self._msgs[0])}:\nTimestamps:\n\tmean msg rate: {statistics.mean(self.msg_rates):.9f},'\
            f'\n\tstd dev msg rate: {statistics.stdev(self.msg_rates):.9f}, \n\tmin msg rate: {np.min(self.msg_rates):.9f},\n\t'\
            f'max msg rate: {np.max(self.msg_rates):.9f},\n\tnumber of msgs with irregularity above the limit: {len(self.error_over_threshold)}'\
            f'\nCapture time\n\tmean capture rate: {statistics.mean(self.capture_rates):.9f},\n\tstd dev capture rate: '\
            f'{statistics.stdev(self.capture_rates):.9f}, \n\tmin capture rate: {np.min(self.capture_rates):.9f},\n\tmax capture rate: '\
            f'{np.max(self.capture_rates):.9f},\n\tnumber of msgs captured with irregularity above the limit: {len(self.error_over_threshold)}\n'
