#!/bin/bash
set -e

cp /opt/aws-ha-app/aws-ha-app.service \
   /etc/systemd/system/aws-ha-app.service

mkdir -p /etc/aws-ha-app

cat > /etc/aws-ha-app/aws-ha-app.env <<'EOF'
PORT=8080
EOF

chmod 644 /etc/aws-ha-app/aws-ha-app.env

chown -R awsapp:awsapp /opt/aws-ha-app

systemctl daemon-reload