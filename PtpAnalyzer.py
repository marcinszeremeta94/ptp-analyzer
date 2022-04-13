#!/usr/bin/env python3
import time
import cmdapp.utils as app
from mptp.Logger import Logger
from mptp import PcapTpPtp


def main():
    start_time = time.time()
    (
        file_path,
        log_severity,
        print_option,
        analyse_depth,
    ) = app.dispatch_args()

    logger = Logger(app.get_file_name_from_path(file_path), log_severity, print_option)
    ptp = PcapTpPtp.PcapToPtpStream(logger, file_path)
    app.analyse_ptp(ptp, analyse_depth)
    app.print_footer(logger, start_time)


if __name__ == "__main__":
    main()
