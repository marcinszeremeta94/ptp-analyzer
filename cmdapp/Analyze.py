from mptp.PtpStream import PtpStream


def analyse_ptp(ptp: PtpStream, analyse_depth: tuple):
    if "--full" in analyse_depth:
        ptp.analyse()
    else:
        if "--announce" in analyse_depth:
            ptp.analyse_announce()
        if "--ports" in analyse_depth:
            ptp.analyse_ports()
        if "--sequenceId" in analyse_depth:
            ptp.analyse_sequence_id()
        if "--timing" in analyse_depth:
            ptp.analyse_timings()
        if "--match" in analyse_depth:
            ptp.analyse_if_stream_match_sequence_of_sync_dreq_dreq_pattern()
