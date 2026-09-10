#!/bin/bash
set -e

systemctl is-active --quiet aws-ha-app

curl -f http://localhost:8080/health

echo "Application validation successful"