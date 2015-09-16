

### Installation

Steps to install the protocol for client-server communications.

1) Create a virtualenv enviroment and activate it.
```
virtualenv .venv
source .venv/bin/activate
```
2) Install the required packages
```
pip install -r scripts/requirements.txt
```
3) Create a self-signed certicate/key.
```
cd scripts/
bash ./protocol-setup.sh
```
