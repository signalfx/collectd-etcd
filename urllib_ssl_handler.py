#!/usr/bin/env python
import sys
import socket
import ssl
from six.moves import http_client
from six.moves import urllib


class CertificateError(ValueError):
    pass


class HTTPSConnection(http_client.HTTPSConnection):
    def __init__(self, host, **kwargs):
        self.ca_certs = kwargs.pop('ca_certs', None)
        self.checker = kwargs.pop('checker', ssl.match_hostname)

        http_client.HTTPSConnection.__init__(self, host, **kwargs)

    def connect(self):
        '''
        override default version to do cert verification
        '''
        args = [(self.host, self.port), self.timeout,]
        if hasattr(self, 'source_address'):
            args.append(self.source_address)
        sock = socket.create_connection(*args)

        if getattr(self, '_tunnel_host', None):
            self.sock = sock
            self._tunnel()

        kwargs = {}
        if self.ca_certs is not None:
            kwargs.update(
                cert_reqs=ssl.CERT_REQUIRED,
                ca_certs=self.ca_certs
                )
        self.sock = ssl.wrap_socket(sock,
                                    keyfile=self.key_file,
                                    certfile=self.cert_file,
                                    **kwargs)
        if self.checker is not None:
            try:
                self.checker(self.sock.getpeercert(), self.host)
            except CertificateError:
                self.sock.shutdown(socket.SHUT_RDWR)
                self.sock.close()
                raise CertificateError("Certificate Error")


class HTTPSHandler(urllib.request.HTTPSHandler):
    def __init__(self, key_file=None, cert_file=None, ca_certs=None,
                 checker=ssl.match_hostname):
        urllib.request.HTTPSHandler.__init__(self)
        self.key_file = key_file
        self.cert_file = cert_file
        self.ca_certs = ca_certs
        self.checker = checker

    def https_open(self, req):
        return self.do_open(self.getConnection, req)

    def getConnection(self, host, **kwargs):
        d = dict(cert_file=self.cert_file,
                 key_file=self.key_file,
                 ca_certs=self.ca_certs,
                 checker=self.checker)
        d.update(kwargs)
        return HTTPSConnection(host, **d)
