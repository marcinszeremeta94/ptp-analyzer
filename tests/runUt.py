import unittest
from mptp.PtpPacket.PtpPacket_tests.test_fields import TimestampFieldTest, PortIdentityFieldTest
from mptp.PtpPacket.PtpPacket_tests.test_PTPv2 import PTPv2LayerTest
from mptp.PtpCheckers.PtpCheckers_tests.PtpSequenceId_test import PtpSequenceId_test 

#python -m tests.runUt
if __name__ == '__main__':
    unittest.main()