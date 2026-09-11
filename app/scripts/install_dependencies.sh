#!/bin/bash
set -e

dnf install -y python3 python3-pip

if ! id awsapp >/dev/null 2>&1; then
    useradd --system --create-home --shell /sbin/nologin awsapp
fi

mkdir -p /opt/aws-ha-app
mkdir -p /etc/aws-ha-app

touch /var/log/aws-ha-app.log

chown -R awsapp:awsapp /opt/aws-ha-app
chown awsapp:awsapp /var/log/aws-ha-app.log

chmod 755 /opt/aws-ha-app
