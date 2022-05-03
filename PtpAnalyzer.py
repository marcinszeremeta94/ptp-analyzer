#!/usr/bin/env python3
import time
import cmdapp.ArgsDispatcher as dispatcher
import cmdapp.utils as apputils 
import cmdapp.Analyze as app
from appcommon.AppLogger.Logger import Logger
from appcommon.ConfigReader.ConfigReader import ConfigReader
from mptp import mPTP


def main():
    start_time = time.time()
    (
        file_path,
        log_severity,
        print_option,
        analyse_depth,
        plotter_off,
    ) = dispatcher.dispatch_args()

    config = ConfigReader()
    config.plotter_off = plotter_off
    logger = Logger(apputils.get_file_name_from_path(file_path), log_severity, print_option)
    ptp = mPTP.PcapToPtpStream(file_path)
    analyzer = mPTP.CreatePtpAnalyser(config, logger, ptp)
    app.analyse_ptp(analyzer, analyse_depth)
    apputils.print_footer(logger, start_time)

if __name__ == "__main__":
    main()
