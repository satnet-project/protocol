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

function create_supervisor_conf()
{

    echo "[supervisord]" | sudo tee $output_conf_file
    echo "logfile=/var/log/supervisor.log" | sudo tee -a $output_conf_file
    echo "[program:satnet-protocol]" | sudo tee -a $output_conf_file
    echo "command=$runner_sh" | sudo tee -a $output_conf_file
    echo "environment=PATH=\"$venv_dir/bin\"" | sudo tee -a $output_conf_file
    echo "directory=$project_path" | sudo tee -a $output_conf_file
    echo "autostart=true" | sudo tee -a $output_conf_file
    echo "autorestart=false" | sudo tee -a $output_conf_file
    echo "stdout_logfile=$logs_dir/output.log" | sudo tee -a $output_conf_file
    echo "stdout_logfile_maxbytes=10MB" | sudo tee -a $output_conf_file
    echo "stdout_logfile_backups=10" | sudo tee -a $output_conf_file
    echo "stderr_logfile=$logs_dir/error.log" | sudo tee -a $output_conf_file
    echo "stderr_logfile_maxbytes=10MB" | sudo tee -a $output_conf_file
    echo "stderr_logfile_backups=10" | sudo tee -a $output_conf_file

}

function remove_supervisor_conf()
{

	echo ">>> Removing satnet-protocol's configuration from within supervisord"

	[[ -f $output_conf_file ]] && {

		sudo rm -f $output_conf_file
		echo ">>> $output_conf_file removed"

	} || {
		echo ">>> <$output_conf_file> not found, skipping removal..."
	}

}

function create_runner_sh()
{

    echo "#!/bin/bash" | sudo tee $runner_sh
    echo "" | sudo tee -a $runner_sh
    echo "source $venv_dir/bin/activate" | sudo tee -a $runner_sh
    # echo "python server_amp.py" | sudo tee -a $runner_sh
    echo "twistd procmon python server_amp.py" | sudo tee -a $runner_sh
    echo "" | sudo tee -a $runner_sh

    chmod +x $runner_sh

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

function configure_supervisor()
{
    echo ">>> Configuration Supervisor"
    create_runner_sh
    create_supervisor_conf
	sudo supervisorctl reread
	sudo supervisorctl update
}

script_path="$( cd "$( dirname "$0" )" && pwd )"
project_path=$( readlink -e "$script_path/.." )

linux_packages="$script_path/debian.packages"
venv_dir="$project_path/.venv"

runner_sh="$script_path/satnet-protocol.sh"
logs_dir="$project_path/logs"
target_supervisor_confd='/etc/supervisor/conf.d'
output_conf_file="$target_supervisor_confd/satnet-protocol.conf"

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
_config_supervisor='true'
_install_pyqt4='false'
_install_sip='false'
_install_desk_shortcuts='false'

if [ $1 == '-install' ];
then

	echo ">>> Installing satnet-protocol..."

    [[ $_install_packages == 'true' ]] && install_packages
    [[ $_install_venv == 'true' ]] && install_venv

    # This installation steps are not mandatory (GUI not required)

    [[ $_generate_keys == 'true' ]] && create_selfsigned_keys
    [[ $_create_logs == 'true' ]] && create_logs_dir

    [[ $_config_supervisor == 'true' ]] && configure_supervisor

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

	echo ">>> [TravisCI] Installing satnet-protocol..."
    [[ $_install_venv == 'true' ]] && install_venv
	exit 0

fi

if [ $1 == '-circleCI' ];
then

	echo ">>> [CircleCI] Installing satnet-protocol..."
    [[ $_install_venv == 'true' ]] && install_venv
    exit 0

fi

if [ $1 == '-uninstall' ];
then

	echo ">>> Removing satnet-protocol..."
	echo ">>> NOTICE: this command only removes external dependencies"
	echo ">>> NOTICE: to fully remove this program, delete this directory"

	[[ $_config_supervisor == 'true' ]] && remove_supervisor_conf
	[[ $_install_packages == 'true' ]] && uninstall_packages

	exit 0

fi

