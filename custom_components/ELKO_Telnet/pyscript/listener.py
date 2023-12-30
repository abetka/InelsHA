import telnetlib

tn_ip = "192.168.88.246"
tn_port = "1111"
def connect(host = tn_ip,port = tn_port):
    try:
        tn = telnetlib.Telnet(host, port, 15)
    except BaseException as e:
        log.error('Event listener: Failed to connect to Telnet server: ' + str(e))
        if e.errno == 51:
            time.sleep(5)
            connect(host,port)
            log.error('Event listener: Try to connect to Telnet server again')
        return
    tn.set_debuglevel(100)
    return tn

@time_trigger
def ELKOlistener():
    task.unique("ELKOlistener")
    try:
        tn = connect()
        while True:
            try:
                line = tn.read_until(b"\r\n")
                log.debug("Event listener: Used Current Telnet Session")
            except EOFError:
                time.sleep(5)
                tn = connect()
                line = tn.read_until(b"\r\n")
                log.debug("Event listener: It seems The previous session was closed so was used a new one.")
            splitted_line = line.decode('ascii').split(';')
            if 'EVENT' in splitted_line[0]:
                log.debug("Event listener: " + splitted_line )
                event_data = {
                    "event_id": splitted_line[1],
                    "device_code": splitted_line[2],
                    "device_state": splitted_line[3].rstrip("\n").rstrip("\r")
                }
                log.debug("Event listener: " + event_data)
                event.fire("ELKO", event_data )
    except (KeyboardInterrupt, SystemExit):
        logging.debug("The application was closed")