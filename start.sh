#!/bin/bash

# Start SSH daemon
/usr/sbin/sshd

# Start frontend server in background (serve built static files)
cd /app/frontend && npx serve -s dist -l 3000 &

# Switch back to app directory and start the Python backend
cd /app
python app/main.py