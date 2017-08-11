#!/bin/bash
flake8 etcd_plugin.py test_etcd.py
py.test test_etcd.py
