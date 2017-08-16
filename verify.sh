#!/bin/bash
flake8 etcd_plugin.py urllib_ssl_handler.py
if [ "$?" -ne 0 ]; then
    exit 1;
fi
py.test test_etcd.py
