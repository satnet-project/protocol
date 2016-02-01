#!/bin/bash

__script_path="$( cd "$( dirname "$0" )" && pwd )"
__project_path="$( readlink -e "$__script_path/.." )"

__logs_dir="$__project_path/logs"
__venv_dir="$__project_path/.venv"

__output_file="$( echo $0 | sed -e 's/\.sh//g' )"

echo ">>> $__output_file"
echo ">>> $__project_path"

echo "[supervisord]" | tee $__output_file
echo "logfile=/var/log/supervisor.log" | tee -a $__output_file
echo "[program:satnet-protocol]" | tee -a $__output_file
echo "command=$__venv_dir/bin/python server_amp.py" | tee -a $__output_file
echo "environment=PATH=\"$__venv_dir/bin:$PATH\"" | tee -a $__output_file
echo "directory=$__project_path" | tee -a $__output_file
echo "autostart=true" | tee -a $__output_file
echo "autorestart=true" | tee -a $__output_file
echo "stderr_logfile=$__logs_dir/error.log" | tee -a $__output_file
echo "stdout_logfile=$__logs_dir/output.log" | tee -a $__output_file

