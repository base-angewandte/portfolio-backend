#!/usr/bin/env bash

LOG_DIR=/logs
APPEND=$( date -d "yesterday 13:00 " '+%Y-%m-%d' )
ACCESS_LOG=${LOG_DIR}/gunicorn.access.log
ACCESS_LOG_ROTATED=${ACCESS_LOG}.${APPEND}
ERROR_LOG=${LOG_DIR}/gunicorn.error.log
ERROR_LOG_ROTATED=${ERROR_LOG}.${APPEND}

if [[ -s ${ACCESS_LOG} ]]; then
    mv ${ACCESS_LOG} ${ACCESS_LOG_ROTATED}
fi

if [[ -s ${ERROR_LOG} ]]; then
    mv ${ERROR_LOG} ${ERROR_LOG_ROTATED}
fi

if [[ -f ${ACCESS_LOG_ROTATED} ]] || [[ -f ${ERROR_LOG_ROTATED} ]]; then
    kill -USR1 `cat /var/run/gunicorn.pid`
    sleep 1
fi

if [[ -f ${ACCESS_LOG_ROTATED} ]]; then
    gzip ${ACCESS_LOG_ROTATED}
fi

if [[ -f ${ERROR_LOG_ROTATED} ]]; then
    gzip ${ERROR_LOG_ROTATED}
fi
