#!/usr/bin/env bash

twistd -y "../server_amp_daemon.py"\
    -l "../logs/test.log"\
    --pidfile "../.satnet.pid"
