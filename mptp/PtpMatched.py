import enum
import time
import copy
import statistics
from dataclasses import dataclass
from mptp.Logger import Logger
from .PTPv2 import PTPv2, PtpType

ONE_SEC_IN_NS = 1000000000
ONE_SEC_IN_US = 1000000
ONE_SEC_IN_MS = 1000


@dataclass
class Ptp1StepExchenge:
    sync = PTPv2()
    delay_req = PTPv2()
    delay_resp = PTPv2()
    t1_t4 = float()
    sync_to_delay_req_time = float()
    delay_req_to_resp_time = float()

    def __repr__(self) -> str:
        return (
            f"Delay Sync-to-Delay_Req: {self.sync_to_delay_req_time}, "
            f"Delay_req-to-Delay_Resp: {self.delay_req_to_resp_time} "
            f"T1-T4 Timestamps difference: {self.t1_t4}\n"
        )


class PtpMatched:
    class DispatcherState(enum.IntEnum):
        NEW_EXCHANGE = 1
        GOT_SYNC = 2
        WAITING_AT_RESP = 3

    def __init__(self, logger: Logger, packets: list[PTPv2], time_offset=0):
        self.time_offset = time_offset
        self._logger = logger
        self._ptp_msg_exchange = []
        self._unmatched_all = []
        self._unmatched_syncs = []
        self._unmatched_delay_reqs = []
        self._unmatched_delay_resps = []
        self._dispatcher_state = self.DispatcherState.NEW_EXCHANGE
        self._current_processed_exchange = Ptp1StepExchenge()
        self._logger.banner_large("ptp one step full sequential message exchange")
        self._add(packets)
        self._log_state()

    @property
    def ptp_exchanges(self):
        return self._ptp_msg_exchange

    @property
    def ptp_unmatched(self):
        return self._unmatched_all

    def _add(self, pkt):
        if type(pkt) == PTPv2:
            self._add_dispatch(pkt)
        elif iter(pkt):
            for p in pkt:
                self._add_dispatch(p)

    def _add_dispatch(self, p):
        if PtpType.is_sync(p):
            self._add_sync(p)
        elif PtpType.is_delay_req(p) or PtpType.is_pdelay_req(p):
            self._add_delay_req(p)
        elif PtpType.is_delay_resp(p) or PtpType.is_pdelay_resp(p):
            self._add_delay_resp(p)

    def _add_sync(self, p):
        if self._dispatcher_state == self.DispatcherState.NEW_EXCHANGE:
            self._current_processed_exchange.sync = p
            self._dispatcher_state = self.DispatcherState.GOT_SYNC
        else:
            self._unmatched_syncs.append(self._current_processed_exchange.sync)
            self._unmatched_all.append(self._current_processed_exchange.sync)
            self._current_processed_exchange.sync = p
            self._dispatcher_state = self.DispatcherState.GOT_SYNC

    def _add_delay_req(self, p):
        if self._dispatcher_state == self.DispatcherState.GOT_SYNC:
            self._current_processed_exchange.delay_req = p
            self._dispatcher_state = self.DispatcherState.WAITING_AT_RESP
        else:
            self._unmatched_delay_reqs.append(p)
            self._unmatched_all.append(p)
            self._dispatcher_state = self.DispatcherState.NEW_EXCHANGE

    def _add_delay_resp(self, p):
        if self._dispatcher_state == self.DispatcherState.WAITING_AT_RESP:
            self._current_processed_exchange.delay_resp = p
            self._add_new_exchange(p)
            self._dispatcher_state = self.DispatcherState.NEW_EXCHANGE
        else:
            self._unmatched_delay_resps.append(p)
            self._unmatched_all.append(p)
            self._dispatcher_state = self.DispatcherState.NEW_EXCHANGE

    def _add_new_exchange(self, p: PTPv2):
        self._update_current_time_differences()
        if (
            self._current_processed_exchange.sync_to_delay_req_time < 0
            or self._current_processed_exchange.delay_req_to_resp_time < 0
        ):
            self._unmatched_syncs.append(self._current_processed_exchange.sync)
            self._unmatched_delay_reqs.append(
                self._current_processed_exchange.delay_req
            )
            self._unmatched_delay_resps.append(p)
            self._unmatched_all.append(p)
            self._logger.error(
                f"PTP Exchange pcap time went back in time. Sync-to-Delay_Req: "
                f"{self._current_processed_exchange.sync_to_delay_req_time} us, "
                f"Delay_Req-to-Delay_Resp: "
                f"{self._current_processed_exchange.delay_req_to_resp_time} us. "
                f"Exchange Discarded!"
            )
            self._logger.msg_timing(self._current_processed_exchange.sync, self.time_offset)
        else:
            self._ptp_msg_exchange.append(
                copy.deepcopy(self._current_processed_exchange)
            )

    def _update_current_time_differences(self):
        ns = self._current_processed_exchange.sync.originTimestamp["ns"]
        if PtpType.is_pdelay_resp(self._current_processed_exchange.delay_resp):
            ns_next = (
                self._current_processed_exchange.delay_resp.requestReceiptTimestamp["ns"]
            )
        else:
            ns_next = self._current_processed_exchange.delay_resp.receiveTimestamp["ns"]
        t1_t4 = ns_next - ns
        if t1_t4 < 0:
            t1_t4 = ONE_SEC_IN_NS - ns + ns_next
        self._current_processed_exchange.t1_t4 = t1_t4 / ONE_SEC_IN_MS
        self._current_processed_exchange.sync_to_delay_req_time = (
            self._current_processed_exchange.delay_req.time
            - self._current_processed_exchange.sync.time
        ) * ONE_SEC_IN_US
        self._current_processed_exchange.delay_req_to_resp_time = (
            self._current_processed_exchange.delay_resp.time
            - self._current_processed_exchange.delay_req.time
        ) * ONE_SEC_IN_US

    def _log_state(self):
        self._logger.info(self.__repr__())
        self._logger.banner_small("Unordered ptp messages")
        self._log_unordered_msgs()
        self._logger.banner_small("ptp message exchange statistics")
        self._log_statistics()

    def _log_statistics(self):
        sync_to_delay = [exchange.sync_to_delay_req_time for exchange in self._ptp_msg_exchange]
        if len(sync_to_delay) != 0:
            self._logger.info(
                f"Sync message to Delay Request message capture time in matched PTP messages "
                f"exchange:\n\tmean: {statistics.mean(sync_to_delay):.3f} us,\n\tstd dev: "
                f"{statistics.stdev(sync_to_delay):.3f} us,\n\tmin: {min(sync_to_delay):.3f}"
                f"us,\n\tmax: {max(sync_to_delay):.3f} us"
            )
        d_req_resp_delay = [exchange.delay_req_to_resp_time for exchange in self._ptp_msg_exchange]
        if len(d_req_resp_delay) != 0:
            self._logger.info(
                f"Delay Request message to Delay Response message capture time in matched PTP "
                f"messages  exchange:\n\tmean: {statistics.mean(d_req_resp_delay):.3f} us,"
                f"\n\tstd dev: {statistics.stdev(d_req_resp_delay):.3f} us,\n\tmin: "
                f"{min(d_req_resp_delay):.3f} us,\n\tmax: {max(d_req_resp_delay):.3f} us"
            )
        t1_to_t4 = [exchange.t1_t4 for exchange in self._ptp_msg_exchange]
        if len(t1_to_t4) != 0:
            self._logger.info(
                f"1st Timestamp to 4th Timestamp time difference in full PTP messages exchange"
                f"exchange:\n\tmean: {statistics.mean(t1_to_t4):.3f} us,\n\tstd dev: "
                f"{statistics.stdev(t1_to_t4):.3f} us,\n\tmin: {min(t1_to_t4):.3f} us,"
                f"\n\tmax: {max(t1_to_t4):.3f} us"
            )

    def _log_unordered_msgs(self):
        if len(self._unmatched_all) == 0:
            self._logger.info("There are no unordered messages")
        for msg in self._unmatched_all:
            if PtpType.is_sync(msg):
                self._logger.warning(
                    f"Unhandled SYNC__MSG:" + self._msg_sequence_and_time_info(msg)
                )
            elif PtpType.is_delay_req(msg):
                self._logger.warning(
                    f"Unordered DELAY_REQ:" + self._msg_sequence_and_time_info(msg)
                )
            elif PtpType.is_delay_resp(msg):
                self._logger.warning(
                    f"Unordered DELAY_RES:" + self._msg_sequence_and_time_info(msg)
                )

    def _msg_sequence_and_time_info(self, msg: PTPv2) -> str:
        t = time.strftime("%H:%M:%S", time.localtime(msg.time))
        return (
            f"   Capture time: {t},    Capture offset: {msg.time-self.time_offset:.9f},"
            f"\tSequence ID: {msg.sequenceId}"
        )

    def __repr__(self) -> str:
        return (
            f"Ptp Signal Match 1-step Sequence:\n\tPtp Exchanges (Sync-D_Req-D_Resp): "
            f"{len(self._ptp_msg_exchange)},\n\tDiscarded (unhandled) Sync Msgs: "
            f"{len(self._unmatched_syncs)},\n\tDiscarded (unordered) Delay Reqs: "
            f"{len(self._unmatched_delay_reqs)},\n\tDiscarded (unordered) Delay Resps: "
            f"{len(self._unmatched_delay_resps)},"
        )
