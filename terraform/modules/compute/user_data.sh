#!/bin/bash
set -euxo pipefail

# Install required packages and management agents
dnf install -y python3 ruby wget amazon-ssm-agent

# Start SSM Agent so private instances can be accessed through Session Manager.
systemctl enable --now amazon-ssm-agent

# Install CodeDeploy Agent
cd /tmp

wget https://aws-codedeploy-ap-south-1.s3.ap-south-1.amazonaws.com/latest/install

chmod +x install

./install auto

systemctl enable --now codedeploy-agent

# Create application directory
mkdir -p /opt/aws-ha-app

# Create application
cat > /opt/aws-ha-app/app.py <<'PY'
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = ${app_port}

class Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == "/health":
            body = b"OK\n"
        else:
            body = b"aws-ha-app\n"

        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass

server = HTTPServer(("0.0.0.0", PORT), Handler)
server.serve_forever()
PY

# Create systemd service
cat > /etc/systemd/system/aws-ha-app.service <<'EOF'
[Unit]
Description=AWS HA Demo Application
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/aws-ha-app/app.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Start application
systemctl daemon-reload
systemctl enable --now aws-ha-app
