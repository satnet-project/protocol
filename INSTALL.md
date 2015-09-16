## Install server
```shell
git clone git@github.com:satnet-project/protocol.git
virtualenv .venv
source .venv/bin/activate
pip install -r scripts/requirements.txt
# The last step will create a self-signed certificate/key
/scripts/protocol-setup.sh
```