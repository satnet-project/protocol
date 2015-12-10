#!/bin/bash
cd "/opt/satnet/protocol/"
source ".venv/bin/activate"
sudo chmod +x /opt/satnet/protocol/server_amp.py
python /opt/satnet/protocol/server_amp.py