[![Code Health](https://landscape.io/github/satnet-project/protocol/jrpc_if/landscape.svg?style=flat)](https://landscape.io/github/satnet-project/protocol/jrpc_if)

# protocol
This repository contains the communications real time protocol based on Twisted for the SatNet network.

## Install server
```shell
git clone git@github.com:satnet-project/protocol.git
virtualenv .venv
source .venv/bin/activate
pip install -r scripts/requirements.txt
# The last step will create a self-signed certificate/key
/scripts/protocol-setup.sh
```

## Run server
```shell
cd {PROJECT_PATH}
python server_amp.py
```

## Execute tests
```shell
cd {PROJECT_PATH}
trial tests/*
```
