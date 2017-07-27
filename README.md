# Collectd etcd Plugin

## Introduction
An etcd [Collectd](http://www.collectd.org/) plugin which users can use to send metrics from etcd instances to SignalFx

## Configuration
The following are required configuration keys:

* Host - Required. Hostname or IP address of the etcd member, default is 'localhost'
* Port - Required. The port of the etcd member, default is '2379'
* Cluster - Required. The cluster to which the member

Optional configurations keys include:

* Interval - Interval between metric calls. Default is 10s
* EnhancedMetrics - Flag to specify whether stats from the ```/metrics``` endpoint are needed. Default is False
* IncludeMetric - Metrics from the ```/metrics``` endpoint can be included individually
* ExcludeMetric - Metrics from the ```/metrics``` endpoint can be excluded individually
* Dimension - Add extra dimensions to your metrics

Specify path to keyfile and certificate if certificate based authentication of clients is enabled on your etcd server
* ssl_keyfile - path to file
* ssl_certificate - path to file

Validation of the server's SSL certificates
* ssl_cert_validation - True/False

Provide a custom file that lists trusted CA certificates, if ssl_cert_validation is enabled
* ssl_ca_certs - path to file
```
LoadPlugin python
<Plugin python>
  ModulePath "/opt/collectd-etcd"

  Import etcd_plugin
  <Module etcd_plugin>
    Host "localhost"
    Port "22379"
    Cluster 1
    Interval 10
    EnhancedMetrics False
    IncludeMetric "etcd_debugging_mvcc_slow_watcher_total"
    IncludeMetric "etcd_debugging_store_reads_total"
    IncludeMetric "etcd_server_has_leader"
  </Module>
  <Module etcd_plugin>
    Host "localhost"
    Port "2379"
    Cluster 1
    Interval 10
    EnhancedMetrics True
    ExcludeMetric "etcd_debugging_mvcc_slow_watcher_total"
    ExcludeMetric "etcd_server_has_leader"
    Dimension foo bar
  </Module>
</Plugin>
```
