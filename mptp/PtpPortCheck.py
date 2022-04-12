from mptp.Logger import Logger
from .PTPv2 import PTP_MSG_TYPE, PTPv2, PtpType


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
        self._logger.banner_large("PTP message MAC address and clock id analysis")
        if len(ptp_stream) < self.MINIMAL_MESSAGE_NUMBER_REQUIRED:
            self._logger.info("Not enough PTP messages to perform valid port check.")
            return
        self._check_ports_for_ptp_messages_in_stream(ptp_stream)
        self._log_status()

    def _check_ports_for_ptp_messages_in_stream(self, ptp_stream: list[PTPv2]):
        for msg in ptp_stream:
            msg_type = PtpType.get_ptp_msg_type(msg)
            if msg_type in (
                PTP_MSG_TYPE.ANNOUNCE_MSG,
                PTP_MSG_TYPE.SYNC_MSG,
                PTP_MSG_TYPE.FOLLOW_UP_MSG,
            ):
                self._check_sync_fup_announce_ports(msg)
            elif msg_type in (PTP_MSG_TYPE.DELAY_REQ_MSG, PTP_MSG_TYPE.PDELAY_REQ_MSG):
                self._check_dreq_ports(msg)
            elif msg_type in (
                PTP_MSG_TYPE.DELAY_RESP_MSG,
                PTP_MSG_TYPE.PDELAY_RESP_MSG,
                PTP_MSG_TYPE.PDELAY_RESP_FOLLOW_UP_MSG,
            ):
                self._check_dresp_ports(msg)

    def _check_sync_fup_announce_ports(self, msg: PTPv2):
        self._initial_source_values(msg)
        if (
            self.ptp_eth_source_port != msg.src
            or self.ptp_eth_source_destination != msg.dst
            or self.ptp_source_clk_id != msg.sourcePortIdentity
        ):
            self._inconsistency_counter += 1
            self._log_sync_announce_followup_issue(msg)
            self._reset_source_data()

    def _check_dreq_ports(self, msg: PTPv2):
        self._initial_slave_values(msg)
        if (
            self.ptp_eth_slave_port != msg.src
            or self.ptp_eth_slave_destination != msg.dst
            or self.ptp_slave_clk_id != msg.sourcePortIdentity
        ):
            self._inconsistency_counter += 1
            self._log_delay_request_issue(msg)
            self._reset_slave_data()

    def _check_dresp_ports(self, msg: PTPv2):
        if self.ptp_eth_slave_port is None:
            return
        if (
            self.ptp_eth_source_port != msg.src
            or self.ptp_eth_source_destination != msg.dst
            or self.ptp_source_clk_id != msg.sourcePortIdentity
            or self.ptp_slave_clk_id != msg.requestingPortIdentity
        ):
            self._inconsistency_counter += 1
            self._log_delay_response_issue(msg)

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

    @staticmethod
    def is_mac_multicast(mac: str) -> bool:
        if mac is None:
            return False
        return mac[1:2] == "1"

    @staticmethod
    def add_multicast_mark_to_mac_address(mac: str) -> str:
        return f"{mac} - Multicast" if PtpPortCheck.is_mac_multicast(mac) else {mac}

    def _log_sync_announce_followup_issue(self, msg: PTPv2):
        self._logger.warning(
            f"{PtpType.get_ptp_type_str(msg)} msg inconsistent with previous port data!\n"
            f"Registered port data:\n\tSource MAC: {self.ptp_eth_source_port},\n\tDestination MAC:"
            f"{PtpPortCheck.add_multicast_mark_to_mac_address(self.ptp_eth_source_destination)},"
            f"\n\tSource Clk ID and Port: {self.ptp_source_clk_id},\nProcessing message port data:"
            f"\n\tSource MAC: {msg.src},\n\tDestination MAC: {msg.dst},"
            f"\n\tSource Clk ID and Port: {msg.sourcePortIdentity}"
        )
        self._logger.msg_timing(msg, self.time_offset)

    def _log_delay_request_issue(self, msg: PTPv2):
        self._logger.warning(
            f"Delay Request msg inconsistent with previous port data!\nRegistered port data:"
            f"\n\tSlave MAC: {self.ptp_eth_slave_port},\n\tDestination MAC: "
            f"{PtpPortCheck.add_multicast_mark_to_mac_address(self.ptp_eth_slave_destination)},"
            f"\n\tSlave Clk ID and Port: {self.ptp_slave_clk_id},\nProcessing message port data:"
            f"\n\tSlave MAC: {msg.src},\n\tDestination MAC: {msg.dst},"
            f"\n\tSlave Clk ID and Port: {msg.sourcePortIdentity}"
        )
        self._logger.msg_timing(msg, self.time_offset)

    def _log_delay_response_issue(self, msg):
        self._logger.warning(
            f"{PtpType.get_ptp_type_str(msg)} msg inconsistent with previous port data!\n"
            f"Registered port data:\n\tSource MAC: {self.ptp_eth_source_port},\n\tDestination MAC:"
            f"{PtpPortCheck.add_multicast_mark_to_mac_address(self.ptp_eth_source_destination)},"
            f"\n\tSource Clk ID and Port: {self.ptp_source_clk_id},\n\tSlave Clk ID and Port: "
            f"{self.ptp_slave_clk_id},\nProcessing message port data:\n\tSource MAC: {msg.src},"
            f"\n\tDestination MAC: {msg.dst},\n\tSource Clk ID and Port: {msg.sourcePortIdentity},"
            f"\n\tSlave Clk ID and Port: {msg.requestingPortIdentity}"
        )
        self._logger.msg_timing(msg, self.time_offset)

    def _log_status(self):
        if self._inconsistency_counter:
            self._logger.info(
                f"PTP Clock ID and MAC number of issues found: {self._inconsistency_counter}"
            )
        else:
            self._logger.info(f"PTP Clock ID and MAC addresses: [OK]")
        self._logger.banner_small("Port and clock id addresses")
        self._logger.info(self.__repr__())

    def __repr__(self) -> str:
        return (
            f"Last PTP MAC address and Clock ID data:\n\tPTP Source MAC: {self.ptp_eth_source_port},"
            f"\n\tPTP Slave MAC: {self.ptp_eth_slave_port},"
            f"\n\tDestination for PTP Source MAC: "
            f"{PtpPortCheck.add_multicast_mark_to_mac_address(self.ptp_eth_source_destination)},"
            f"\n\tDestination for PTP Slave MAC: "
            f"{PtpPortCheck.add_multicast_mark_to_mac_address(self.ptp_eth_slave_destination)},"
            f"\n\tSource Clock ID and Port: {self.ptp_source_clk_id},"
            f"\n\tRequesting Clock ID and Port: {self.ptp_slave_clk_id}"
        )
