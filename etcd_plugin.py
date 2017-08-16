#!/usr/bin/env python
import urllib2
import urllib_ssl_handler
import json
import collections
import collectd
import six


LEADER = "StateLeader"
FOLLOWER = "StateFollower"
DEFAULT_INTERVAL = 10
DEFAULT_API_TIMEOUT = 60
PLUGIN_NAME = "etcd"

Metric = collections.namedtuple('Metric', ('name', 'type'))


SELF_METRICS = {
    'recvAppendRequestCnt':
        Metric('etcd.self.recvappendreq.cnt', 'counter'),
    'sendAppendRequestCnt':
        Metric('etcd.self.sendappendreq.cnt', 'counter'),
    'recvPkgRate':
        Metric('etcd.self.recvpkg.rate', 'gauge'),
    'recvBandwidthRate':
        Metric('etcd.self.recvbandwidth.rate', 'gauge'),
    'sendPkgRate':
        Metric('etcd.self.sendpkg.rate', 'gauge'),
    'sendBandwidthRate':
        Metric('etcd.self.sendbandwidth.rate', 'gauge')
}


STORE_METRICS_LEADER = {
    'compareAndDeleteFail':
        Metric('etcd.store.compareanddelete.fail', 'counter'),
    'compareAndDeleteSuccess':
        Metric('etcd.store.compareanddelete.success', 'counter'),
    'compareAndSwapFail':
        Metric('etcd.store.compareandswap.fail', 'counter'),
    'compareAndSwapSuccess':
        Metric('etcd.store.compareandswap.success', 'counter'),
    'createFail':
        Metric('etcd.store.create.fail', 'counter'),
    'createSuccess':
        Metric('etcd.store.create.success', 'counter'),
    'deleteFail':
        Metric('etcd.store.delete.fail', 'counter'),
    'deleteSuccess':
        Metric('etcd.store.delete.success', 'counter'),
    'updateFail':
        Metric('etcd.store.update.fail', 'counter'),
    'updateSuccess':
        Metric('etcd.store.update.success', 'counter'),
    'setsFail':
        Metric('etcd.store.sets.fail', 'counter'),
    'setsSuccess':
        Metric('etcd.store.sets.success', 'counter')
}


STORE_METRICS = {
    'getsFail':
        Metric('etcd.store.gets.fail', 'counter'),
    'getsSuccess':
        Metric('etcd.store.gets.success', 'counter'),
    'watchers':
        Metric('etcd.store.watchers', 'gauge'),
    'expireCount':
        Metric('etcd.store.expire.count', 'counter')
}


LEADER_METRICS_COUNTS = {
    'fail':
        Metric('etcd.leader.counts.fail', 'counter'),
    'success':
        Metric('etcd.leader.counts.success', 'counter')
}


LEADER_METRICS_LATENCY = {
    'average':
        Metric('etcd.leader.latency.average', 'gauge'),
    'current':
        Metric('etcd.leader.latency.current', 'gauge'),
    'maximum':
        Metric('etcd.leader.latency.max', 'gauge'),
    'minimum':
        Metric('etcd.leader.latency.min', 'gauge'),
    'standardDeviation':
        Metric('etcd.leader.latency.stddev', 'gauge')
}


def read_config(conf):
    '''
    Reads the configurations provided by the user
    '''
    plugin_conf = {}
    cluster = 'default'
    interval = DEFAULT_INTERVAL
    custom_dimensions = {}
    enhanced_metrics = False
    exclude_optional_metrics = set()
    include_optional_metrics = set()
    http_timeout = DEFAULT_API_TIMEOUT

    required_keys = frozenset(('Host', 'Port'))
    ssl_keys = {}
    testing = False

    for val in conf.children:
        if val.key in required_keys:
            plugin_conf[val.key] = val.values[0]
        elif val.key == 'Interval' and val.values[0]:
            interval = val.values[0]
        elif val.key == 'Cluster' and val.values[0]:
            cluster = val.values[0]
        elif val.key == 'Dimension':
            if len(val.values) == 2:
                custom_dimensions.update({val.values[0]: val.values[1]})
            else:
                collectd.warning("WARNING: Check configuration \
                                            setting for %s" % val.key)
        elif val.key == 'EnhancedMetrics' and val.values[0]:
            enhanced_metrics = str_to_bool(val.values[0])
        elif val.key == 'IncludeMetric' and val.values[0]:
            include_optional_metrics.add(val.values[0])
        elif val.key == 'ExcludeMetric' and val.values[0]:
            exclude_optional_metrics.add(val.values[0])
        elif val.key == 'ssl_keyfile' and val.values[0]:
            ssl_keys['ssl_keyfile'] = val.values[0]
        elif val.key == 'ssl_certificate' and val.values[0]:
            ssl_keys['ssl_certificate'] = val.values[0]
        elif val.key == 'ssl_ca_certs' and val.values[0]:
            ssl_keys['ssl_ca_certs'] = val.values[0]
        elif val.key == 'Testing' and str_to_bool(val.values[0]):
            testing = True

    collectd.debug("Configuration settings:")

    for key in required_keys:
        try:
            val = plugin_conf[key]
            collectd.debug("%s : %s" % (key, val))
        except KeyError:
            raise KeyError("Missing required config setting: %s" % key)

    base_url = ("http://%s:%s" % (plugin_conf['Host'], plugin_conf['Port']))
    if 'ssl_certificate' in ssl_keys and 'ssl_keyfile' in ssl_keys:
        base_url = ('https'+base_url[4:])

    module_config = {
            'state': None,
            'member_id': ("%s:%s" % (
                plugin_conf['Host'], plugin_conf['Port'])),
            'plugin_conf': plugin_conf,
            'cluster': cluster,
            'interval': interval,
            'ssl_keys': ssl_keys,
            'base_url': base_url,
            'http_timeout': http_timeout,
            'custom_dimensions': custom_dimensions,
            'enhanced_metrics': enhanced_metrics,
            'include_optional_metrics': include_optional_metrics,
            'exclude_optional_metrics': exclude_optional_metrics,
            'Testing': testing
            }

    collectd.debug("module_config: (%s)" % str(module_config))
    # print module_config
    if testing:
        return module_config

    collectd.register_read(
                            read_metrics,
                            interval,
                            data=module_config,
                            name=module_config['member_id']
    )


def str_to_bool(flag):
    '''
    Converts true/false to boolean
    '''
    flag = str(flag).strip().lower()
    if flag == 'true':
        return True
    elif flag != 'false':
        collectd.warning("WARNING: REQUIRES BOOLEAN. \
                RECEIVED %s. ASSUMING FALSE." % (str(flag)))

    return False


def read_metrics(data):
    '''
    Registered read call back function that collects
    metrics from all endpoints
    '''
    collectd.debug("STARTED FETCHING METRICS")
    map_id_to_url(data, 'members')
    get_self_metrics(data, 'self')
    get_store_metrics(data, 'store')
    if data['state'] == LEADER:
        get_leader_metrics(data, 'leader')
    # get optional metrics
    if data['enhanced_metrics'] or len(data['include_optional_metrics']) > 0:
        get_optional_metrics(data, 'metrics')


def map_id_to_url(data, endpoint):
    '''
    etcd uses interval id for each member. This method
    maps the id to corresponding base url
    '''
    # collectd.debug("DEBUGGING: %s" % data)
    url = ("%s/v2/%s" % (data['base_url'], endpoint))
    response = get_json(data, url)

    if response:
        for member in response[endpoint]:
            data[member['id']] = str(member['clientURLs'][0])


def get_self_metrics(data, endpoint):
    '''
    Fetches metrics from the /self endpoint
    '''
    collectd.debug("METRICS FROM %s ENDPOINT" % endpoint)
    response = prepare_url(data, endpoint)

    if response:
        data['state'] = LEADER if LEADER == response['state'] else FOLLOWER
        default_dimensions = {
                'state': data['state'],
                'cluster': data['cluster']
        }
        plugin_instance = prepare_plugin_instance(data, default_dimensions)

        for key in SELF_METRICS:
            if key in response:
                prepare_and_dispatch_metric(
                        SELF_METRICS[key].name,
                        response[key],
                        SELF_METRICS[key].type,
                        plugin_instance
                )
            else:
                prepare_and_dispatch_metric(
                    SELF_METRICS[key].name,
                    0,
                    SELF_METRICS[key].type,
                    plugin_instance
                )


def get_store_metrics(data, endpoint):
    '''
    Fetches metrics from the /store endpoint
    '''
    collectd.debug("METRICS FROM %s ENDPOINT" % endpoint)
    response = prepare_url(data, endpoint)

    if response:
        default_dimensions = {
                'state': data['state'],
                'cluster': data['cluster']
        }
        plugin_instance = prepare_plugin_instance(data, default_dimensions)

        for key in STORE_METRICS:
            if key in response:
                prepare_and_dispatch_metric(
                    STORE_METRICS[key].name,
                    response[key],
                    STORE_METRICS[key].type,
                    plugin_instance
                )

        # Only leader reports operations on the
        # store are global to all the members
        if data['state'] == LEADER:
            for key in STORE_METRICS_LEADER:
                if key in response:
                    prepare_and_dispatch_metric(
                        STORE_METRICS_LEADER[key].name,
                        response[key],
                        STORE_METRICS_LEADER[key].type,
                        plugin_instance
                    )


def get_leader_metrics(data, endpoint):
    '''
    Fetches metrics from the /leader endpoint
    '''
    collectd.debug("METRICS FROM %s ENDPOINT" % endpoint)
    response = prepare_url(data, endpoint)

    if response:
        for follower, value in six.iteritems(response.get('followers', {})):
            default_dimensions = {
                    'state': data['state'],
                    'follower': data[follower][7:],
                    'cluster': data['cluster']
            }
            plugin_instance = prepare_plugin_instance(data, default_dimensions)

            for key in LEADER_METRICS_COUNTS:
                if key in value['counts']:
                    prepare_and_dispatch_metric(
                        LEADER_METRICS_COUNTS[key].name,
                        value['counts'][key],
                        LEADER_METRICS_COUNTS[key].type,
                        plugin_instance
                    )

            for key in LEADER_METRICS_LATENCY:
                if key in value['latency']:
                    prepare_and_dispatch_metric(
                        LEADER_METRICS_LATENCY[key].name,
                        value['latency'][key],
                        LEADER_METRICS_LATENCY[key].type,
                        plugin_instance
                    )


def get_optional_metrics(data, endpoint):
    '''
    Fetches optional metrics from /metrics endpoint
    '''
    collectd.debug("METRICS FROM %s ENDPOINT" % endpoint)
    url = ("%s/%s" % (data['base_url'], endpoint))
    response = get_text(data, url)

    if response:
        metrics = {}
        transform_text_to_metrics(response, metrics)
        default_dimensions = {
                'state': data['state'],
                'cluster': data['cluster']
        }
        # if the bool is true, then exclude metrics that are not required
        if data['enhanced_metrics']:
            for metric in metrics:
                if metric in data['exclude_optional_metrics']:
                    continue
                plugin_instance = prepare_plugin_instance(
                    data,
                    default_dimensions,
                    ('%s%s' % (',', metrics[metric].get('dimensions', {}))))
                prepare_and_dispatch_metric(
                    metrics[metric]['name'],
                    metrics[metric]['value'],
                    metrics[metric]['type'],
                    plugin_instance
                )
        else:
            # include only the required metrics
            for metric in data['include_optional_metrics']:
                if metric in metrics:
                    plugin_instance = prepare_plugin_instance(
                        data,
                        default_dimensions,
                        ('%s%s' % (',', metrics[metric].get(
                                        'dimensions',
                                        {}))))
                    prepare_and_dispatch_metric(
                        metrics[metric]['name'],
                        metrics[metric]['value'],
                        metrics[metric]['type'],
                        plugin_instance
                    )


def transform_text_to_metrics(response, metrics):
    '''
    Transforms optional text from /metrics endpoint to metrics format
    '''
    for line in response.splitlines():
        formatted = line.split(' ')
        if len(formatted) == 1:  # When SSL fails
            break
        if formatted[1] == 'TYPE'\
                and formatted[3] not in ('histogram', 'summary'):
            metric = {
                'name': str(formatted[2]).replace('_', '.'),
                'type': str(formatted[3])
                }
            metrics[formatted[2]] = metric
            continue
        if len(formatted) == 2:
            name_and_dimensions = str(formatted[0]).split('{')
            name = formatted[0]
            dimensions = ''
            if len(name_and_dimensions) > 1:
                name = name_and_dimensions[0]
                dimensions = \
                    name_and_dimensions[1].replace('}', '').replace('\"', '')
            if name in metrics:
                metrics[name].update({
                    'value': float(str(formatted[1])),
                    'dimensions': dimensions
                    })


def prepare_plugin_instance(data, default_dimensions, more_dimensions=''):
    '''
    Prepares the plugin instance string to be passed to collectd
    '''
    # add custom dimensions to the list of dimensions
    default_dimensions.update(data['custom_dimensions'])
    default_dimensions = format_dimensions(
        default_dimensions,
        (more_dimensions)
        )
    return ("%s%s" % (data['member_id'], default_dimensions))


def prepare_url(data, endpoint):
    '''
    Returns json
    '''
    url = ("%s/v2/stats/%s" % (data['base_url'], endpoint))
    return get_json(data, url)


def get_json(data, url):
    '''
    Makes the API call and prepares the json to be returned
    '''
    response = make_api_call(data, url)
    try:
        if response:
            return json.load(response)
    except ValueError, e:
        collectd.error("ERROR: JSON parsing failed: (%s) %s" % (e, url))
        return


def get_text(data, url):
    '''
    Makes the API call and returns the text (for optional metrics)
    '''
    response = make_api_call(data, url)
    if response:
        return response.read()


def make_api_call(data, url):
    collectd.debug("GETTING THIS  URL %s" % url)
    try:
        key_file, cert_file, ca_certs = get_ssl_params(data)
        opener = urllib2.build_opener(urllib_ssl_handler.HTTPSHandler(
            key_file=key_file, cert_file=cert_file, ca_certs=ca_certs))

        response = opener.open(url)
        return response
    except (urllib2.HTTPError, urllib2.URLError), e:
        collectd.error("ERROR: API call failed: (%s) %s" % (e, url))


def get_ssl_params(data):
    '''
    Helper method to prepare auth tuple
    '''
    key_file = None
    cert_file = None
    ca_certs = None

    ssl_keys = data['ssl_keys']
    if 'ssl_certificate' in ssl_keys and 'ssl_keyfile' in ssl_keys:
        key_file = ssl_keys['ssl_keyfile']
        cert_file = ssl_keys['ssl_certificate']

    if 'ssl_ca_certs' in ssl_keys:
        ca_certs = ssl_keys['ssl_ca_certs']

    return (key_file, cert_file, ca_certs)


def prepare_and_dispatch_metric(name, value, _type, dimensions):
    '''
    Prepares and dispatches a metric
    '''
    data_point = collectd.Values(plugin=PLUGIN_NAME)
    data_point.type_instance = name
    data_point.type = _type
    data_point.values = [value]
    data_point.plugin_instance = dimensions

    # With some versions of CollectD, a dummy metadata map must to be added
    # to each value for it to be correctly serialized to JSON by the
    # write_http plugin. See
    # https://github.com/collectd/collectd/issues/716
    data_point.meta = {'true': 'true'}

    data_point.dispatch()
    collectd.debug("DISPATCHED: %s" % prepare_and_print_metric(
                    name,
                    value,
                    _type,
                    dimensions))


def prepare_and_print_metric(name, value, _type, dimensions):
    '''
    Prints out metrics in string format
    '''
    out = ("{ name : %s, value : %s, type : %s, dimension : %s}" % (
                name,
                value,
                _type,
                dimensions))
    return out


def format_dimensions(dimensions, more_dimensions=''):
    '''
    Formats dimensions before fed to collectd plugin instance
    '''
    formatted = []
    formatted.extend(("%s=%s" % (k, v)) for k, v in six.iteritems(dimensions))
    return ('[%s%s]' % (str(formatted).replace('\'', '').
            replace(' ', '').replace("\"", '').replace('[', '').
                replace(']', ''),
                '' if len(more_dimensions) == 1 else more_dimensions))


if __name__ == "__main__":
    # run standalone
    pass
else:
    collectd.register_config(read_config)
