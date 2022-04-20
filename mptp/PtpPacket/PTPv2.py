from enum import Enum
from scapy.fields import (
    BitEnumField,
    BitField,
    ByteField,
    ConditionalField,
    FlagsField,
    LongField,
    ShortField,
    SignedByteField,
    XBitField,
    XByteField,
    XIntField,
    XStrFixedLenField,
)
from scapy.layers.l2 import Ether
from scapy.packet import Packet, bind_layers

from .Fields import TimestampField, PortIdentityField


class PTP_MSG_TYPE(Enum):
    SYNC_MSG = 0x0
    DELAY_REQ_MSG = 0x1
    DELAY_RESP_MSG = 0x9
    PDELAY_REQ_MSG = 0x2
    PDELAY_RESP_MSG = 0x3
    PDELAY_RESP_FOLLOW_UP_MSG = 0xA
    FOLLOW_UP_MSG = 0x8
    ANNOUNCE_MSG = 0xB
    SIGNALLING_MSG = 0xC


class PTPv2(Packet):
    name = "PTPv2"

    MSG_TYPES = {
        0x0: "Sync",
        0x1: "DelayReqest",
        0x9: "DelayResponse",
        0x8: "FollowUp",
        0xA: "DelayResponseFollowUp",
        0xB: "Announce",
    }

    CLK_ACCURACY = {
        0x20: "25ns",
        0x21: "100ns",
        0x23: "1us",
        0x24: "2.5us",
        0x25: "10us",
        0x26: "25us",
        0x27: "100us",
        0x28: "250us",
        0x29: "1ms",
        0x2A: "2.5ms",
        0x2B: "10ms",
        0x2C: "25ms",
        0x2D: "100ms",
        0x2E: "250ms",
        0x2F: "1s",
        0x30: "10s",
        0x31: ">10s",
        0xFE: "unknown",
    }

    TIME_SOURCE = {
        0x00: "Unknown",
        0x10: "AtomicClock",
        0x20: "GPS",
        0x22: "TerrestrialRadio",
        0x50: "NTP",
        0x60: "HandSet",
        0x90: "Other",
        0xA0: "InternalOscillator",
    }

    FLAGS = [
        "LI61",
        "LI59",
        "UTC_REASONABLE",
        "TIMESCALE",
        "TIME_TRACEABLE",
        "FREQUENCY_TRACEABLE",
        "?",
        "?",
        "ALTERNATE_MASTER",
        "TWO_STEP",
        "UNICAST",
        "?",
        "?",
        "profileSpecific1",
        "profileSpecific2",
        "SECURITY",
    ]

    fields_desc = [
        # Common fields
        BitField("transportSpecific", 1, 4),
        BitEnumField("messageType", 0, 4, MSG_TYPES),
        XBitField("reserved0", 0, 4),
        BitField("versionPTP", 0x2, 4),
        ShortField("messageLength", 34),
        ByteField("domainNumber", 0),
        XByteField("reserved1", 0),
        FlagsField("flags", 0, 16, FLAGS),
        LongField("correctionField", 0),
        XIntField("reserved2", 0),
        PortIdentityField("sourcePortIdentity", 0),
        ShortField("sequenceId", 0),
        XByteField("control", 0),
        SignedByteField("logMessageInterval", -3),
        
        # Announce
        ConditionalField(
            TimestampField("originTimestamp", 0),
            lambda pkt: PtpType.is_announce(pkt)
            or PtpType.is_sync(pkt)
            or PtpType.is_delay_req(pkt),
        ),
        ConditionalField(
            ShortField("utcOffset", 0), lambda pkt: PtpType.is_announce(pkt)
        ),
        ConditionalField(
            ShortField("priority1", 0), lambda pkt: PtpType.is_announce(pkt)
        ),
        ConditionalField(
            ByteField("grandmasterClockClass", 0), lambda pkt: PtpType.is_announce(pkt)
        ),
        ConditionalField(
            BitEnumField("grandmasterClockAccuracy", 0x21, 8, CLK_ACCURACY),
            lambda pkt: PtpType.is_announce(pkt),
        ),
        ConditionalField(
            ShortField("grandmasterClockVariance", 0),
            lambda pkt: PtpType.is_announce(pkt),
        ),
        ConditionalField(
            ByteField("priority2", 0), lambda pkt: PtpType.is_announce(pkt)
        ),
        ConditionalField(
            XStrFixedLenField("grandmasterClockId", 0, 8),
            lambda pkt: PtpType.is_announce(pkt),
        ),
        ConditionalField(
            ShortField("localStepsRemoved", 0), lambda pkt: PtpType.is_announce(pkt)
        ),
        ConditionalField(
            BitEnumField("timeSource", 0x90, 8, TIME_SOURCE),
            lambda pkt: PtpType.is_announce(pkt),
        ),
        ConditionalField(
            ShortField("padding", 0),
            lambda pkt: PtpType.is_sync(pkt) or PtpType.is_delay_req(pkt),
        ),
        # FollowUp
        ConditionalField(
            TimestampField("preciseOriginTimestamp", 0),
            lambda pkt: PtpType.is_followup(pkt),
        ),
        ConditionalField(
            XStrFixedLenField("informationTlv", 0, 32),
            lambda pkt: PtpType.is_followup(pkt),
        ),
        # DelayResp
        ConditionalField(
            TimestampField("receiveTimestamp", 0),
            lambda pkt: PtpType.is_delay_resp(pkt),
        ),
        # PDelayResp
        ConditionalField(
            TimestampField("requestReceiptTimestamp", 0),
            lambda pkt: PtpType.is_pdelay_resp(pkt),
        ),
        # DelayRespFollowUp
        ConditionalField(
            TimestampField("responseOriginTimestamp", 0),
            lambda pkt: PtpType.is_delay_resp_followup(pkt),
        ),
        ConditionalField(
            PortIdentityField("requestingPortIdentity", 0),
            lambda pkt: PtpType.is_delay_resp(pkt)
            or PtpType.is_delay_resp_followup(pkt)
            or PtpType.is_pdelay_resp(pkt),
        ),
    ]


bind_layers(Ether, PTPv2, type=0x88F7)


class PtpType:
    @staticmethod
    def get_ptp_msg_type(ptp_v2: PTPv2) -> PTP_MSG_TYPE:
        if ptp_v2.messageType == PTP_MSG_TYPE.SYNC_MSG.value:
            return PTP_MSG_TYPE.SYNC_MSG
        elif ptp_v2.messageType == PTP_MSG_TYPE.FOLLOW_UP_MSG.value:
            return PTP_MSG_TYPE.FOLLOW_UP_MSG
        elif ptp_v2.messageType == PTP_MSG_TYPE.DELAY_REQ_MSG.value:
            return PTP_MSG_TYPE.DELAY_REQ_MSG
        elif ptp_v2.messageType == PTP_MSG_TYPE.DELAY_RESP_MSG.value:
            return PTP_MSG_TYPE.DELAY_RESP_MSG
        elif ptp_v2.messageType == PTP_MSG_TYPE.PDELAY_REQ_MSG.value:
            return PTP_MSG_TYPE.PDELAY_REQ_MSG
        elif ptp_v2.messageType == PTP_MSG_TYPE.PDELAY_RESP_MSG.value:
            return PTP_MSG_TYPE.PDELAY_RESP_MSG
        elif ptp_v2.messageType == PTP_MSG_TYPE.PDELAY_RESP_FOLLOW_UP_MSG.value:
            return PTP_MSG_TYPE.PDELAY_RESP_FOLLOW_UP_MSG
        elif ptp_v2.messageType == PTP_MSG_TYPE.ANNOUNCE_MSG.value:
            return PTP_MSG_TYPE.ANNOUNCE_MSG
        elif ptp_v2.messageType == PTP_MSG_TYPE.SIGNALLING_MSG.value:
            return PTP_MSG_TYPE.SIGNALLING_MSG
        else:
            return None

    @staticmethod
    def get_ptp_type_str(ptp_v2: PTPv2) -> str:
        if ptp_v2.messageType == PTP_MSG_TYPE.SYNC_MSG.value:
            return "Sync"
        elif ptp_v2.messageType == PTP_MSG_TYPE.FOLLOW_UP_MSG.value:
            return "Follow-up"
        elif ptp_v2.messageType == PTP_MSG_TYPE.DELAY_REQ_MSG.value:
            return "Delay req"
        elif ptp_v2.messageType == PTP_MSG_TYPE.DELAY_RESP_MSG.value:
            return "Delay res"
        elif ptp_v2.messageType == PTP_MSG_TYPE.PDELAY_REQ_MSG.value:
            return "PDelay req"
        elif ptp_v2.messageType == PTP_MSG_TYPE.PDELAY_RESP_MSG.value:
            return "PDelay res"
        elif ptp_v2.messageType == PTP_MSG_TYPE.PDELAY_RESP_FOLLOW_UP_MSG.value:
            return "Delay res follow-up"
        elif ptp_v2.messageType == PTP_MSG_TYPE.ANNOUNCE_MSG.value:
            return "Announce"
        elif ptp_v2.messageType == PTP_MSG_TYPE.SIGNALLING_MSG.value:
            return "Signaling"
        else:
            return "Unknown"

    @staticmethod
    def is_sync(ptpv2: PTPv2) -> bool:
        return ptpv2.messageType == PTP_MSG_TYPE.SYNC_MSG.value

    @staticmethod
    def is_followup(ptpv2: PTPv2) -> bool:
        return ptpv2.messageType == PTP_MSG_TYPE.FOLLOW_UP_MSG.value

    @staticmethod
    def is_delay_req(ptpv2: PTPv2) -> bool:
        return ptpv2.messageType == PTP_MSG_TYPE.DELAY_REQ_MSG.value

    @staticmethod
    def is_delay_resp(ptpv2: PTPv2) -> bool:
        return ptpv2.messageType == PTP_MSG_TYPE.DELAY_RESP_MSG.value

    @staticmethod
    def is_pdelay_req(ptpv2: PTPv2) -> bool:
        return ptpv2.messageType == PTP_MSG_TYPE.PDELAY_REQ_MSG.value

    @staticmethod
    def is_pdelay_resp(ptpv2: PTPv2) -> bool:
        return ptpv2.messageType == PTP_MSG_TYPE.PDELAY_RESP_MSG.value

    @staticmethod
    def is_delay_resp_followup(ptpv2: PTPv2) -> bool:
        return ptpv2.messageType == PTP_MSG_TYPE.PDELAY_RESP_FOLLOW_UP_MSG.value

    @staticmethod
    def is_announce(ptpv2: PTPv2) -> bool:
        return ptpv2.messageType == PTP_MSG_TYPE.ANNOUNCE_MSG.value

    @staticmethod
    def is_signalling(ptpv2: PTPv2) -> bool:
        return ptpv2.messageType == PTP_MSG_TYPE.SIGNALLING_MSG.value
