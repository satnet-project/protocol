#!/bin/bash
script_path="$( cd "$( dirname "$0" )" && pwd )"
project_path=$( readlink -e "$script_path/.." )

if [ $1 == '-install' ];
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
	sudo apt --assume-yes install shc
	sudo apt --assume-yes --force-yes install unzip

	# Create a virtualenv
	virtualenv $venv_path
	source "$venv_path/bin/activate"
	pip install -r "$project_path/requirements.txt"

	# Downloading packages for GUI
	# Needed to install SIP first
	cd $venv_path
	mkdir build && cd build
	pip install SIP --allow-unverified SIP --download="."
	unzip sip*
	echo "antes de uno"
	pwd
	ls
	cd sip*
	python configure.py
	make
	sudo make install
	cd ../ && rm -r -f sip*

	# PyQt4 installation.
	wget http://downloads.sourceforge.net/project/pyqt/PyQt4/PyQt-4.11.4/PyQt-x11-gpl-4.11.4.tar.gz
	tar xvzf PyQt-x11-gpl-4.11.4.tar.gz
	cd PyQt-x11-gpl-4.11.4
	python ./configure.py --confirm-license --no-designer-plugin -q /usr/bin/qmake-qt4 -e QtGui -e QtCore
	make
	# Bug. Needed ldconfig, copy it from /usr/sbin
	cp /sbin/ldconfig ../../bin/
	sudo ldconfig
	sudo make install
	cd ../ && rm -r -f PyQt*

	# Create a self-signed certicate
	bash "$script_path/protocol-setup.sh"

	# Supervisor install
	sudo apt --assume-yes install supervisor

	echo ">>> This script will generate a daemon for SATNet protocol"
	echo ">>> Populating directories"
	mkdir ~/.satnet/
	mkdir ~/.satnet/logs/
	sudo mkdir /opt/satnet
	sudo cp -r -f ../../protocol /opt/satnet/

	currentUser=$(whoami)

	cd $script_path
	sudo shc -f satnetprotocol.sh
	sudo rm satnetprotocol.sh.x.c
	sudo chmod 777 satnetprotocol.sh.x
	sudo chown $currentUser satnetprotocol.sh.x
	mv satnetprotocol.sh.x satnetprotocol

	mkdir ~/bin/
	mv satnetprotocol ~/bin/

	cp satnetprotocol.desktop ~/Escritorio
	cp satnetprotocol.desktop ~/Desktop

	echo ">>> Copying daemons"
	sudo cp satnet-protocol.sh /usr/local/bin
	sudo chmod +x /usr/local/bin/satnet-protocol.sh
	sudo cp satnet-protocol-conf.conf /etc/supervisor/conf.d/

	echo ">>> Updating Supervisor"
	sudo supervisorctl reread
	sudo supervisorctl update

	currentUser=$(whoami)
	sudo chown $currentUser ~/.satnet/logs/* 

	echo ">>> For apply changes you must reboot your system"
	echo ">>> Reboot now? (yes/no)"
	read OPTION
	if [ $OPTION == 'yes' ];
	then
		sudo reboot
	fi
fi

if [ $1 == '-travisCI' ];
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

if [ $1 == '-circleCI' ];
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

if [ $1 == '-uninstall' ];
then
	echo ">>> Removing program files"
	sudo rm -r -f /opt/satnet/

	echo ">>> Removing the daemon for SATNet protocol"
	sudo rm /usr/local/bin/satnet-protocol.sh
	sudo rm /etc/supervisor/conf.d/satnet-protocol-conf.conf

	echo ">>> Removing old logs"
	rm ~/.satnet/logs/*

	echo ">>> Removing executables"
	rm ~/bin/satnetprotocol

	echo ">>> Removing links"
	rm ~/Desktop/satnetprotocol.desktop
	rm ~/Escritorio/satnetprotocol.desktop

	sudo apt --assume-yes remove supervisor
	sudo apt --assume-yes remove build-essential
	sudo apt --assume-yes remove python-dev
	sudo apt --assume-yes remove python-pip
	sudo apt --assume-yes remove virtualenv
	sudo apt --assume-yes remove libffi-dev
	sudo apt --assume-yes remove libssl-dev
	sudo apt --assume-yes remove libpq-dev
	sudo apt --assume-yes remove shc
	sudo apt --assume-yes remove unzip

	echo ">>> Do you wish to remove all configuration files? (yes/no)"
	read OPTION
	if [ $OPTION == 'yes' ];
	then
		rm -r -f ~/.satnet
	fi
fi


if [ $1 == '-update' ];
then
	echo ">>> This script will update protocol files and directories"
	echo ">>> Removing old data"
	sudo rm -rf /opt/satnet/

	echo ">>> Downloading new data" # To-do. Download new server data.
	wget https://github.com/satnet-project/protocol/archive/jrpc_if.zip
	unzip jrpc_if

	echo ">>> Copying new data"
	sudo mkdir /opt/satnet/
	sudo mkdir /opt/satnet/protocol/
	sudo cp -rf protocol-jrpc_if/* /opt/satnet/protocol/
	rm -rf protocol-jrpc_if/

	echo ">>> Installing new protocol"
	# cd /opt/satnet/protocol/scripts

	echo ">>> Updating daemon protocol"
	sudo rm /usr/local/bin/satnet-protocol.sh
	sudo rm /etc/supervisor/conf.d/satnet-protocol-conf.conf
	sudo cp satnet-protocol.sh /usr/local/bin
	sudo chmod +x /usr/local/bin/satnet-protocol.sh
	sudo cp satnet-protocol-conf.conf /etc/supervisor/conf.d/

	echo ">>> Updating Supervisor"
	sudo supervisorctl update

fi
