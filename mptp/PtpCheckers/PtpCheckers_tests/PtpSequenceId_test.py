from tests.testutils.DummyLogger import DummyLogger
from mptp.PtpCheckers.PtpSequenceId import PtpSequenceId
import unittest

class PtpSequenceId_test(unittest.TestCase):
    
    dummy_time_offset: float = 4.0
    dummy_logger = DummyLogger()
    
    def setUp(self):
        self.sut = PtpSequenceId(self.dummy_logger, self.dummy_time_offset)
    
    def test1(self):
        print(self.sut)
        self.assertEqual(4, 4)
        self.assertEqual(self.dummy_time_offset, self.sut.time_offset)
    
if __name__ == '__main__':
    unittest.main()

# python -m mptp.PtpCheckers.PtpCheckers_tests.PtpSequenceId_test
