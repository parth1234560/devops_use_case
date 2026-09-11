#!/bin/bash
set -e

systemctl is-active --quiet aws-ha-app

for attempt in $(seq 1 30); do
    if curl -fsS http://localhost:8080/health; then
        echo "Application validation successful"
        exit 0
    fi

    echo "Waiting for application health check (${attempt}/30)"
    sleep 2
done

echo "Application failed health validation"
systemctl status aws-ha-app --no-pager || true
tail -n 100 /var/log/aws-ha-app.log || true
exit 1
