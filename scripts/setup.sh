#!/bin/bash
script_path="$( cd "$( dirname "$0" )" && pwd )"
project_path=$( readlink -e "$script_path/.." )

if [ $1 == '-i' ];
then
	venv_path="$project_path/.venv"

	# Install required packages
	sudo apt --assume-yes install build-essential
	sudo apt --assume-yes install python-dev
	sudo apt --assume-yes install python-pip
	sudo apt --assume-yes install virtualenv
	sudo apt --assume-yes install libffi-dev
	sudo apt --assume-yes install libssl-dev
	sudo apt --assume-yes install libpq-dev

	# Create a virtualenv
	virtualenv $venv_path
	source "$venv_path/bin/activate"
	pip install -r "$project_path/requirements.txt"

	# Create a self-signed certicate
	bash "$script_path/protocol-setup.sh"

	# Supervisor install
	sudo apt --assume-yes install supervisor

	echo ">>> This script will generate a daemon for SATNet protocol"
	sudo mkdir /opt/satnet

	pwd

	sudo cp -r -f ../../protocol /opt/satnet/

	sudo cp satnet-protocol.sh /usr/local/bin
	sudo chmod +x /usr/local/bin/satnet-protocol.sh

	sudo cp satnet-protocol-conf.conf /etc/supervisor/conf.d/

	sudo supervisorctl reread
	sudo supervisorctl update

elif [ $1 == '-travisCI' ];
then
	venv_path="$project_path/.venv"

	# Install required packages
	# sudo apt --assume-yes install build-essential
	# sudo apt --assume-yes install python-dev
	# sudo apt --assume-yes install python-pip
	# sudo apt --assume-yes install virtualenv
	# sudo apt --assume-yes install libffi-dev
	# sudo apt --assume-yes install libssl-dev
	# sudo apt --assume-yes install libpq-dev

	# Create a virtualenv
	# virtualenv $venv_path
	# source "$venv_path/bin/activate"
	pip install -r "$script_path/requirements-tests.txt"

	# Create a self-signed certicate
	# bash "$script_path/protocol-setup.sh"

fi
