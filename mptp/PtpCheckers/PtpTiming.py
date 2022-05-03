from appcommon.AppLogger.ILogger import ILogger
from mptp.PtpPacket.PTPv2 import PTPv2, PtpType
from typing import List
from enum import IntEnum
import time
import statistics

ONE_SEC_IN_NS = 1000000000


class MsgInterval(IntEnum):
    # Value is time diff between msgs in ns
    Rate_16 = 62_500_000
    Rate_8 = 125_000_000
    Rate_4 = 250_000_000
    Rate_2 = 500_000_000
    Rate_1 = 1_000_000_000
    Unknown = 0

def rate_to_str(rate: MsgInterval) -> str:
    if rate == MsgInterval.Rate_1:
        return "Rate: 1 message per second"
    elif rate == MsgInterval.Rate_2:
        return "Rate: 2 messages per second"
    elif rate == MsgInterval.Rate_4:
        return "Rate: 4 messages per second"
    elif rate == MsgInterval.Rate_8:
        return "Rate: 8 messages per second"
    elif rate == MsgInterval.Rate_16:
        return "Rate: 16 messages per second"
    else:
        return ""

# This analysis makes sense for ptp msgs like announce, sync and follow-up
class PtpTiming:
    def __init__(self, logger: ILogger, packets: List[PTPv2], time_offset=0, ptp_rate_err = 0.01):
        if len(packets) == 0:
            self._msgs = []
            return
        self._msgs = packets
        self._time_offset = time_offset
        self._logger = logger
        self._msg_interval = self._get_msg_rate_out_of_capture(packets)
        self.ERROR_THRESHOLD = self._get_concrete_err_threshold_from_percentage(ptp_rate_err)
        self._status_ok = True
        self.error_over_threshold = []
        self.msg_rates = []
        self.capture_error_over_threshold = []
        self.capture_rates = []
        self.processed_ptp_type = PtpType.get_ptp_msg_type(self._msgs[0]) if packets else None
        if not self._is_input_valid():
            self._status_ok = False
            return
        self._status_ok &= self._analyse_timestamp_regularity()
        self._status_ok &= self._analyse_capture_time_regularity()
        self._logger.info(self.__repr__())
                   

    def _analyse_capture_time_regularity(self):
        if self._msg_interval == MsgInterval.Unknown:
            return False
        self._logger.debug(
            f"Analyse capture time regularity of {self.processed_ptp_type}:"
            f"\n\tExpected time diff for {rate_to_str(self._msg_interval)} is: {self._msg_interval.value/1000} us., "
            f"allowed delta set to: {self.ERROR_THRESHOLD/1000} us."
        )
        for i, msg in enumerate(self._msgs[:-1]):
            ns, ns_next = self._get_capture_time_diff(msg, self._msgs[i + 1])
            err, rate, diff = self._get_msg_rate_and_error(ns, ns_next)
            self.capture_rates.append(rate)
            if abs(err) > self.ERROR_THRESHOLD:
                self.capture_error_over_threshold.append(err)
                self._logger.warning(
                    f"{PtpType.get_ptp_type_str(self._msgs[i+1])} msg capture time is irregular with "
                    f"time difference above delta, msg rate: {rate:.3f}, Time diff: {diff} ns, "
                    f"Time err: {err/1000} us\n"
                    + self._msg_sequence_and_time_info(self._msgs[i + 1])
                )
        if len(self.capture_error_over_threshold) == 0:
            self._logger.info(
                f"All {self.processed_ptp_type} msgs within threshold. Capture time regularity: OK"
            )
            return True
        else:
            self._logger.warning(
                f"Number of capture time irregularities of {self.processed_ptp_type}: {len(self.capture_error_over_threshold)}"
            )
            return False

    def _analyse_timestamp_regularity(self):
        self._logger.debug(
            f"Analyse Timestamp regularity of {self.processed_ptp_type}:"
            f"\n\tExpected time diff for{rate_to_str(self._msg_interval)} is: {self._msg_interval.value/1000} us., "
            f"allowed delta set to: {self.ERROR_THRESHOLD/1000} us."
        )
        for i, msg in enumerate(self._msgs[:-1]):
            if PtpType.is_sync(msg) or PtpType.is_announce(msg):
                if msg.originTimestamp["s"] == 0:
                    return False
                ns, ns_next = self._get_sync_timestamp_diff(msg, self._msgs[i + 1])
            if PtpType.is_followup(msg):
                ns, ns_next = self._get_followup__timestamp_diff(msg, self._msgs[i + 1])
            err, rate, diff = self._get_msg_rate_and_error(ns, ns_next)
            self.msg_rates.append(rate)
            if abs(err) > self.ERROR_THRESHOLD:
                self.error_over_threshold.append(err)
                self._logger.warning(
                    f"{PtpType.get_ptp_type_str(self._msgs[i+1])} msg timestamp is irregular with "
                    f"time difference above delta, msg rate: {rate:.3f}, Time diff: {diff} ns, "
                    f"Time err: {err/1000} us\n"
                    + self._msg_sequence_and_time_info(self._msgs[i + 1])
                )
        if len(self.error_over_threshold) == 0:
            self._logger.info(
                f"All {self.processed_ptp_type} msgs within threshold. Timestamp regularity: OK"
            )
            return True
        else:
            self._logger.warning(
                f"Number of timestamp time irregularities of {self.processed_ptp_type}: {len(self.error_over_threshold)}"
            )
            return False
        
    def _get_msg_rate_out_of_capture(self, msgs) -> MsgInterval:
        for i, msg in enumerate(msgs[:-1]):
            ns, ns_next = self._get_capture_time_diff(msg, self._msgs[i + 1])
            rate = self._get_msg_rate_from_neighbor_msgs(ns, ns_next)
            msg_rates: List[float] = []
            msg_rates.append(rate)
            mean_rate = statistics.mean(msg_rates)
            msg_interval = self._meanToMsgRate(mean_rate)
            if msg_interval is MsgInterval.Unknown:
                self._logger.error("Unable to determin msg rate")
            self._logger.info(f"Detected {rate_to_str(msg_interval)} of {PtpType.get_ptp_type_str(msg[0])}")
            return msg_interval

    def _meanToMsgRate(self, rate: float) -> MsgInterval:
        RATE_MAX_DELTA_COEFFICIENT = 0.3    # 30%
        if self._isBetweenDelta(rate, 1, RATE_MAX_DELTA_COEFFICIENT):
            return MsgInterval.Rate_1
        elif self._isBetweenDelta(rate, 2, RATE_MAX_DELTA_COEFFICIENT):
            return MsgInterval.Rate_2
        elif self._isBetweenDelta(rate, 4, RATE_MAX_DELTA_COEFFICIENT):
            return MsgInterval.Rate_4
        elif self._isBetweenDelta(rate, 8, RATE_MAX_DELTA_COEFFICIENT):
            return MsgInterval.Rate_8
        elif self._isBetweenDelta(rate, 16, RATE_MAX_DELTA_COEFFICIENT):
            return MsgInterval.Rate_16
        else:
            return MsgInterval.Unknown

    def _isBetweenDelta(self, rate: float, val: int, delta: float) -> bool:
        return (val - (val * delta)) < rate < (val + (val * delta))
     
    def _get_capture_time_diff(self, msg, msg_n):
        ns = msg.time * ONE_SEC_IN_NS
        ns_next = msg_n.time * ONE_SEC_IN_NS
        return (int(ns), int(ns_next))
    
    def _get_concrete_err_threshold_from_percentage(self, percentage: float) -> int:
        threshold = int(self._msg_interval.value * percentage)
        self._logger.info(f'Allowed Threshold: {threshold}, what is {percentage*100}% of msgs time difference')
        return threshold
        

    def _get_msg_rate_and_error(self, ns, ns_next):
        t1_diff = ns_next - ns
        if t1_diff < 0:
            t1_diff = ONE_SEC_IN_NS - ns + ns_next
        rate = ONE_SEC_IN_NS / t1_diff
        err = t1_diff - self._msg_interval.value
        return (err, rate, t1_diff)
    
    def _get_msg_rate_from_neighbor_msgs(self, ns, ns_next):
        t1_diff = ns_next - ns
        if t1_diff < 0:
            t1_diff = ONE_SEC_IN_NS - ns + ns_next
        rate = ONE_SEC_IN_NS / t1_diff
        return rate

    def _get_sync_timestamp_diff(self, msg, msg_n):
        ns = msg.originTimestamp["ns"]
        ns_next = msg_n.originTimestamp["ns"]
        return (ns, ns_next)

    def _get_followup__timestamp_diff(self, msg, msg_n):
        ns = msg.preciseOriginTimestamp["ns"]
        ns_next = msg_n.preciseOriginTimestamp["ns"]
        return (ns, ns_next)

    def _msg_sequence_and_time_info(self, msg):
        t = time.strftime("%H:%M:%S", time.localtime(msg.time))
        return f"[TIME] Capture time: {t},\tCapture offset: {msg.time-self._time_offset:.9f},\tSequence ID: {msg.sequenceId}"

    def _is_input_valid(self):
        if len(self._msgs) == 0:
            return False
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

    def __repr__(self) -> str:
        if (
            len(self.msg_rates) == 0
            or len(self._msgs) == 0
            or len(self.capture_rates) == 0
        ):
            return "Ptp Timing: not enough data"
        return (
            f"Ptp Timing of {PtpType.get_ptp_type_str(self._msgs[0])}:\nTimestamps:\n\tmean msg rate: {statistics.mean(self.msg_rates):.9f},"
            f"\n\tstd dev msg rate: {statistics.stdev(self.msg_rates):.9f}, \n\tmin msg rate: {min(self.msg_rates):.9f},\n\t"
            f"max msg rate: {max(self.msg_rates):.9f},\n\tnumber of msgs with irregularity above the limit: {len(self.error_over_threshold)}"
            f"\nCapture time\n\tmean capture rate: {statistics.mean(self.capture_rates):.9f},\n\tstd dev capture rate: "
            f"{statistics.stdev(self.capture_rates):.9f}, \n\tmin capture rate: {min(self.capture_rates):.9f},\n\tmax capture rate: "
            f"{max(self.capture_rates):.9f},\n\tnumber of msgs captured with irregularity above the limit: {len(self.capture_error_over_threshold)}\n"
        )
