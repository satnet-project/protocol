#!/bin/bash

#    Copyright 2015 Samuel Góngora García
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#
# :Author:
#     Samuel Góngora García (s.gongoragarcia@gmail.com)
#
# __author__ = 's.gongoragarcia@gmail.com'

function create_selfsigned_keys()
{

    [[ -d $keys_dir ]] || {
        echo '>>> Creating keys directory...'
        mkdir -p $keys_dir
    } && {
        echo ">>> $keys_dir exists, skipping..."
    }

    [[ -f $keys_server_pem ]] && [[ -f $keys_public_pem ]] && {
        echo ">>> Keys already exist, skipping key generation..."
        return
    }

    # 1: Generate a Private Key
    echo '>>> Generating a private key'
    openssl genrsa -des3 -passout pass:satnet -out $keys_private 1024
    # 2: Generate a CSR (Certificate Signing Request)
    echo '>>> Generating a CSR'
    openssl req -new -key $keys_private -passin pass:satnet\
    	-out $keys_csr -subj "/CN=$keys_CN"
    # 3: Remove Passphrase from Private Key
    echo '>>> Removing passphrase from private key'
    openssl rsa -in $keys_private -passin pass:satnet -out $keys_private
    # 4: Generating a Self-Signed Certificate
    echo '>>> Generating a public key (certificate)'
    openssl x509 -req -days 365 -in $keys_csr -signkey $keys_private\
    	-out $keys_crt

    echo '>>> Generating key bundles'
    # 5: Generate server bundle (Certificate + Private key)
    cat $keys_crt $keys_private > $keys_server_pem
    # 6: Generate clients bundle (Certificate)
    cp $keys_crt $keys_public_pem

}

function create_daemon()
{
    echo '#! /bin/bash' | tee $initd_sh
    echo '### BEGIN INIT INFO' | tee -a $initd_sh
    echo '# Provides:          satnetprotocol' | tee -a $initd_sh
    echo '# Required-Start:    $local_fs $remote_fs $network $syslog' | tee -a $initd_sh
    echo '# Required-Stop:     $local_fs $remote_fs $network $syslog' | tee -a $initd_sh
    echo '# Default-Start:     2 3 4 5' | tee -a $initd_sh
    echo '# Default-Stop:      0 1 6' | tee -a $initd_sh
    echo '# Short-Description: Start/stop SatNet protocol' | tee -a $initd_sh
    echo '### END INIT INFO' | tee -a $initd_sh
    echo '' | tee -a $initd_sh
    echo 'logger "satnetprotocol: Start script executed"' | tee -a $initd_sh
    echo "SATNET_PROTOCOL_PATH=$project_path" | tee -a $initd_sh
    echo 'export PYTHONPATH="$SATNET_PROTOCOL_PATH:$PYTHONPATH"' | tee -a $initd_sh
    echo '' | tee -a $initd_sh
    echo 'case "$1" in' | tee -a $initd_sh
    echo '  start)' | tee -a $initd_sh
    echo '    logger "satnetprotocol: Starting"' | tee -a $initd_sh
    echo '    echo "Starting SatNet protocol..."' | tee -a $initd_sh
    echo '    source "$SATNET_PROTOCOL_PATH/.venv/bin/activate"' | tee -a $initd_sh
    echo '    twistd -y "$SATNET_PROTOCOL_PATH/server_amp_daemon.tac" -l "$SATNET_PROTOCOL_PATH/server_amplog.log" --pidfile "SATNET_PROTOCOL_PATH/twistd.pid"' | tee -a $initd_sh
    echo '    ;;' | tee -a $initd_sh
    echo '  stop)' | tee -a $initd_sh
    echo '    logger "satnetprotocol: Stopping"' | tee -a $initd_sh
    echo '    [[ -d $SATNET_PROTOCOL_PATH/twistd.pid ]] || {' | tee -a $initd_sh
    echo '        echo "Stopping SatNet protocol..."' | tee -a $initd_sh
    echo '        kill `cat $SATNET_PROTOCOL_PATH/twistd.pid`' | tee -a $initd_sh
    echo '    } && {' | tee -a $initd_sh
    echo '        echo "SatNet protocol not running"' | tee -a $initd_sh
    echo '    }' | tee -a $initd_sh
    echo '    ;;' | tee -a $initd_sh
    echo '  *)' | tee -a $initd_sh
    echo '    logger "satnetprotocol: Invalid usage"'  | tee -a $initd_sh
    echo '    echo "Usage: /etc/init.d/satnetprotocol {start|stop}"' | tee -a $initd_sh
    echo '    exit 1' | tee -a $initd_sh
    echo '    ;;' | tee -a $initd_sh
    echo 'esac' | tee -a $initd_sh
    echo '' | tee -a $initd_sh
    echo 'exit 0' | tee -a $initd_sh
    echo '' | tee -a $initd_sh

    sudo chmod 755 $initd_sh 

}

function install_packages()
{
	echo ">>> Installing system packages..."
	sudo aptitude update && sudo aptitude dist-upgrade -y
	sudo aptitude install $( cat "$linux_packages" ) -y
}

function uninstall_packages()
{
	echo ">>> Uninstalling system packages..."
	sudo aptitude remove $( cat "$linux_packages" ) -y
}

function install_venv()
{
	[[ -d $venv_dir ]] || {

    	echo ">>> Creating virtual environment..."
    	virtualenv --python=python2.7 $venv_dir
    	source "$venv_dir/bin/activate"
	    pip install -r "$project_path/requirements.txt"
	    deactivate

	} && {
	    echo ">>> Python Virtual environment found, skipping"
	}
}

function create_logs_dir()
{
	[[ -d $logs_dir ]] || {

    	echo ">>> Creating logging directory = $logs_dir"
    	mkdir -p $logs_dir

    } && {
        echo ">>> $logs_dir exists, skipping"
    }
}

function config_daemon()
{
    echo ">>> Creating daemon"
    [[ $_config_daemon == 'true' ]] && create_daemon

    sudo chmod 755 $initd_sh
    sudo mv $initd_sh /etc/init.d/

    sudo chown root:root /etc/init.d/satnetprotocol

    sudo update-rc.d satnetprotocol defaults
    sudo update-rc.d satnetprotocol enable
}

script_path="$( cd "$( dirname "$0" )" && pwd )"
project_path=$( readlink -e "$script_path/.." )

linux_packages="$script_path/debian.packages"
venv_dir="$project_path/.venv"

initd_sh="$script_path/satnetprotocol"
logs_dir="$project_path/logs"

keys_dir="$project_path/key"
keys_private="$keys_dir/test.key"
keys_csr="$keys_dir/test.csr"
keys_crt="$keys_dir/test.crt"
keys_server_pem="$keys_dir/server.pem"
keys_public_pem="$keys_dir/public.pem"
keys_CN="edu.calpoly.aero.satnet"

_install_venv='true'
_install_packages='true'
_generate_keys='true'
_create_logs='true'
_config_daemon='true'

if [ $1 == '-install' ];
then

	echo ">>> Installing satnet-protocol..."

    [[ $_install_packages == 'true' ]] && install_packages
    [[ $_install_venv == 'true' ]] && install_venv

    [[ $_config_daemon == 'true' ]] && config_daemon

    [[ $_generate_keys == 'true' ]] && create_selfsigned_keys
    [[ $_create_logs == 'true' ]] && create_logs_dir

    [[ $_reboot == 'true' ]] && {

    	echo ">>> To apply changes you must reboot your system"
    	echo ">>> Reboot now? (yes/no)"
    	read OPTION
    	[[ $OPTION == 'yes' ]] && sudo reboot

    }

	exit 0

fi

if [ $1 == '-travisCI' ];
then

	echo ">>> [TravisCI] Installing satnetprotocol..."
    [[ $_install_venv == 'true' ]] && install_venv
	exit 0

fi

if [ $1 == '-circleCI' ];
then

	echo ">>> [CircleCI] Installing satnetprotocol..."
    [[ $_install_venv == 'true' ]] && install_venv
    exit 0

fi

if [ $1 == '-uninstall' ];
then

	echo ">>> Removing satnetprotocol..."
	echo ">>> NOTICE: this command only removes external dependencies"
	echo ">>> NOTICE: to fully remove this program, delete this directory"

	[[ $_install_packages == 'true' ]] && uninstall_packages

	exit 0

fi
