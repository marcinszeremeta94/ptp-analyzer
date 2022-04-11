from mptp.Logger import Logger
from .PTPv2 import PTPv2, PtpType


class PtpPortCheck:

    MINIMAL_MESSAGE_NUMBER_REQUIRED = 5

    def __init__(self, logger: Logger, time_offset=0):
        self._logger = logger
        self._inconsistency_counter = 0
        self.time_offset = time_offset
        self.ptp_eth_source_port = None
        self.ptp_eth_slave_port = None
        self.ptp_eth_source_destination = None
        self.ptp_eth_slave_destination = None
        self.ptp_source_clk_id = None
        self.ptp_slave_clk_id = None

    def check_ports(self, ptp_stream):
        self._inconsistency_counter = 0
        if len(ptp_stream) < self.MINIMAL_MESSAGE_NUMBER_REQUIRED:
            self._logger.info('Not enough PTP messages to perform valid port check. ')
        self._logger.banner_large('PTP message MAC address and clock id analysis')
        for msg in ptp_stream:
            if PtpType.is_announce(msg) or PtpType.is_sync(msg) or PtpType.is_followup(msg):
                self._check_sync_fup_announce_ports(msg)
            elif PtpType.is_delay_req(msg) or PtpType.is_pdelay_req(msg):
                self._check_dreq_ports(msg)
            elif PtpType.is_delay_resp(msg) or PtpType.is_pdelay_resp(msg) or PtpType.is_delay_resp_followup:
                self._check_dresp_ports(msg)
        if self._inconsistency_counter:
            self._logger.info(f'PTP Clock ID and MAC number of issues found: {self._inconsistency_counter}')
        else:
            self._logger.info(f'PTP Clock ID and MAC addresses: [OK]')
        self._logger.info(self.__repr__())

    def _check_sync_fup_announce_ports(self, msg: PTPv2):
        self._initial_source_values(msg)
        if self.ptp_eth_source_port != msg.src or self.ptp_eth_source_destination != msg.dst or \
                self.ptp_source_clk_id != msg.sourcePortIdentity:
            self._inconsistency_counter += 1
            self._log_sync_announce_followup_issue(msg)
            self._reset_source_data()

    def _check_dreq_ports(self, msg: PTPv2):
        self._initial_slave_values(msg)
        if self.ptp_eth_slave_port != msg.src or self.ptp_eth_slave_destination != msg.dst or \
                self.ptp_slave_clk_id != msg.sourcePortIdentity:
            self._inconsistency_counter += 1
            self._log_delay_request_issue(msg)
            self._reset_slave_data()

    def _check_dresp_ports(self, msg: PTPv2):
        if self.ptp_eth_slave_port is None:
            return
        if self.ptp_eth_source_port != msg.src or self.ptp_eth_source_destination != msg.dst or \
                self.ptp_source_clk_id != msg.sourcePortIdentity or self.ptp_slave_clk_id != msg.requestingPortIdentity:
            self._inconsistency_counter += 1
            self.__log_delay_response_issue(msg)

    def _initial_source_values(self, msg: PTPv2):
        if self.ptp_eth_source_port is None:
            self.ptp_eth_source_port = msg.src
        if self.ptp_eth_source_destination is None:
            self.ptp_eth_source_destination = msg.dst
        if self.ptp_source_clk_id is None:
            self.ptp_source_clk_id = msg.sourcePortIdentity

    def _initial_slave_values(self, msg: PTPv2):
        if self.ptp_slave_clk_id is None:
            self.ptp_slave_clk_id = msg.sourcePortIdentity
        if self.ptp_eth_slave_port is None:
            self.ptp_eth_slave_port = msg.src
        if self.ptp_eth_slave_destination is None:
            self.ptp_eth_slave_destination = msg.dst

    def _reset_source_data(self):
        self.ptp_eth_source_port = None
        self.ptp_eth_source_destination = None
        self.ptp_source_clk_id = None
        
    def _reset_slave_data(self):
        self.ptp_eth_slave_port = None
        self.ptp_eth_slave_destination = None
        self.ptp_slave_clk_id = None
    
    def _is_mac_multicast(self, mac: str) -> bool:
        if mac is None:
            return False
        return mac[1:2] == '1'

    def _log_sync_announce_followup_issue(self, msg):
        self._logger.warning(
            f'{PtpType.get_ptp_type_str(msg)} msg inconsistent with previous port data!\nRegistered port data:'
            f'\n\tSource MAC: {self.ptp_eth_source_port},\n\tDestination MAC: {self.ptp_eth_source_destination},'
            f'\n\tSource Clk ID and Port: {self.ptp_source_clk_id},\nProcessing message port data:'
            f'\n\tSource MAC: {msg.src},\n\tDestination MAC: {msg.dst},'
            f'\n\tSource Clk ID and Port: {msg.sourcePortIdentity}')
        self._logger.msg_timing(msg, self.time_offset)

    def _log_delay_request_issue(self, msg):
        self._logger.warning(
            f'Delay Request msg inconsistent with previous port data!\nRegistered port data:'
            f'\n\tSlave MAC: {self.ptp_eth_slave_port},\n\tDestination MAC: {self.ptp_eth_slave_destination},'
            f'\n\tSlave Clk ID and Port: {self.ptp_slave_clk_id},\nProcessing message port data:'
            f'\n\tSlave MAC: {msg.src},\n\tDestination MAC: {msg.dst},'
            f'\n\tSlave Clk ID and Port: {msg.sourcePortIdentity}')
        self._logger.msg_timing(msg, self.time_offset)

    def __log_delay_response_issue(self, msg):
        self._logger.warning(
            f'{PtpType.get_ptp_type_str(msg)} msg inconsistent with previous port data!\nRegistered port data:'
            f'\n\tSource MAC: {self.ptp_eth_source_port},\n\tDestination MAC: {self.ptp_eth_source_destination},'
            f'\n\tSource Clk ID and Port: {self.ptp_source_clk_id},\n\tSlave Clk ID and Port: {self.ptp_slave_clk_id},'
            f'\nProcessing message port data:\n\tSource MAC: {msg.src},\n\tDestination MAC: {msg.dst},'
            f'\n\tSource Clk ID and Port: {msg.sourcePortIdentity},\n\tSlave Clk ID and Port: {msg.requestingPortIdentity}')
        self._logger.msg_timing(msg, self.time_offset)

    def __repr__(self):
        source_multicasting = 'Multicast' if self._is_mac_multicast(self.ptp_eth_source_destination) else ''
        slave_multicasting = 'Multicast' if self._is_mac_multicast(self.ptp_eth_slave_destination) else ''
        return f'Last PTP MAC address and Clock ID data:\n\tPTP Source MAC: {self.ptp_eth_source_port},'\
            f'\n\tPTP Slave MAC: {self.ptp_eth_slave_port},'\
            f'\n\tDestination for PTP Source MAC: {self.ptp_eth_source_destination} {source_multicasting},'\
            f'\n\tDestination for PTP Slave MAC: {self.ptp_eth_slave_destination} {slave_multicasting},'\
            f'\n\tSource Clock ID and Port: {self.ptp_source_clk_id},'\
            f'\n\tRequesting Clock ID and Port: {self.ptp_slave_clk_id}'
