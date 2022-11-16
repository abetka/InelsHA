import os
import logging
logging.basicConfig( filename='if_run.log', level=logging.DEBUG )

def checkServiceStatus():
    try:
        for line in os.popen("ps aux | grep 'listener.py' | grep -v grep | wc -l | xargs"):
            if int(line) >= 1:
                logging.debug("The listener.py script was already running!")
            else:
                os.popen("python3 custom_components/ELKO_telnet/listener.py > listener_stdout.log &")
                logging.debug("The listener.py script restarted!")
    except OSError as ose:
        logging.error('The problem with checking ' + ose)

    pass

if __name__ == '__main__':
    checkServiceStatus()