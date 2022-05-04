## PTP Analyzer  

**Tool providing complex reports with analysis of PTPv2 over Ethernet signal from pcap files**

_See examples below or in examples directory_

Analysis provide:
1. Checking amount of particular PTP packet type
2. Announce data change within pcap file
3. MAC addresses and Clock ID consistency
4. Consistency in PTP message sequence ID increasing
5. Detection and check of message rate errors
6. Providing statistics of intervals and rates
7. Checking PTP messages not in sequence (one-step-mode)
8. Providing statistics of intervals between PTP message exchanges
9. Timestamp to capture time consistency histogram 

The `PTPv2` layer is automatically bound to the Ethernet layer based on its `type` field (`0x88F7`).
Tested with tcpdump pcaps from ordinaryclock one-step mode.
Should handle two-step and transparentclocks tcpdumps as well.
Should work under Windows and Linux

## Motivation
I needed a script to quickly analyse pcaps from several ports (ordinary clock) from tcpdump running for 1-2 minutes for some time.
This need turned out into this script/app, and grew along with my analysis so architecture might be not as noble as might be. 
However, after all works perfect for finding issues between master clock and boundry clock in terms off timing or queue stuck.

## Requirements
Python 3.7+ `scapy[basic]`, and `matplotlib`

## Setup
```
git clone https://github.com/marcinszeremeta94/ptp-analyzer.git
cd ptp-analyzer
pip install -r requirements.txt
chmod u+x PtpAnalyzer.py
```

## Quick Start
```
python PtpAnalyzer.py ../my_pcaps/eth2_ptp.pcap
./PtpAnalyzer.py eth2_ptp.pcap --verbose --no-prints
./PtpAnalyzer.py eth2_ptp.pcap -v --no-prints --no-plots
```

## Usage
Application accepts pcap files eg. got as result as work of `tcpdump -i eth0 -w ptp.pcap ether proto 0x88F7`

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
named same as provided pcap file same as plots with .png extention. 
**If file exist will be overwritten!**

        OPTIONS:
        -v or --verbose - More logging and printing, all warnings and wrong frames appear time
        -l or --no-logs - Turns off creating report file
        -p or --no-prints - Turns off printing logs to console
        -t or --no-plots - Turns off timings histogram png file creation
        --full - Analysis Depth - all available analysis - DEFAULT
        --announce - Analysis Depth - announce PTP messages check
        --ports - Analysis Depth - MAC and Clock ID check
        --sequenceId - Analysis Depth - PTP message sequence ID check
        --timing - Analysis Depth - Message rate and interval check with statistics
        --match - Analysis Depth - One step mesage exchange check with statistics
        -h or --help - Print help
 
## Plot and Report Preview
 
 **Plots**
![image](https://user-images.githubusercontent.com/69167289/166838130-5283f556-3f8c-4fc8-9aa6-31725d858f1d.png)
Seems ok
 
![image](https://user-images.githubusercontent.com/69167289/166838230-4450e1bd-7250-4fee-9ee5-b738b0fdfbd1.png)
Here are some issues in ordinary clock queue
 
![image](https://user-images.githubusercontent.com/69167289/166838320-123582b3-e812-49b6-bf5c-fccc6006605e.png)
two-step, no announce - acceptable
 
 **Reports**
![image](https://user-images.githubusercontent.com/69167289/166838495-7188c6c5-78c5-4898-820c-7ea5f1a43e96.png)
Initial Check
 
![image](https://user-images.githubusercontent.com/69167289/166838577-beaf4e92-16fd-4624-8615-2228ed933ca1.png)
Announce
 
![image](https://user-images.githubusercontent.com/69167289/166838628-ccbba11c-8efa-424e-a4ca-c5fc99eb2418.png)
Sequence OK
 
![image](https://user-images.githubusercontent.com/69167289/166838712-afe32f3f-1515-4ff7-b489-608d14259e8b.png)
Timings and rates OK - two-step so timestamps in followups, no announce
 
![image](https://user-images.githubusercontent.com/69167289/166838861-7cdc1e5b-b07c-4532-8185-f0c63da539ce.png)
PTP msg exhange OK - verbose
 
![image](https://user-images.githubusercontent.com/69167289/166838947-f9e79e46-9871-41df-b97b-d842926ffe68.png)
PTP exchange, at the begining of pcap no Delay_Req - Resp - verbose - OK
 
![image](https://user-images.githubusercontent.com/69167289/166839119-21a3a9f0-f550-4d22-b223-426adb0306fc.png)
Some slight issues with message rates
 
![image](https://user-images.githubusercontent.com/69167289/166839332-edd6e36f-79e7-4a58-a871-93a16e924dad.png)
Issues with sequence number

![image](https://user-images.githubusercontent.com/69167289/166839249-6288d99f-6436-4edf-8210-6d32516d405c.png)
Some wierd things in pcap detected as well
 
![image](https://user-images.githubusercontent.com/69167289/166839354-7b918e86-f2e9-422a-905c-1fdbcdbacfe7.png)
No PTP in pcap
 
## Issues
Sometimes matplotlib has some issues seting logarithmic scale with big inconsistencies
 
## External code use
PTP frames extraction in mptp/PtpPackets is extension of layers and fields files of:
[scapy-gptp](https://github.com/weinshec/scapy-gptp) repository
by Christoph Weinsheimer 

 ## Anyway
 I hope it may be useful for someone :)
