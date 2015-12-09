#!/bin/bash
cd "/opt/protocol/"
source ".venv/bin/activate"
sudo chmod +x /opt/protocol/server_amp.py
python /opt/protocol/server_amp.py