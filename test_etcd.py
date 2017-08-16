#!/usr/bin/env python
import collections
import mock
import sys
import pytest
import sample_responses


class MockCollectd(mock.MagicMock):
    """
    Mocks the functions and objects provided by the collectd module
    """

    @staticmethod
    def log(log_str):
        print log_str

    debug = log
    info = log
    warning = log
    error = log


def mock_api_call(data, url):
    parsed_url = url.split('/')
    # one of the endpoints that the plugin needs
    return getattr(sample_responses, parsed_url[-1])


sys.modules['collectd'] = MockCollectd()

import etcd_plugin

ConfigOption = collections.namedtuple('ConfigOption', ('key', 'values'))

fail_mock_config_required_params = mock.Mock()
fail_mock_config_required_params.children = [
    ConfigOption('Host', ('localhost',)),
    ConfigOption('Testing', ('True',))
]


def test_config_fail():
    with pytest.raises(KeyError):
        etcd_plugin.read_config(fail_mock_config_required_params)


mock_config_enhanced_metrics_on = mock.Mock()
mock_config_enhanced_metrics_on.children = [
    ConfigOption('Host', ('localhost',)),
    ConfigOption('Port', ('2379',)),
    ConfigOption('Interval', ('10',)),
    ConfigOption('Cluster', ('MocketcdCluster',)),
    ConfigOption('EnhancedMetrics', ('tRue',)),
    ConfigOption('ExcludeMetric', ('etcd_debugging_mvcc_slow_watcher_total',)),
    ConfigOption('Testing', ('True',))
]


mock_config_enhanced_metrics_off = mock.Mock()
mock_config_enhanced_metrics_off.children = [
    ConfigOption('Host', ('localhost',)),
    ConfigOption('Port', ('22379',)),
    ConfigOption('Interval', ('10',)),
    ConfigOption('Cluster', ('MocketcdCluster',)),
    ConfigOption('IncludeMetric', ('etcd_debugging_mvcc_slow_watcher_total',)),
    ConfigOption('Testing', ('True',))
]


@mock.patch('etcd_plugin.get_text', mock_api_call)
def test_optional_metrics_on():
    etcd_plugin.read_metrics(
        etcd_plugin.read_config(
            mock_config_enhanced_metrics_off))


@mock.patch('etcd_plugin.get_text', mock_api_call)
def test_optional_metrics_off():
    etcd_plugin.read_metrics(
        etcd_plugin.read_config(
            mock_config_enhanced_metrics_on))


mock_config = mock.Mock()
mock_config.children = [
    ConfigOption('Host', ('localhost',)),
    ConfigOption('Port', ('2379',)),
    ConfigOption('Interval', ('10',)),
    ConfigOption('Cluster', ('MocketcdCluster',)),
    ConfigOption('Testing', ('True',))
]


def test_default_config():
    module_config = etcd_plugin.read_config(mock_config)
    assert module_config['plugin_conf']['Host'] == 'localhost'
    assert module_config['plugin_conf']['Port'] == '2379'
    assert module_config['interval'] == '10'
    assert module_config['base_url'] == 'http://localhost:2379'
    assert module_config['cluster'] == 'MocketcdCluster'


mock_config_ssl = mock.Mock()
mock_config_ssl.children = [
    ConfigOption('Host', ('localhost',)),
    ConfigOption('Port', ('2379',)),
    ConfigOption('Interval', ('10',)),
    ConfigOption('Cluster', ('MocketcdCluster',)),
    ConfigOption('ssl_keyfile', ('ssl_keyfile',)),
    ConfigOption('ssl_certificate', ('ssl_certificate',)),
    ConfigOption('ssl_ca_certs', ('ssl_ca_certs',)),
    ConfigOption('Testing', ('True',))
]


def test_with_ssl_config():
    module_config = etcd_plugin.read_config(mock_config_ssl)
    assert module_config['plugin_conf']['Host'] == 'localhost'
    assert module_config['plugin_conf']['Port'] == '2379'
    assert module_config['interval'] == '10'
    assert module_config['ssl_keys']['ssl_keyfile'] == 'ssl_keyfile'
    assert module_config['ssl_keys']['ssl_certificate'] == 'ssl_certificate'
    assert module_config['ssl_keys']['ssl_ca_certs'] == 'ssl_ca_certs'
    assert module_config['base_url'] == 'https://localhost:2379'
    assert module_config['cluster'] == 'MocketcdCluster'


mock_config_check_bool = mock.Mock()
mock_config_check_bool.children = [
    ConfigOption('Host', ('localhost',)),
    ConfigOption('Port', ('2379',)),
    ConfigOption('Interval', ('10',)),
    ConfigOption('Cluster', ('MocketcdCluster',)),
    ConfigOption('ssl_keyfile', ('ssl_keyfile',)),
    ConfigOption('ssl_certificate', ('ssl_certificate',)),
    ConfigOption('ssl_ca_certs', ('ssl_ca_certs',)),
    ConfigOption('EnhancedMetrics', ('xyz',)),
    ConfigOption('Testing', ('True',))
]


def test_boolean_config():
    module_config = etcd_plugin.read_config(mock_config_check_bool)
    assert module_config['plugin_conf']['Host'] == 'localhost'
    assert module_config['plugin_conf']['Port'] == '2379'
    assert module_config['interval'] == '10'
    assert module_config['ssl_keys']['ssl_keyfile'] == 'ssl_keyfile'
    assert module_config['ssl_keys']['ssl_certificate'] == 'ssl_certificate'
    assert module_config['ssl_keys']['ssl_ca_certs'] == 'ssl_ca_certs'
    assert module_config['base_url'] == 'https://localhost:2379'
    assert module_config['cluster'] == 'MocketcdCluster'
    assert module_config['enhanced_metrics'] == False


@mock.patch('etcd_plugin.get_json', mock_api_call)
def test_read():
    etcd_plugin.read_metrics(etcd_plugin.read_config(mock_config))
