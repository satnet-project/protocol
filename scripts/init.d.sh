#! /bin/sh
### BEGIN INIT INFO
# Provides:          ghserver
# Required-Start:    $local_fs $remote_fs $network $syslog
# Required-Stop:     $local_fs $remote_fs $network $syslog
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Start/stop GHServer server
### END INIT INFO

logger "GHServer: Start script executed"
GH_SERVER_PATH="/home/myname/Python/ghserver"
export PYTHONPATH="$GH_SERVER_PATH:$PYTHONPATH"

case "$1" in
  start)
    logger "GHServer: Starting"
    echo "Starting GHServer..."
    twistd -y "$GH_SERVER_PATH/ghserverapp.py" -l "$GH_SERVER_PATH/ghserver.log" --pidfile "$GH_SERVER_PATH/twistd.pid"
    ;;
  stop)
    logger "GHServer: Stopping"
    echo "Stopping GHServer..."
    kill `cat $GH_SERVER_PATH/twistd.pid`
    ;;
  *)
    logger "GHServer: Invalid usage"
    echo "Usage: /etc/init.d/ghserver {start|stop}"
    exit 1
    ;;
esac

exit 0
