#!/bin/bash
set -e

systemctl daemon-reload
systemctl enable aws-ha-app
systemctl restart aws-ha-app