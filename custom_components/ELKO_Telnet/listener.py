import sys
import telnetlib
import logging
import requests
from homeassistant.core import HomeAssistant
#--configuration
hass_url = "http://192.168.88.247:8123/api/webhook/"
tn_ip = "192.168.88.246"
tn_port = "1111"

logging.basicConfig( filename='listener.log', level=logging.DEBUG )

def connect(host = tn_ip,port = tn_port):
    try:
        tn = telnetlib.Telnet(tn_ip, tn_port, 15)
    except BaseException as e:
        logging.error('Failed to connect to Telnet server: ' + str(e))
        if e.errno == 51:
            time.sleep(5)
            connect(host,port)
            logging.error('Try to connect to Telnet server again')
        return
    tn.set_debuglevel(100)
    return tn

if __name__ == '__main__':
    try:
        tn = connect()
        while True:
            try:
                line = tn.read_until(b"\r\n")
                logging.debug("Used Current Telnet Session")
            except EOFError:
                time.sleep(5)
                tn = connect()
                line = tn.read_until(b"\r\n")
                logging.debug("It seems The previous session was closed so was used a new one.")
            splitted_line = line.decode('ascii').split(';')
            if 'EVENT' in splitted_line[0]:
                logging.debug(line)
                event_data = {
                    "event_id": splitted_line[1],
                    "device_code": splitted_line[2],
                    "device_state": splitted_line[3].rstrip("\n").rstrip("\r")
                }
                HomeAssistant.bus.async_fire("ELKO_telnet", event_data)
                # headers = {'Content-Type': 'application/json'}
                # print (event_data)
                # uri = hass_url + splitted_line[2]
                # print (uri)
                # requests.post( uri, json=event_data, headers=headers )
    except (KeyboardInterrupt, SystemExit):
        logging.debug("The application was closed")