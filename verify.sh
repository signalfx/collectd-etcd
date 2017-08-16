#!/bin/bash
flake8 etcd_plugin.py test_etcd.py
if [ "$?" -ne 0 ]; then
    exit 1;
fi
py.test test_etcd.py
