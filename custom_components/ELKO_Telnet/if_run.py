import os
import logging
logging.basicConfig( filename='if_run.log', level=logging.DEBUG )

def checkServiceStatus():
    try:
        os.popen("apt-get -y update")
        os.popen("apt-get install -y procps")
        for line in os.popen("ps aux | grep 'listener.py' | grep -v grep | wc -l | xargs"):
            if int(line) >= 1:
                logging.debug("The listener.py script was already running! Try to restart script")
                os.popen("ps -fu $USER| grep 'listener.py' | grep -v 'grep' | awk '{print $2}'| xargs -n1 kill ")
                os.popen("python3 listener.py > listener_stdout.log &")
                logging.debug("The listener.py script was restarting")
            else:
                os.popen("python3 listener.py > listener_stdout.log &")
                logging.debug("The listener.py script started!")
    except OSError as ose:
        logging.error('The problem with checking ' + ose)

    pass

if __name__ == '__main__':
    while True:
        checkServiceStatus()
        time.sleep(10)