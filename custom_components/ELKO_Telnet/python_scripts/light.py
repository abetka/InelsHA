host = '192.168.88.246'
port = 1111
delimiter = ';'
device_id = data.get("device_id")
brightness = data.get("brightness","100")
transition = data.get("transition","1")
rgb_color = data.get("rgb_color")

def telnet_command(command) -> str | None:
    try:
        logger.debug("Telnet connect to: %s with port: %s", host, port)
        telnet = telnetlib.Telnet(host, port)
        telnet.write(command)
        response = telnet.read_until(b"\r\n").decode('ascii').split(delimiter)[2].rstrip("\r").rstrip("\n")
        telnet.close()
    except OSError as error:
        logger.error(
            'Command "%s" failed with exception: %s', command, repr(error)
        )
        return None
    logger.debug("Telnet response: %s", response)
    return response

def turn_on() -> None:
    """Turn the device on."""
    command = b"SET" + delimiter.encode('ascii') + device_id.encode('ascii')+ delimiter.encode('ascii')+ brightness.encode('ascii') + b"\r\n"
    logger.debug("Turn On: %s", command)
    telnet_command(command)
    # if self.assumed_state:
    #     self._attr_is_on = True
    #     self.schedule_update_ha_state()

def turn_off() -> None:
    """Turn the device off."""
    command = b"SET" + delimiter.encode('ascii') + device_id.encode('ascii')+ delimiter.encode('ascii') + b"0\r\n"
    logger.debug("Turn Off: %s", command)
    telnet_command(command)
    # if self.assumed_state:
    #     self._attr_is_on = False
    #     self.schedule_update_ha_state()