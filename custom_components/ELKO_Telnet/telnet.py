import telnetlib
import logging

#--configuration

_LOGGER = logging.getLogger(__name__)

def command(**kwargs ) -> str | None:
    try:
        _LOGGER.debug("Telnet connect to: %s with port: %s", kwargs['host'], kwargs['port'])
        telnet = telnetlib.Telnet(kwargs['host'], kwargs['port'])
        telnet.write(kwargs['telnet_command'])
        response = telnet.read_until(b"\r\n").decode('ascii').split(kwargs['delimiter'])[2].rstrip("\r").rstrip("\n")
        telnet.close()
    except OSError as error:
        _LOGGER.error(
            'Command "%s" failed with exception: %s', command, repr(error)
        )
        return None
    _LOGGER.debug("Telnet response: %s", response)
    return response

def getData( **kwargs ) -> str | None:
    _LOGGER.debug("kwargs: %s", kwargs.keys())
    kwargs.update({
        'telnet_command': b"GET" + kwargs['delimiter'].encode('ascii') + kwargs['device_id'].encode('ascii') + b"\r\n",
    })
    _LOGGER.debug("command line: %s", kwargs['telnet_command'])
    return command(**kwargs)

def setData( **kwargs ) -> str | None:
    _LOGGER.debug("kwargs: %s", kwargs.keys())
    kwargs.update({
        'telnet_command': b"SET" + kwargs['delimiter'].encode('ascii') + kwargs['device_id'].encode('ascii')+ kwargs['delimiter'].encode('ascii')+ kwargs['command'].encode('ascii') + b"\r\n"
    })
    _LOGGER.debug("command line: %s", kwargs['telnet_command'])
    return command(**kwargs)
