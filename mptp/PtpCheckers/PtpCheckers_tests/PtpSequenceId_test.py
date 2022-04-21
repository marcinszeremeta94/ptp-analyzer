from mptp.PtpPacket.PTPv2 import PTPv2, PTP_MSG_TYPE
from mptp.PtpCheckers.PtpSequenceId import PtpSequenceId
from tests.testutils.DummyLogger import DummyLogger
from typing import List
import unittest

class PtpSequenceId_test(unittest.TestCase):
    
    dummy_time_offset: float = 4.0
    dummy_logger = DummyLogger()
    
    def setUp(self):
        self.sut = PtpSequenceId(self.dummy_logger, self.dummy_time_offset)
        
    def test_object_creation(self):
        self.assertNotEqual(None, self.sut)
    
    def test_is_cached_time_offset_correct(self):
        self.assertEqual(self.dummy_time_offset, self.sut.time_offset)
    
    def test_check_sync_followup_sequence(self):
        self.assertEqual(self.dummy_time_offset, self.sut.time_offset)
        sync, fup = PtpSequenceId_test.create_ptp_sync_fup_test_data()
        self.sut.check_sync_followup_sequence(sync, fup)    
    
    @staticmethod  
    def create_ptp_sync_fup_test_data(n: int = 10):
        sync: List[PTPv2] = []
        fup: List[PTPv2] = []
        for i in range(0, n):
            sync.append(PTPv2())
            sync[-1].messageType = PTP_MSG_TYPE.SYNC_MSG.value
            sync[-1].sequenceId = i
            fup.append(PTPv2())
            fup[-1].messageType = PTP_MSG_TYPE.FOLLOW_UP_MSG.value
            fup[-1].sequenceId = i  
        return (sync, fup)
        
    
if __name__ == '__main__':
    unittest.main()

