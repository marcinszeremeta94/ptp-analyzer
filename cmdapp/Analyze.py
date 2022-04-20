from mptp.Analyser import Analyser


def analyse_ptp(analyser: Analyser, analyse_depth: tuple):
    if "--full" in analyse_depth:
        analyser.analyse()
    else:
        if "--announce" in analyse_depth:
            analyser.analyse_announce()
        if "--ports" in analyse_depth:
            analyser.analyse_ports()
        if "--sequenceId" in analyse_depth:
            analyser.analyse_sequence_id()
        if "--timing" in analyse_depth:
            analyser.analyse_timings()
        if "--match" in analyse_depth:
            analyser.analyse_if_stream_match_sequence_of_sync_dreq_dreq_pattern()
