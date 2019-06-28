#!/bin/sh
cat - /tmp/crontab > /etc/crontabs/root
crond -f -l 2
