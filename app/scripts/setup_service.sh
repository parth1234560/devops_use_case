#!/bin/bash
set -e

cp /opt/aws-ha-app/aws-ha-app.service \
   /etc/systemd/system/aws-ha-app.service

mkdir -p /etc/aws-ha-app

cat > /etc/aws-ha-app/aws-ha-app.env <<'EOF'
PORT=8080
AWS_REGION=ap-south-1
DB_SECRET_ID=aws-ha-app/database
DB_INSTANCE_IDENTIFIER=aws-ha-app-mysql
LOG_FILE=/var/log/aws-ha-app.log
EOF

chmod 644 /etc/aws-ha-app/aws-ha-app.env

if [ -f /opt/aws-ha-app/requirements.txt ]; then
    python3 -m pip install -r /opt/aws-ha-app/requirements.txt
fi

chown -R awsapp:awsapp /opt/aws-ha-app

systemctl daemon-reload
