#!/usr/bin/env python3

'''

Pisco.py - Run commands on Cisco devices via Telnet

Usage: use --help for help

-   Passwords will be prompted at runtime if needed.
-   We can provide multiple commands and/or IP addresses in the arguments, separated by commas.
-   Import pisco.py to use the TelnetDevice class and it's methods

'''

import os
import sys
import argparse
import re
import time
import telnetlib
import getpass
from datetime import datetime

# Used to split username/password lists
DELIMITER = ","

class TelnetDevice(telnetlib.Telnet):
    '''
    Define a TelnetDevice class that inherits from telnetlib.Telnet

    We add a few methods that simplify interacting with a Cisco IOS device:
    -   send_command
    -   read_output 
    -   enable
    -   get_facts
    -   get_int_list
    -   get_int_status (with or without full description and PoE status)

    Those methods handle encoding/decoding of strings/bytes.
    '''

    def __init__(self, host, username=None, password=None, enable_password=None, quiet=False, debug=False):
        '''
        Instantiating the TelnetDevice class will automatically connect and log into the device
        '''
        self.host = host
        self.hostname = ""
        self.username = username
        self.password = password
        self.enable_password = enable_password
        self.enable_mode = False
        self.infos = {}
        self.int_status = {}
        self.when = datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")
        self.debug = debug

        if not quiet:
            print("[+] Connecting to {}... ".format(host))

        telnetlib.Telnet.__init__(self, host, timeout=4)
        response = self.read_output(password_prompt=True).splitlines()[-1]

        if self.debug:
            self.set_debuglevel(5)

        retries = 0
        login_successful = False            

        while not login_successful:
            if "User" in response:
                if not self.username:
                    self.username = input("Username: ")
                self.send_command(self.username.split(DELIMITER)[retries])
                response = self.read_output(password_prompt=True)
            
            if "Pass" in response:
                if not self.password:
                    self.password = getpass.getpass()
                if len(self.username.split(DELIMITER)) != len(self.password.split(DELIMITER)):
                    print("[!] Username and password lists must be the same length (use comma as delimiter)")
                    raise ConnectionError
                self.send_command(self.password.split(DELIMITER)[retries])
                response = self.read_output(password_prompt=True)

            if response.endswith(">"):
                login_successful = True
                self.hostname = response.splitlines()[-1].rstrip(">")
            elif response.endswith("#"):
                login_successful = True
                self.enable_mode = True
                self.hostname = response.splitlines()[-1].rstrip("#")
            else:
                if (len(self.username.split(DELIMITER)) - retries) > 1:
                    print("[!] Wrong login/password, trying next one in list")
                    retries += 1
                else:
                    print("[!] Wrong login/password")
                    raise ConnectionError

        if not quiet:
            print("[+] Login successful")


    def send_command(self, command):
        '''
        Send command to device.

        Note: We use Latin_1 encoding because ascii can yield invalid characters with some devices like Cisco WISM.
        '''

        self.write(command.encode("Latin_1") + b"\n")


    def read_output(self,password_prompt=False):
        '''
        Read output until one of the possible prompts.
        
        Use password_prompt when a ":" prompt is possible.
        '''
        
        if password_prompt:
            expected = [b"\>", b"\#", b"sername\:", b"assword\:"]
        else:
            expected = [b"\>", b"\#"]

        response = self.expect(expected, timeout=7)
        response = response[2].decode("Latin_1")
        
        return response      


    def enable(self):
        '''
        Enter enable mode. Multiple passwords can be provided.
        '''

        if self.enable_mode:
            return
        
        retries = 0
        self.send_command("enable")
        
        while self.enable_mode == False:
            response = self.read_output(password_prompt=True)
            # We ask for password only twice in interactive mode, but we'll try all the passwords in the list
            # This is to avoid getting stuck at the enable password prompt
            # If the password is incorrect we'd rather fail and move to the next device
            if "Password:" in response:
                if not self.enable_password:
                    self.enable_password = getpass.getpass(prompt="Enable password: ")
                    retries = 0
                if (len(self.enable_password.split(DELIMITER)) - retries >= 1):
                    self.send_command(self.enable_password.split(DELIMITER)[retries])     
                else:
                    self.send_command("")
                    self.enable_password = None
                retries += 1
            elif "#" in response:
                    self.enable_mode = True
            else:
                if (len(self.enable_password.split(DELIMITER)) - retries >= 1):
                    self.send_command("enable")
                else:
                    print("[!] Wrong password, can't go into enable mode")
                    break
        

    def get_facts(self):
        '''
        Get hostname, IOS info and uptime and put them in a dictionnary
        '''

        self.send_command("show version | include Model .umber|uptime")
        response = self.read_output().splitlines()
        response_split = [ line.split() for line in response ]
        response_split.pop(0)
        hostname = response_split[0][0]
        uptime = " ".join(response_split[0][3:])
        model = response_split[1][-1]

        self.facts = { 
                        "ip_address":self.host, \
                        "hostname":hostname, \
                        "model":model, \
                        "uptime":uptime, \
                        "when":self.when }

        return self.facts


    def get_int_list(self):
        '''
        Get a simple list of all physical interfaces
        '''
        self.send_command("show int status")
        list_interfaces = [line.split()[0] for line in self.read_output().splitlines()[3:-1] if not line.startswith("----") and line.strip()]
        
        return list_interfaces


    def get_int_status(self, get_full_description=False, get_power=False):
        '''
        Get interfaces' status and description and store result in a dictionnary "self.int_status"
        '''
        self.send_command("show int status")
        list_int_status = [line for line in self.read_output().splitlines()[3:-1] if not line.startswith("----") and line.strip()]

        for line in list_int_status:
            interface = line[0:8].strip()
            description = line[10:29].strip()
            status = line[29:39].strip()
            vlan = line[42:47].strip()
            speed = line[60:66].strip().replace("a-", "").replace("auto", "-")
            
            self.int_status[interface] = { "description": description, \
                                      "status": status, \
                                      "vlan": vlan, \
                                      "speed": speed, \
                                      "power": "-"}

        if get_full_description:
            self.send_command("show int desc")
            list_int_description = [line for line in self.read_output().splitlines()[3:-1] if line.strip()]
            for line in list_int_description:
                interface = line[0:8].strip()
                if interface in self.int_status:
                    description = line[55:].strip()
                    self.int_status[interface]["description"] = description

        if get_power:
            self.send_command("show power inline | i /")
            response = self.read_output().splitlines()
            if len(response) > 5:
                response = response[1:-1]
                for line in response:
                    interface = line[0:10].strip()
                    power = line[26:32].strip().replace(".0", "") + "W"
                    self.int_status[interface].update({"power": power})

        return self.int_status


def parse_arguments():
    '''
    Parse command line arguments.

    Main options:
        -c / -C:    specify the commands to send via the command line, with a text file, or by loading an <ipaddress>_autodeploy.txt file automatically
        -d / -D:    specify IP addresses at the command line, or point to a file containing a list of IP addresses
        -u / -p:    specify credentials at the command line - this is NOT SECURE! (for example in your shell history)
                    multiple credentials can be specified as a comma separated list
        -n:         by default the program will go into enable mode at login. We can disable this with --no-enable 
        -s:         we can use --save to save the output to a text file instead of stdout
        -S:         to save the output of each host to a different file
        -O:         use -O filename to save to this filename. Do not forget to use "-s" too
                    use keywords '{date_time}', '{ip_address}' or '{username}' to insert values in the directoy's name
        -b:         use 'batch' mode to send all commands at once instead of reading the output of each command - useful for banner commands for example
        -T:         print output as a one liner per device - ok for short outputs, can be very ugly if the output of the command is more than one line
        --debug:    enable Telnetlib debugging

    '''

    parser = argparse.ArgumentParser(description="Run commands on Cisco devices via Telnet", add_help=False)

    first_arg_group = parser.add_argument_group(title="Devices/Commands")
    arg_device = first_arg_group.add_mutually_exclusive_group(required=True)
    arg_device.add_argument("-d", "--device", help="IP address(es) of the device(s) to connect to (separated by commas)")
    arg_device.add_argument("-D", "--device-list", help="text file containing a list of IP addresses")
    arg_commands = first_arg_group.add_mutually_exclusive_group(required=True)
    arg_commands.add_argument("-c", "--commands", help="command(s) to execute on the device (separated by commas)", nargs="*")
    arg_commands.add_argument("-C", "--command-list", help="text file containing a list of commands to execute")
    arg_commands.add_argument("--autodeploy", help="load commands from file <ipaddress>_autodeploy.txt for each device", action="store_true")

    second_arg_group = parser.add_argument_group(title="Credentials")
    second_arg_group.add_argument("-u", "--username")
    second_arg_group.add_argument("-p", "--password")
    second_arg_group.add_argument("-e", "--enable-password")

    third_arg_group = parser.add_argument_group(title="Save output")
    third_arg_group.add_argument("-s", "--save", help="save the output to text file(s)", action="store_true")
    third_arg_group.add_argument("-O", "--output-directory", help="specify a directory where to save the output to")
    third_arg_group.add_argument("-S", "--separate-output", help="save the output of each device to a separate file", action="store_true")

    fourth_arg_group = parser.add_argument_group(title="Options")
    fourth_arg_group.add_argument("-n", "--no-enable", help="do not go into enable mode", action="store_true")
    fourth_arg_group.add_argument("-b", "--batch", help="send all commands at once (EXPERIMENTAL)", action="store_true")
    fourth_arg_group.add_argument("-T", "--table", help="format output as a table with IP address in first column", action="store_true")
    fourth_arg_group.add_argument("--debug", help="enable Telnet debugging", action="store_true")
    fourth_arg_group.add_argument("-h", "--help", help="display this message and exit", action="help")

    return parser.parse_args()


def main():
    '''
    Pisco.py Main program

    '''
    args = parse_arguments()
    
    # Get list of unique IP addresses from text file or arguments
    if args.device_list:
        with open(args.device_list) as f:
            content = f.readlines()
            list_ip_addresses = []
            for line in content:
                if not line.startswith("!") and not line.startswith("#") and line.strip():
                    for ip_address in re.findall(r"(?:\d{1,3}\.){3}\d{1,3}", line):
                        if ip_address not in list_ip_addresses and not ip_address.startswith("255."):
                            list_ip_addresses.append(ip_address)
    else:
        list_ip_addresses = args.device.split(",")

    # Get command(s) to execute from text file or arguments
    if args.command_list:
        with open(args.command_list, "r") as f:
            commands = [ line.rstrip() for line in f.readlines() if line.strip() ]
    elif args.autodeploy:
        # We will load the commands further up
        pass
    else:
        # Join parts of the command together, else we'll end up with each word as a separate command
        # Specify multiple commands by using a comma
        commands = " ".join(args.commands).split(",")

    # Redirect stdout to screen or file when saving is enabled
    output_file_object = None

    # Timestamping for filename
    date_time = datetime.strftime(datetime.now(), "%Y-%m-%d_%Hh%Mm%S")

    # Iterate over the list of IPs and connect to each of them via Telnet, run the commands, then print the output and close
    for ip_address in list_ip_addresses:
        
        try:
            telnet = TelnetDevice(ip_address, username=args.username, password=args.password, enable_password=args.enable_password, debug=args.debug, quiet=args.table)
        except Exception as e:
            print("[!] Error while connecting to {}".format(ip_address))
            print(str(e)) 
            continue

        if not args.no_enable:
            telnet.enable()

        # Store the credentials so we can reuse them for each device. Remove this part if you want to get prompted each time.
        args.username = telnet.username
        args.password = telnet.password
        args.enable_password = telnet.enable_password

        # Set terminal length 0 to avoid the --More-- prompt with long outputs
        telnet.send_command("terminal length 0")
        telnet.read_output()

        if args.save:
            if args.output_directory:
                save_dir = args.output_directory.format(date_time=date_time, ip_address=ip_address, hostname=telnet.hostname, username=telnet.username)
                if not os.path.exists(save_dir):
                    os.makedirs(save_dir, exist_ok=True)
            else:
                save_dir = os.getcwd()
            if args.separate_output:
                filename = os.path.join(save_dir, "pisco_output_{}_{}_{}.txt".format(telnet.hostname, ip_address, date_time))
            else:
                filename = os.path.join(save_dir, "pisco_output_{}.txt".format(date_time))
            output_file_object = open(filename, "a")
            print("[+] Saving output to {}...".format(filename), end="")

        if args.autodeploy:
            filename = "{}_autodeploy.txt".format(ip_address)
            if os.path.exists(filename):
                with open(filename, "r") as f:
                    commands = [ line.rstrip() for line in f.readlines() if line.strip() ]
            else:
                print("[!] No autodeploy file found. Skipping device.")
                continue

        if args.batch:
            # EXPERIMENTAL!
            telnet.send_command("")
            for c in commands:
                telnet.send_command(c)
                time.sleep(0.3)
            telnet.send_command("\x1A")
            telnet.send_command("exit")
            response = telnet.read_all().decode("Latin-1")
            print("\n[{}] {} ({}): Output of batch commands:\n{}\n".format(telnet.when, telnet.host, telnet.hostname, response), file=output_file_object)
        else:
            for c in commands:
                telnet.send_command(c)
                time.sleep(0.1)
                response = telnet.read_output()
                # Clean up the output a little bit by removing the first and last lines (IOS prompts)
                if len(response.splitlines()) > 1:            
                    response = response.splitlines()
                    response.pop(0)
                    response.pop(-1)
                    response = "\n".join(response)
                if args.table:
                    print("{}\t{}\t{}".format(telnet.host, telnet.hostname, response.replace("\n", "").replace("\r", "")), file=output_file_object)
                else:
                    print("\n[{}] {} ({}): Output of command '{}'\n{}\n".format(telnet.when, telnet.host, telnet.hostname, c, response), file=output_file_object)
            telnet.close()

        if args.save:
            print(" Done\n")
    
    if output_file_object:
        output_file_object.close()

    sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        sys.exit(1)
