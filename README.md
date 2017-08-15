# collectd etcd Plugin

An etcd [collectd](http://www.collectd.org/) plugin which users can use to send metrics from etcd instances to SignalFx

## Installation

* Checkout this repository somewhere on your system accessible by collectd. The suggested location is `/usr/share/collectd/`
* Install the Python requirements with sudo ```pip install -r requirements.txt```
* Configure the plugin (see below)
* Restart collectd

## Requirements

* collectd 4.9 or later (for the Python plugin)
* Python 2.6 or later
* etcd 2.0.8 or later

## Configuration
The following are required configuration keys:

* Host - Required. Hostname or IP address of the etcd member, default is 'localhost'
* Port - Required. The port of the etcd member, default is '2379'

Optional configurations keys include:

* Interval - Interval between metric calls. Default is 10s
* Cluster - The cluster to which the member belongs. By default, this is set to "default"
* EnhancedMetrics - Flag to specify whether stats from the `/metrics` endpoint are needed. Default is False
* IncludeMetric - Metrics from the `/metrics` endpoint can be included individually
* ExcludeMetric - Metrics from the `/metrics` endpoint can be excluded individually
* Dimension - Add extra dimensions to your metrics

Specify path to keyfile and certificate if certificate based authentication of clients is enabled on your etcd server
* ssl_keyfile - path to file
* ssl_certificate - path to file

Provide a custom file that lists trusted CA certificates, required when keyfile and certificate are provided
* ssl_ca_certs - path to file

Note that multiple etcd members can be configured in the same file.

```
LoadPlugin python
<Plugin python>
  ModulePath "/usr/share/collectd/collectd-etcd"

  Import etcd_plugin
  <Module etcd_plugin>
    Host "localhost"
    Port "22379"
    Cluster "dev"
    Interval 10
    EnhancedMetrics False
    IncludeMetric "etcd_debugging_mvcc_slow_watcher_total"
    IncludeMetric "etcd_debugging_store_reads_total"
    IncludeMetric "etcd_server_has_leader"
  </Module>
  <Module etcd_plugin>
    Host "localhost"
    Port "2379"
    Cluster "dev"
    Interval 10
    EnhancedMetrics True
    ExcludeMetric "etcd_debugging_mvcc_slow_watcher_total"
    ExcludeMetric "etcd_server_has_leader"
    Dimension foo bar
  </Module>
</Plugin>
```
