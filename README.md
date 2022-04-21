## PTP Analyzer  

**Tool providing complex reports with analysis of PTPv2 over Ethernet signal from pcap files**

_See example reports in examples_

Analysis provide:
1. Checking amount of particular PTP packet type
2. Announce data change within pcap file
3. MAC addresses and Clock ID consistency
4. Consistency in PTP message sequence ID increasing
5. Detection and check of message rate errors
6. Providing statistics of intervals and rates
7. Checking PTP messages not in sequence (one-step-mode)
8. Providing statistics of intervals between PTP message exchanges

The `PTPv2` layer is automatically bound to the Ethernet layer based on its `type` field (`0x88F7`).
Tested with tcpdump pcaps from ordinaryclock one-step mode.
Should handle two-step and transparentclocks tcpdumps as well.
Should work under Windows and Linux

PTP frames extraction is extension of layers and fields:
[scapy-gptp](https://github.com/weinshec/scapy-gptp)

## Requirements
Python 3.7+ and `scapy[basic]`

## Setup
```
git clone https://github.com/marcinszeremeta94/ptp-analyzer.git
pip install -r requirements.txt
```

## Usage
PtpAnalyzer.py script file can be run as python script or simply ./ from shell
```
python PtpAnalyzer.py [FILENAME] [options]
./PtpAnalyzer.py [FILENAME] [options]
```
_example_
```
python PtpAnalyzer.py eth2_ptp.pcap
./PtpAnalyzer.py eth2_ptp.pcap
./PtpAnalyzer.py eth2_ptp.pcap -v --no-prints
```
 report location is printed when analysis is done.

Argument [FILENAME] is mandatory. Pcap file is dispatched by scapy,
which does not accept tcpdumps taken from all interfaces (Linux cooked capture).
All other options are, well optional and not required. Default arguments are marked
as DEFAULT in argument list below. Order of options does not matter, however
if more than one option impact the same functionality last one is taken.
Analysis depth arguments adds up.
Analysis reports are stored in <Ptp Analyser Path>/reports/ as .log files 
named same as provided pcap file. If file exist will be overwritten!

        OPTIONS:
        -v or --verbose - More logging and printing, all warnings and wrong frames appear time
        -l or --no-logs - Turns creating report file
        -p or --no-prints - Turns off printing logs to console
        --full - Analysis Depth - all available analysis - DEFAULT
        --announce - Analysis Depth - announce PTP messages check
        --ports - Analysis Depth - MAC and Clock ID check
        --sequenceId - Analysis Depth - PTP message sequence ID check
        --timing - Analysis Depth - Message rate and interval check with statistics
        --match - Analysis Depth - One step mesage exchange check with statistics
        -h or --help - Print help
