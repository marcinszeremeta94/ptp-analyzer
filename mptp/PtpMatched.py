from mptp.Logger import Logger
from .PTPv2 import PTPv2, PtpType
from dataclasses import dataclass
import enum
import time
import copy
import numpy as np
import statistics

ONE_SEC_IN_NS = 1000000000
ONE_SEC_IN_US = 1000000
ONE_SEC_IN_MS = 1000


@dataclass
class Ptp1StepExchenge:
    sync = PTPv2()
    delay_req = PTPv2()
    delay_resp = PTPv2()
    sync_to_delay_req_time = int()
    delay_req_to_resp_time = int()

    def __repr__(self) -> str:
        return f'Delay Sync-to-Delay_Req: {self.sync_to_delay_req_time}, Delay_req-to-Delay_Resp: {self.delay_req_to_resp_time}\n'


class PtpMatched:

    class DispatcherState(enum.IntEnum):
        NEW_EXCHANGE = 1
        GOT_SYNC = 2
        WAITING_AT_RESP = 3

    def __init__(self, logger: Logger, packets, time_offset=0):
        self.time_offset = time_offset
        self._logger = logger
        self._ptp_msg_exchange = []
        self._unmatched_all = []
        self._unmatched_syncs = []
        self._unmatched_delay_reqs = []
        self._unmatched_delay_resps = []
        self._dispatcher_state = self.DispatcherState.NEW_EXCHANGE
        self._current_processed_exchange = Ptp1StepExchenge()
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

    def _add_new_exchange(self, p):
        self._update_current_time_differences()
        if(self._current_processed_exchange.sync_to_delay_req_time < 0 or self._current_processed_exchange.delay_req_to_resp_time < 0):
            self._unmatched_syncs.append(self._current_processed_exchange.sync)
            self._unmatched_delay_reqs.append(self._current_processed_exchange.delay_req)
            self._unmatched_delay_resps.append(p)
            self._unmatched_all.append(p)
            self._logger.error(f'PTP Exchange pcap time went back in time. Sync-to-Delay_Req: '
                                 f'{self._current_processed_exchange.sync_to_delay_req_time} us, Delay_Req-to-Delay_Resp: '
                                 f'{self._current_processed_exchange.delay_req_to_resp_time} us. Exchange Discarded!')
            self._logger.msg_timing(self._current_processed_exchange.sync, self.time_offset)
        else:
            self._ptp_msg_exchange.append(copy.deepcopy(self._current_processed_exchange))

    def _update_current_time_differences(self):
        self._current_processed_exchange.sync_to_delay_req_time = (
            self._current_processed_exchange.delay_req.time - self._current_processed_exchange.sync.time) * ONE_SEC_IN_US
        self._current_processed_exchange.delay_req_to_resp_time = (
            self._current_processed_exchange.delay_resp.time - self._current_processed_exchange.delay_req.time) * ONE_SEC_IN_US

    def _log_state(self):
        self._logger.new_line()
        self._log_unordered_msgs()
        self._log_statistics()
        self._logger.info(self.__repr__())

    def _log_statistics(self):
        sync_to_delay = [
            exchange.sync_to_delay_req_time for exchange in self._ptp_msg_exchange]
        if len(sync_to_delay) != 0:
            self._logger.info(f'Sync message to Delay Request message capture time in matched PTP messages exchange:\n\tmean: '
                              f'{statistics.mean(sync_to_delay):.3f} ms,\n\tstd dev: {statistics.stdev(sync_to_delay):.3f} ms,\n\tmin: '
                              f'{np.min(sync_to_delay):.3f} ms,\n\tmax: {np.max(sync_to_delay):.3f} ms')
        delay_req_resp_delay = [
            exchange.delay_req_to_resp_time for exchange in self._ptp_msg_exchange]
        if len(delay_req_resp_delay) != 0:
            self._logger.info(f'Delay Request message to Delay Response message  capture time in matched PTP messages '
                              f'exchange:\n\tmean: {statistics.mean(delay_req_resp_delay):.3f} ms,\n\tstd dev: '
                              f'{statistics.stdev(delay_req_resp_delay):.3f} ms,\n\tmin: {np.min(delay_req_resp_delay):.3f} ms,'
                              f'\n\tmax: {np.max(delay_req_resp_delay):.3f} ms')

    def _log_unordered_msgs(self):
        for msg in self._unmatched_all:
            if PtpType.is_sync(msg):
                self._logger.warning(
                    f'Unhandled SYNC__MSG:' + self._msg_sequence_and_time_info(msg))
            elif PtpType.is_delay_req(msg):
                self._logger.warning(
                    f'Unordered DELAY_REQ:' + self._msg_sequence_and_time_info(msg))
            elif PtpType.is_delay_resp(msg):
                self._logger.warning(
                    f'Unordered DELAY_RES:' + self._msg_sequence_and_time_info(msg))

    def _msg_sequence_and_time_info(self, msg):
        t = time.strftime('%H:%M:%S', time.localtime(msg.time))
        return f'   Capture time: {t},    Capture offset: {msg.time-self.time_offset:.9f},\tSequence ID: {msg.sequenceId}'

    def __repr__(self):
        return f'Ptp Signal Match 1-step Sequence:\n\tPtp Exchanges (Sync-D_Req-D_Resp): {len(self._ptp_msg_exchange)},'\
            f'\n\tDiscarded (unhandled) Sync Msgs: {len(self._unmatched_syncs)},\n\tDiscarded (unordered) Delay Reqs: '\
            f'{len(self._unmatched_delay_reqs)},\n\tDiscarded (unordered) Delay Resps: {len(self._unmatched_delay_resps)},'
