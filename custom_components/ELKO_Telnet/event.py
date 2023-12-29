import telnetlib
import logging

class ELKOEvents(EventEntity):
    #--configuration
    tn_ip = "192.168.88.246"
    tn_port = "1111"
    _attr_device_class = EventDeviceClass.BUTTON
    _attr_event_types = ["single_press", "double_press"]

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

    # @callback
    # def _async_handle_event(self, event: str) -> None:
    #     """Handle the demo button event."""
        # self._trigger_event(event, {"extra_data": 123})
        # self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
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
                logging.debug("event ELKO, trigered with parameters " + event_data )
                self._trigger_event("ELKO", event_data)
                self.async_write_ha_state()