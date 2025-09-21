# IPing
An IP pinger script working with a specific IP address range. Its kind of user-friendly and very advanced, working with an advanced pinger made from scratch for improved IP hunting.

# Setup Guide

This little script lets you ping a bunch of IPs at once and shows you if they’re alive (green), flaky (yellow), or dead (red). You can feed it either a range of IPs or a subnet, and it’ll handle the rest.



## Setup

1. Install Python (3.7 or newer).
Check if you have it:

`python --version`

2. Install the only extra thing it needs:


`pip install colorama`

3. Save the script as pinger.py.

That’s it, you’re ready.



## How to Run

Open a terminal in the folder where you saved the script, then run:
`python ping_scan.py <IP_RANGE> [options]`

## Examples

Ping a range of IPs:

`python ping_scan.py 192.168.1.1-192.168.1.20`

Ping a whole subnet:

`python ping_scan.py 192.168.1.0/28`

Use fewer workers and a shorter timeout:

`python ping_scan.py 192.168.0.0/24 -w 10 -t 500`

Save results to a text file:

`python ping_scan.py 10.0.0.1-10.0.0.50 -o results.txt`



## Options
-c → Number of pings per host (default: 4)

-t → Timeout in milliseconds (default: 1000)

-w → Number of workers/threads (default: 20)

-o → Save output to a file



## Output

Green = Host responded (0% loss)

Yellow = Some packet loss

Red = Host didn’t respond at all


```At the end, you’ll also get a quick summary with how many were up, flaky, or dead.```
