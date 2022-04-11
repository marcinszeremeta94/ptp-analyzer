from .PTPv2 import PtpType


class PtpSequenceId:

    def __init__(self, logger, time_offset=0):
        self.__logger = logger
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
        delay_resp_fup_correct = self._is_same_len(dresp_fup, dresp)
        delay_resp_fup_correct &= self._is_sequence_in_order(dresp_fup)
        delay_resp_fup_correct &= self._is_sequence_in_superset(dresp, dresp_fup)
        if delay_resp_fup_correct:
            self.__logger.info('Delay Resp follow-up msg sequenceId: [OK]')

    def _check_sync_sequence_correctness(self, sync):
        if self._is_sequence_in_order(sync):
            self.__logger.info('Sync msg sequenceId: [OK]')

    def _check_followup_sequence_correctness(self, sync, followup):
        if len(followup) == 0:
            return
        followup_correct = self._is_same_len(sync, followup)
        followup_correct &= self._is_sequence_in_order(followup)
        followup_correct &= self._is_sequence_in_superset(sync, followup)
        if followup_correct:
            self.__logger.info('Follow-up msg sequenceId: [OK]')

    def _check_delay_req_sequence_correctness(self, dreq, dresp):
        delay_req_correct = self._is_same_len(dreq, dresp)
        delay_req_correct &= self._is_sequence_in_order(dreq)
        if delay_req_correct:
            self.__logger.info('Delay Req msg sequenceId: [OK]')

    def _check_delay_resp_sequence_correctness(self, dreq, dresp):
        if len(dresp) == 0:
            return
        delay_resp_correct = self._is_sequence_in_order(dresp)
        delay_resp_correct &= self._is_sequence_in_superset(dreq, dresp)
        if delay_resp_correct:
            self.__logger.info('Delay Resp msg sequenceId: [OK]')

    def _is_same_len(self, arg1, arg2):
        if len(arg1) != len(arg2):
            self.__logger.warning(f'Number of {PtpType.get_ptp_type_str(arg1)} and'
                                  f'{PtpType.get_ptp_type_str(arg2)} messages mismatch!')
            return False
        return True

    def _is_sequence_in_order(self, ptp_frames):
        SEQUENCE_ID_SATURATION_DIFF = -0xFFFE
        status = True
        for i, frame in enumerate(ptp_frames[:-1]):
            diff = ptp_frames[i+1].sequenceId - frame.sequenceId
            if diff != 1 and diff != SEQUENCE_ID_SATURATION_DIFF:
                self._log_mismatch(frame, ptp_frames[i+1], diff)
                status = False
        return status

    def _is_sequence_in_superset(self, collection, subset):
        missing_seq = set([msg.sequenceId for msg in collection]
                          ) - set([msg.sequenceId for msg in subset])
        if len(missing_seq) > 0:
            self.__logger.warning(f'{PtpType.get_ptp_type_str(collection[0])} missing msgs to '
                                  f'{PtpType.get_ptp_type_str(subset[0])} msgs with Id: {missing_seq}')
            return False
        return True

    def _log_mismatch(self, frame, next_f, diff):
        self.__logger.warning(
            f'{PtpType.get_ptp_type_str(frame)} msg sequenceId mismatch with next msg: diff: {diff}, Next id: {next_f.sequenceId}')
        self.__logger.msg_timing(frame, self.time_offset)
