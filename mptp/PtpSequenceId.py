from .PTPv2 import PTPv2, PtpType
from .Logger import Logger


class PtpSequenceId:

    def __init__(self, logger: Logger, time_offset=0):
        self._logger = logger
        self.time_offset = time_offset

    def check_sync_followup_sequence(self, sync, followup):
        self._check_sync_sequence_correctness(sync)
        self._check_followup_sequence_correctness(sync, followup)

    def check_delay_req_resp_sequence(self, dreq, dresp):
        self._check_delay_req_sequence_correctness(dreq, dresp)
        self._check_delay_resp_sequence_correctness(dreq, dresp)

    def check_dresp_dresp_fup_sequence(self, dresp, dresp_fup):
        if len(dresp_fup) == 0:
            return
        self._logger.banner_small('delay request follow-up message sequence id')
        delay_resp_fup_correct = self._is_same_len(dresp_fup, dresp)
        delay_resp_fup_correct &= self._is_sequence_in_order(dresp_fup)
        delay_resp_fup_correct &= self._is_sequence_in_superset(dresp, dresp_fup)
        if delay_resp_fup_correct:
            self._logger.info('Delay Resp Follow-up msg sequenceId: [OK]')

    def _check_sync_sequence_correctness(self, sync):
        if len(sync) == 0:
            return
        self._logger.banner_small('Sync message sequence id')
        if self._is_sequence_in_order(sync):
            self._logger.info('Sync msg sequenceId: [OK]')

    def _check_followup_sequence_correctness(self, sync, followup):
        if len(followup) == 0:
            return
        self._logger.banner_small('Follow-up message sequence id')
        followup_correct = self._is_same_len(sync, followup)
        followup_correct &= self._is_sequence_in_order(followup)
        followup_correct &= self._is_sequence_in_superset(sync, followup)
        if followup_correct:
            self._logger.info('Follow-up msg sequenceId: [OK]')

    def _check_delay_req_sequence_correctness(self, dreq, dresp):
        if len(dreq) == 0:
            return
        self._logger.banner_small('delay request message sequence id')
        delay_req_correct = self._is_same_len(dreq, dresp)
        delay_req_correct &= self._is_sequence_in_order(dreq)
        if delay_req_correct:
            self._logger.info('Delay Req msg sequenceId: [OK]')

    def _check_delay_resp_sequence_correctness(self, dreq, dresp):
        if len(dresp) == 0:
            return
        self._logger.banner_small('delay resp message sequence id')
        delay_resp_correct = self._is_sequence_in_order(dresp)
        delay_resp_correct &= self._is_sequence_in_superset(dreq, dresp)
        if delay_resp_correct:
            self._logger.info('Delay Resp msg sequenceId: [OK]')

    def _is_same_len(self, arg1, arg2) -> bool:
        if len(arg1) != len(arg2):
            self._logger.info(f'Number of {PtpType.get_ptp_type_str(arg1[0])} and'
                              f'{PtpType.get_ptp_type_str(arg2[0])} messages mismatch!')
            return False
        return True

    def _is_sequence_in_order(self, ptp_frames) -> bool:
        SEQUENCE_ID_SATURATION_DIFF = -0xFFFE
        inconsistent_counter = 0
        for frame, next_frame in zip(ptp_frames[:-1], ptp_frames[1:]):
            diff = next_frame.sequenceId - frame.sequenceId
            if diff != 1 and diff != SEQUENCE_ID_SATURATION_DIFF:
                self._log_mismatch(frame, next_frame, diff)
                inconsistent_counter += 1
        if inconsistent_counter > 0:
            self._log_inconsistency(ptp_frames[0], inconsistent_counter)
        return inconsistent_counter == 0
    
    def _is_sequence_in_superset(self, collection, subset) -> bool:
        missing_seq = set([msg.sequenceId for msg in collection]) - set([msg.sequenceId for msg in subset])
        if len(missing_seq) > 0:
            self._logger.info(f'{PtpType.get_ptp_type_str(collection[0])} missing msgs to '
                                 f'{PtpType.get_ptp_type_str(subset[0])} msgs with Id: {missing_seq}')
            return False
        return True

    def _log_inconsistency(self, frame: PTPv2, counter: int):
        self._logger.info(f'{PtpType.get_ptp_type_str(frame)} number of sequence Id inconsistencies: {counter}')
    
    def _log_mismatch(self, frame: PTPv2, next_f: PTPv2, diff: int):
        self._logger.warning(
            f'{PtpType.get_ptp_type_str(frame)} msg sequenceId mismatch with next msg: diff: {diff}, Next id: {next_f.sequenceId}')
        self._logger.msg_timing(frame, self.time_offset)
