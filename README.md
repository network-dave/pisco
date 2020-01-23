# pisco.py

CLI tool to run commands on Cisco devices via Telnet.

Pisco is a little project I've put together to help me automate a couple tasks involving legacy Cisco devices. 
Instead of relying on external libraries, I wanted to develop something quickly with full control on the process.
It was made with specific considerations in mind. It had to be:

- Lightweight - only a couple hundred lines long including documentation.
- Self-contained - relies on Python's Standard Library only.
- Portable - works on Windows, Linux and Mac.
- Backward compatible - works with older versions of Python3 (tested with Python 3.4.3 on Windows Server 2003).
  


## Prerequisites

Python >= 3.4

Pisco.py has no dependencies other that modules from the Standard Library.
  


## Installation

Simply copy pisco.py to any directory and run it from your favorite terminal.

You can also "import pisco" from another Python script and reuse the TelnetDevice class.
  


## Supported platforms

Any Cisco IOS devices. Might eventually work with other stuff like Cisco WLC's... Maybe even other brands.

Let me know if it does!
  

## Usage

** Coming soon... **



## Examples

Get the running config from a device:
```
py pisco.py -c show run -d 172.16.100.1
```
Run a command including a pipe filter without going into enable mode from 2 devices using username 'networkdave':
```
py pisco.py -c "show int status | i down" -d 172.16.100.1,172.16.100.2 -u networkdave -n
```
Run the commands from 'commands.txt' on the device by trying 2 different usernames and passwords and then save it to file:
```
py pisco.py -C commands.txt -d 172.16.100.1 -u networkdave,networkbill -p davespass,billspass -s
```
Configure the description for interface Gi1/0/1 on all devices listed in 'my_switches.txt' using the admin:CiscoCisco credentials:
```
py pisco.py -c "conf t,int g1/0/1,desc Interface 1" -D my_switches.txt -u admin -p CiscoCisco -e Enable123
```
Save and then pull the running config from all devices listed in 'my_switches.txt' using the admin:CiscoCisco credentials, and save the output for each device in the './configs' folder in a different subfolder named after it's IP address (a poor man's config backup script):
```
py pisco.py -c "write,show run" -D my_switches.txt -u admin -p CiscoCisco -sSO ./configs/{ip_address}
```
  


## Disclaimer

Pisco.py is my first Python project and was made for educational and practical reasons. 

If you have any remarks regarding the code I will be happy to hear from you, please drop me a line at my email address.


## Caveats

Pisco relies on looking for characters ">" or "#" to find the prompt of the device. If those characters appear elsewhere in the output (for example in an interface's description) it will break the system. I'm looking for a way to fix this ASAP.

