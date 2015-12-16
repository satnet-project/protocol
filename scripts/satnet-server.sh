#!/bin/bash
cd "/opt/satnet/server/"
source ".venv/bin/activate"
sudo chmod +x /opt/satnet/server/manage.py
python manage.py runserversgongarpass
