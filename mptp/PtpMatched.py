from dataclasses import dataclass
import enum
from .PTPv2 import PTPv2, PtpType
from enum import Enum
import time
import numpy as np
import statistics

@dataclass
class Ptp1StepExchenge:
    sync = PTPv2()
    delay_req = PTPv2()
    delay_resp = PTPv2()
    sync_to_delay_req_time = int()
    delay_req_to_resp_time = int()
    

class PtpMatched:
    
    class DispatcherState(enum.IntEnum):
        NEW_EXCHANGE = 1
        GOT_SYNC = 2
        WAITING_AT_RESP = 3
    
    def __init__(self, logger, packets=[], time_offset = 0):
        self.time_offset = time_offset
        self.__logger = logger
        self._ptp_msg_exchange = []
        self._announces = []
        self._other_ptp_frames = []
        self._all_ptp_frames = []
        self._unmatched_all = []
        self._unmatched_syncs = []
        self._unmatched_delay_reqs = []
        self._unmatched_delay_resps = []
        self.__dispatcher_state = self.DispatcherState.NEW_EXCHANGE
        self.__current_processed_exchange = Ptp1StepExchenge() 
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
        self._all_ptp_frames.append(p)
        if PtpType.is_announce(p):
            self._announces.append(p)
        elif PtpType.is_sync(p):
            self._add_sync(p)       
        elif PtpType.is_delay_req(p) or PtpType.is_pdelay_req(p):
            self._add_delay_req(p)  
        elif PtpType.is_delay_resp(p) or PtpType.is_pdelay_resp(p):
            self._add_delay_resp(p)
        else: self._other_ptp_frames.append(p)
            
    def _add_sync(self, p):
        if self.__dispatcher_state == self.DispatcherState.NEW_EXCHANGE:
            self.__current_processed_exchange.sync = p
            self.__dispatcher_state = self.DispatcherState.GOT_SYNC
        else:
            self._unmatched_syncs.append(self.__current_processed_exchange.sync)
            self._unmatched_all.append(self.__current_processed_exchange.sync)
            self.__current_processed_exchange.sync = p
            self.__dispatcher_state = self.DispatcherState.GOT_SYNC
            
    def _add_delay_req(self, p):
        if self.__dispatcher_state == self.DispatcherState.GOT_SYNC:
            self.__current_processed_exchange.delay_req = p
            self.__dispatcher_state = self.DispatcherState.WAITING_AT_RESP
        else:
            self._unmatched_delay_reqs.append(p)
            self._unmatched_all.append(p)
            self.__dispatcher_state = self.DispatcherState.NEW_EXCHANGE
            
    def _add_delay_resp(self, p):
        if self.__dispatcher_state == self.DispatcherState.WAITING_AT_RESP:
            self.__current_processed_exchange.delay_resp = p
            self._update_current_time_differences()
            self._ptp_msg_exchange.append(self.__current_processed_exchange)
            self.__dispatcher_state = self.DispatcherState.NEW_EXCHANGE
        else:
            self._unmatched_delay_resps.append(p)
            self._unmatched_all.append(p)
            self.__dispatcher_state = self.DispatcherState.NEW_EXCHANGE
    
    def _update_current_time_differences(self):
        self.__current_processed_exchange.sync_to_delay_req_time = \
                self.__current_processed_exchange.delay_req.time - self.__current_processed_exchange.sync.time
        self.__current_processed_exchange.delay_req_to_resp_time = \
            self.__current_processed_exchange.delay_resp.time - self.__current_processed_exchange.delay_req.time                                 
        
    def _log_state(self):
        self.__logger.new_line()
        self._log_unordered_msgs()
        self._log_statistics()
        self.__logger.info(self.__repr__())
        
    def _log_statistics(self):
        sync_to_delay = [exchange.sync_to_delay_req_time for exchange in self.ptp_exchanges]
        if len(sync_to_delay) != 0:
            if np.min(sync_to_delay) == np.max(sync_to_delay):
                self.__logger.info(f'Sync to Delay_Req capture time in matched exchange is constant. time: {np.max(sync_to_delay)}')
            else:
                self.__logger.info(f'Sync to Delay_Req capture time in matched exchange:\n\tmean: {statistics.mean(sync_to_delay)},\n\t'\
                    f'std dev: {statistics.stdev(sync_to_delay)},\n\tmin: {np.min(sync_to_delay)},\n\tmax: {np.max(sync_to_delay)}')       
        delay_req_resp_delay = [exchange.delay_req_to_resp_time for exchange in self.ptp_exchanges]
        if len(delay_req_resp_delay) != 0:
            if np.min(delay_req_resp_delay) == np.max(delay_req_resp_delay):
                self.__logger.info(f'Delay_Req to Delay_Resp capture time in matched exchange is constant. time: {np.max(sync_to_delay)}')
            else:
                self.__logger.info(f'Delay_Req to Delay_Resp capture time in matched exchange:\n\tmean: {statistics.mean(delay_req_resp_delay)},\n\t'\
                    f'std dev: {statistics.stdev(delay_req_resp_delay)},\n\tmin: {np.min(delay_req_resp_delay)},\n\tmax: {np.max(delay_req_resp_delay)}')         
    
    def _log_unordered_msgs(self):
        for msg in self._unmatched_all:
            if PtpType.is_sync(msg):
                self.__logger.warning(f'Unhandled SYNC__MSG:' + self._msg_sequence_and_time_info(msg))
            elif PtpType.is_delay_req(msg):
                self.__logger.warning(f'Unordered DELAY_REQ:' + self._msg_sequence_and_time_info(msg))
            elif PtpType.is_delay_resp(msg):
                self.__logger.warning(f'Unordered DELAY_RES:' + self._msg_sequence_and_time_info(msg))              
    
    def _msg_sequence_and_time_info(self, msg):
        t = time.strftime('%H:%M:%S', time.localtime(msg.time))
        return f'   Capture time: {t},    Capture offset: {msg.time-self.time_offset:.9f},\tSequence ID: {msg.sequenceId}'
            
    def __repr__(self):
        return f'Ptp Signal 1-step:\n\tAnnounce messages: {len(self._announces)},\n\tPtp Exchanges (SYNC-D_REQ-D_RESP): {len(self._ptp_msg_exchange)},'\
                f'\n\tDiscarded (unhandled) Sync Msgs: {len(self._unmatched_syncs)},\n\tDiscarded (unordered) Delay Reqs: {len(self._unmatched_delay_reqs)},'\
                f'\n\tDiscarded (unordered) Delay Resps: {len(self._unmatched_delay_resps)},'\
                f'\n\tOther PTP frames: {len(self._other_ptp_frames)} \n\tPTP frames total: {len(self._all_ptp_frames)}'
