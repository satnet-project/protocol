#!/bin/bash
script_path="$( cd "$( dirname "$0" )" && pwd )"
project_path=$( readlink -e "$script_path/.." )
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
