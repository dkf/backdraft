#!/usr/bin/env python

import ctypes
import tornado.ioloop
import functools
import time
import sys
from xml.dom.minidom import parseString
from tornado.httpclient import AsyncHTTPClient
from USB import *

def initialize():
    usb_init()
    usb_find_busses()
    usb_find_devices()

def busses():
    bus = usb_get_busses()
    while bus:
        yield bus.contents
        bus = bus.contents.next

def devices():
    for bus in busses():
        device = bus.devices
        while device:
            yield device.contents
            device = device.contents.next

def controllable(device):
    if device.is_controllable_hub():
        return True
    return False

def main():
    initialize()
    devs = filter(controllable, devices())
    print "Found %s controllable hubs" % len(devs)
    # {url: (hub #, port #), ...}
    urls = {"http://chb1.kcprod.info:8080/hudson/job/kc-backend-chb2/rssAll": (0, 2),
            "http://chb1.kcprod.info:8080/hudson/job/Selenium%20Tests/rssAll": (0, 1)}
    if len(devs) > 0 or len(urls) > 0:
        monitor = AsyncMonitor(devs, urls)
        monitor.start()


class AsyncMonitor:
    def __init__(self, devs, urls):
        self.devices = devs
        self.urls = urls
        self.http_client = AsyncHTTPClient()
    def start(self):
        for (key, val) in self.urls.items():
            self.http_client.fetch(key, self.handle_response)
        self.io_loop = tornado.ioloop.IOLoop.instance()
        self.io_loop.start()
    def url_failed(self, url):
        (hub, port) = self.urls[url]
        print "Build failed: %s enabling hub %s, port %s" % (url, hub, port)
        self.devices[hub].power_on(port)
    def url_succeeded(self, url):
        print ".",
        sys.stdout.flush()
        (hub, port) = self.urls[url]
        self.devices[hub].power_off(port)
    def handle_response(self, res):
        if res.error:
            print "Error: ", res.error
        else:
            self.examine(res.body, res.request.url)
        self.io_loop.add_timeout(time.time() + 5, functools.partial(self.schedule, res.request.url))
    def schedule(self, url):
        self.http_client.fetch(url, self.handle_response)
    def examine(self, body, url):
        dom = parseString(body)
        if self.getText(dom.getElementsByTagName("title")[1].childNodes).find("SUCCESS") == -1:
            self.url_failed(url)
        else:
            self.url_succeeded(url)
        dom.unlink()
    def getText(self, nodes):
        r = ""
        for node in nodes:
            if node.nodeType == node.TEXT_NODE:
                r = r + node.data
        return r

if __name__ == "__main__":
    main()
