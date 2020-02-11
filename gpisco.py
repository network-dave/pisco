import pisco
from functools import partial
from gooey import Gooey, GooeyParser

'''

gPisco.py

Add a Gooey (GUI) to pisco.py

'''

@Gooey(program_name="Pisco Command Runner", default_size=(1000,800), show_sidebar=False, terminal_font_family="Courier New")
def gooey_arguments():
    '''
    Overwrite the argument parser from pisco.py with a Gooey parser
    '''

    parser = GooeyParser(description="Run commands on Cisco devices via Telnet", add_help=False)

    first_arg_group = parser.add_argument_group(title="Commands / Devices")
    arg_device = first_arg_group.add_mutually_exclusive_group(required=True)
    arg_device.add_argument("-d", "--device", help="IP address(es) of the device(s) to connect to (separated by commas)")
    arg_device.add_argument("-D", "--device-list", help="text file containing a list of IP addresses (one address per line)", widget="FileChooser")
    arg_commands = first_arg_group.add_mutually_exclusive_group(required=True)
    arg_commands.add_argument("-c", "--commands", help="command(s) to execute on the device (separated by commas)", nargs="*")
    arg_commands.add_argument("-C", "--command-list", help="text file containing a list of commands to execute", widget="FileChooser")
    arg_commands.add_argument("--autodeploy", help="load list of commands from file <ipaddress>_autodeploy.txt for each device", action="store_true")

    second_arg_group = parser.add_argument_group(title="Credentials")
    second_arg_group.add_argument("-u", "--username",required=True)
    second_arg_group.add_argument("-p", "--password", widget="PasswordField",required=True)
    second_arg_group.add_argument("-e", "--enable-password", widget="PasswordField")

    third_arg_group = parser.add_argument_group(title="Save output")
    third_arg_group.add_argument("-s", "--save", help="save the output to text file(s)", action="store_true")
    third_arg_group.add_argument("-O", "--output-directory", help="specify a directory where to save the output to", widget="FileChooser")
    third_arg_group.add_argument("-S", "--separate-output", help="save the output of each device to a separate file", action="store_true")

    fourth_arg_group = parser.add_argument_group(title="Options")
    fourth_arg_group.add_argument("-n", "--no-enable", help="do not go into enable mode after login", action="store_true", default=True)
    fourth_arg_group.add_argument("-b", "--batch", help="send all commands at once (EXPERIMENTAL)", action="store_true")
    fourth_arg_group.add_argument("-T", "--table", help="format output as a table with IP address in first position", action="store_true")
    fourth_arg_group.add_argument("--debug", help="enable Telnet debugging", action="store_true")
    fourth_arg_group.add_argument("-h", "--help", help="display this message and exit", action="help")

    return parser.parse_args()


# STDOUT is buffered by default, this is needed to output the print statements in real time
print = partial(print, flush=True)

pisco.parse_arguments = gooey_arguments
pisco.main()
