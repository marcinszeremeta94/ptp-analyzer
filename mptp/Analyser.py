import time
from appcommon.AppLogger.ILogger import ILogger
from appcommon.ConfigReader.ConfigReader import ConfigReader
from mptp.PtpStream import PtpStream
from mptp.PtpCheckers.PtpTiming import PtpTiming
from mptp.PtpCheckers.PtpMatched import PtpMatched
from mptp.PtpCheckers.PtpSequenceId import PtpSequenceId
from mptp.PtpCheckers.PtpAnnounceSignal import PtpAnnounceSignal
from mptp.PtpCheckers.PtpPortCheck import PtpPortCheck


class Analyser:
    def __init__(self, config: ConfigReader, logger: ILogger, ptp_stream: PtpStream):
        self._logger: ILogger = logger
        self._config: ConfigReader = config
        self._ptp_stream: PtpStream = ptp_stream
        if len(ptp_stream.ptp_total) > 0:
            t = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ptp_stream.ptp_total[0].time))
            self._logger.info(f"Pcap started at: {t}")
        self._logger.banner_small("counted messages")
        self._logger.info(self._ptp_stream.__repr__())

    def analyse(self):
        if len(self._ptp_stream.ptp_total) == 0:
            self._logger.error("PTP stream empty")
            return
        self.analyse_announce()
        self.analyse_ports()
        self.analyse_sequence_id()
        self.analyse_timings()
        self.analyse_if_stream_match_sequence_of_sync_dreq_dreq_pattern()
        self._logger.banner_small("Finished")
        self._logger.info("Done")

    def analyse_announce(self):
        self._announce_sig = PtpAnnounceSignal(self._logger, self._ptp_stream.time_offset)
        self._announce_sig.check_announce_consistency(self._ptp_stream.announce)

    def analyse_ports(self):
        port_check = PtpPortCheck(self._logger, self._ptp_stream.time_offset)
        port_check.check_ports(self._ptp_stream.ptp_total)

    def analyse_sequence_id(self):
        if len(self._ptp_stream.ptp_total) == 0:
            self._logger.error("PTP stream empty")
            return
        self._logger.banner_large("ptp messages sequence id analysis")
        seq_check = PtpSequenceId(self._logger, self._ptp_stream.time_offset)
        seq_check.check_sync_followup_sequence(self._ptp_stream.sync, self._ptp_stream.follow_up)
        seq_check.check_delay_req_resp_sequence(self._ptp_stream.delay_req, self._ptp_stream.delay_resp)
        seq_check.check_dresp_dresp_fup_sequence(self._ptp_stream.delay_resp, self._ptp_stream.delay_resp_fup)

    def analyse_timings(self):
        if len(self._ptp_stream.ptp_total) == 0:
            self._logger.error("PTP stream empty")
            return
        self._logger.banner_large("ptp timing and rate")
        self._announce_timing = PtpTiming(self._logger, self._ptp_stream.announce, self._ptp_stream.time_offset, self._config.ptp_rate_err)
        self._sync_timing = PtpTiming(self._logger, self._ptp_stream.sync, self._ptp_stream.time_offset, self._config.ptp_rate_err)
        self._followup_timing = PtpTiming(self._logger, self._ptp_stream.follow_up, self._ptp_stream.time_offset, self._config.ptp_rate_err)

    def analyse_if_stream_match_sequence_of_sync_dreq_dreq_pattern(self):
        if len(self._ptp_stream.sync) == 0:
            self._logger.error("No PTP Sync messages")
            return
        self._sync_dreq_dresp_match = PtpMatched(self._logger, self._ptp_stream.ptp_total, self._ptp_stream.time_offset)
