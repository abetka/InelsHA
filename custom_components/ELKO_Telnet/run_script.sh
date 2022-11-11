dupe_script=$(ps -ef | grep "listener.py" | grep -v grep | wc -l | xargs)

if [ ${dupe_script} -gt 0 ]; then
    echo "The listener.py script was already running!"
    exit 0
else
    python3 listener.py > listener_stdout.log &
    echo "The listener.py script restarted!"
fi