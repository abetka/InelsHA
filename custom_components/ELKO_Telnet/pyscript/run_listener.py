import os

def checkServiceStatus():
    try:
        os.popen("apt-get -y update")
        os.popen("apt-get install -y procps")
        for line in os.popen("ps aux | grep 'listener.py' | grep -v grep | wc -l | xargs"):
            if int(line) >= 1:
                log.debug("The listener.py script was already running! Try to restart script")
                os.popen("ps -fu $USER| grep 'listener.py' | grep -v 'grep' | awk '{print $2}'| xargs -n1 kill ")
                os.popen("python3 custom_components/ELKO_telnet/listener.py > listener_stdout.log &")
                log.debug("The listener.py script was restarting")
            else:
                os.popen("python3 custom_components/ELKO_telnet/listener.py > listener_stdout.log &")
                log.debug("The listener.py script started!")
    except OSError as ose:
        log.error('The listener.py: The problem with checking ' + ose)

    pass

@time_trigger
def ELKO_Run_listener():
    task.unique("ELKO_Run_listener")
    checkServiceStatus()