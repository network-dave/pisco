# pisco.py

Run commands on Cisco devices via Telnet.

Pisco is a little project I've put together to help me automate a couple tasks involving legacy Cisco devices. 
Instead of relying on external libraries, I wanted to develop something quickly with full control on the process.
It was made with specific considerations in mind. It had to be:

- Lightweight - only a couple hundred lines long including documentation.
- Self-contained - relies on Python's Standard Library only.
- Portable - works on Windows, Linux and Mac.
- Backward compatible - works with older versions of Python3 (tested with Python 3.4.3 on Windows Server 2003).
  


## Prerequisites

Python >= 3.4

Pisco.py has no dependencies other than modules from the Standard Library.
  


## Installation

Simply copy pisco.py to any directory and run it from your favorite terminal.

You can also "import pisco" from another Python script and reuse the TelnetDevice class.
  


## Supported platforms

Any Cisco IOS devices. Might eventually work with other stuff like Cisco WLC's... Maybe even other brands.

Let me know if it does!
  

## Usage

Run 'pisco.py --help' for help.

Notes:
- Specify multiple IP addresses or usernames/passwords by separating them by a comma
- When using multiple usernames and passwords, both lists must have the same length
- 'DEVICE_LIST.txt' skips lines starting with '!' or '#'
- 'COMMANDS.txt' shall include one command per line
- '--save' will save the output to a 'pisco_output_xxx.txt" file in the current directory
- You can use {ip_address}, {hostname}, {date_time} and/or {username} in the path for '--output-directory'


## Examples

Get the running config from a device:
```
py pisco.py -c show run -d 172.16.100.1
```
Run a command including a pipe filter without going into enable mode from 2 devices using username 'networkdave':
```
py pisco.py -c "show int status | i down" -d 172.16.100.1,172.16.100.2 -u networkdave -n
```
Run the commands in 'commands.txt' on a device by trying 2 different usernames and passwords and save the output to file:
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
 
 
## GUI

A graphical front-end is available for pisco.py via the gpisco.py script. It uses the Gooey library (https://github.com/chriskiehl/Gooey) to generate a GUI from the command-line script. Gooey let's you turn any python script in a graphical program with only a few lines of code (1 is enough).

Just run:

```
pip install gooey
gpisco.py
```

and BINGO, no more CLI.

You can also package a stand-alone executable file thanks to pyInstaller (https://www.pyinstaller.org/), using the gpisco.spec file.


## Disclaimer

Pisco.py is my first Python project and was made for educational and practical purposes. Use at your own risk!

If you have any remarks regarding the code I will be happy to hear from you, please drop me a line at my email address.


## Caveats

Pisco relies on looking for characters ">" or "#" to find the prompt of the device. If those characters appear elsewhere in the output (for example in an interface's description) it will break the system. I'm looking for a way to fix this ASAP.

