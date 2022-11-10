#!/usr/bin/python3

import sys, getopt, telnetlib

telnet_host = ''
telnet_port = ''
sensor_id = ''
_delimiter = ';'

def main(argv):
    try:
        opts, args = getopt.getopt(argv,"h:p:i:")
    except getopt.GetoptError:
        print ('get_data.py -h <host> -p <port> -id <sensor_id>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            telnet_host = arg
        elif opt == '-p':
            telnet_port = arg
        elif opt == '-i':
            sensor_id = arg
    command = b"GET" + _delimiter.encode('ascii') + sensor_id.encode('ascii') + b"\r\n"
    print (telnet_command( telnet_host, telnet_port, command, _delimiter))

def telnet_command(host, port, command, delimiter):
    try:
        telnet = telnetlib.Telnet( host, port)
        telnet.write(command)
        response = telnet.read_until(b"\r\n").decode('ascii').split(delimiter)[2].rstrip("\r").rstrip("\n")
        telnet.close()
    except OSError as error:
        print (
            'Command failed with exception: ' + command.decode('ascii') + " error: " + repr(error)
        )
        return None
    return response

if __name__ == "__main__":
   main(sys.argv[1:])