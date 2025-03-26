import logging as log
import snappi
from datetime import datetime
import time

   
def Test_otg_flows(controller):
    # TODO: add support for BGP for IPv6 as well
    test_const = {
        "pktRate": 200,
        "pktCount": 1000,
        "pktSize": 128,
        "trafficDuration": 20,
        "txMac": "00:00:01:01:01:01",
        "txIp": "192.168.11.100",
        "txGateway": "192.168.11.1",
        "txPrefix": 24,
        "rxMac": "00:00:01:01:01:02",
        "rxIp": "192.168.12.100",
        "rxGateway": "192.168.12.1",
        "rxPrefix": 24,
    }

    api = snappi.api(location="https://"+controller+":8443", verify=False)

    c = otg_flow_config(api, test_const, controller)

    api.set_config(c)

    start_protocols(api)

    # start_capture(api)

    start_transmit(api)

    wait_for(lambda: flow_metrics_ok(api, test_const), "flow metrics",2,90)

    # stop_capture(api)

    # get_capture(api, "prx", "prx.pcap")
    # get_capture(api, "ptx", "ptx.pcap")


def otg_flow_config(api, tc, controller):
    c = api.config()
    ptx = c.ports.add(name="ptx", location=controller+":5555;1+"+controller+":50071;ens4")
    prx = c.ports.add(name="prx", location=controller+":5555;2+"+controller+":50071;ens5")
    
    # capture configuration

    rx_capture = c.captures.add(name="prx_capture")
    rx_capture.set(port_names=["prx"],format="pcap",overwrite=True)
    
    tx_capture = c.captures.add(name="ptx_capture")
    tx_capture.set(port_names=["ptx"],format="pcap",overwrite=True)

    dtx = c.devices.add(name="dtx")
    drx = c.devices.add(name="drx")

    dtx_eth = dtx.ethernets.add(name="dtx_eth")
    dtx_eth.connection.port_name = ptx.name
    dtx_eth.mac = tc["txMac"]
    dtx_eth.mtu = 1500

    dtx_ip = dtx_eth.ipv4_addresses.add(name="dtx_ip")
    dtx_ip.set(address=tc["txIp"], gateway=tc["txGateway"], prefix=tc["txPrefix"])


    drx_eth = drx.ethernets.add(name="drx_eth")
    drx_eth.connection.port_name = prx.name
    drx_eth.mac = tc["rxMac"]
    drx_eth.mtu = 1500

    drx_ip = drx_eth.ipv4_addresses.add(name="drx_ip")
    drx_ip.set(address=tc["rxIp"], gateway=tc["rxGateway"], prefix=tc["rxPrefix"])


    for i in range(0, 2):
        f = c.flows.add()
        f.duration.fixed_packets.packets = tc["pktCount"]
        f.rate.pps = tc["pktRate"]
        f.size.fixed = tc["pktSize"]
        f.metrics.enable = True

    ftx_v4 = c.flows[0]
    ftx_v4.name = "ftx_v4"
    ftx_v4.tx_rx.device.set(
        tx_names=[dtx_ip.name], rx_names=[drx_ip.name]
    )

    ftx_v4_eth, ftx_v4_ip, ftx_v4_udp = ftx_v4.packet.ethernet().ipv4().udp()
    ftx_v4_eth.src.value = dtx_eth.mac
    ftx_v4_ip.src.value = tc["txIp"]
    ftx_v4_ip.dst.value = tc["rxIp"]
    ftx_v4_udp.src_port.value = 5000
    ftx_v4_udp.dst_port.value = 6000

    frx_v4 = c.flows[1]
    frx_v4.name = "frx_v4"
    frx_v4.tx_rx.device.set(
        tx_names=[drx_ip.name], rx_names=[dtx_ip.name]
    )

    frx_v4_eth, frx_v4_ip, frx_v4_udp = frx_v4.packet.ethernet().ipv4().udp()
    frx_v4_eth.src.value = drx_eth.mac
    frx_v4_ip.src.value = tc["rxIp"]
    frx_v4_ip.dst.value = tc["txIp"]
    frx_v4_udp.src_port.value = 5000
    frx_v4_udp.dst_port.value = 6000

    # print("Config:\n%s", c)
    return c


def flow_metrics_ok(api, tc):
    for m in get_flow_metrics(api):
        if (
            m.transmit != m.STOPPED
            or m.frames_tx != tc["pktCount"]
            or m.frames_rx != tc["pktCount"]
        ):
            return False
    return True


def get_flow_metrics(api):

    print("%s Getting flow metrics    ..." % datetime.now())
    req = api.metrics_request()
    req.flow.flow_names = []

    metrics = api.get_metrics(req).flow_metrics

    tb = Table(
        "Flow Metrics",
        [
            "Name",
            "State",
            "Frames Tx",
            "Frames Rx",
            "FPS Tx",
            "FPS Rx",
            "Bytes Tx",
            "Bytes Rx",
        ],
    )

    for m in metrics:
        tb.append_row(
            [
                m.name,
                m.transmit,
                m.frames_tx,
                m.frames_rx,
                m.frames_tx_rate,
                m.frames_rx_rate,
                m.bytes_tx,
                m.bytes_rx,
            ]
        )
    print(tb)
    return metrics

def start_protocols(api):
    print("%s Starting protocols    ..." % datetime.now())
    cs = api.control_state()
    cs.choice = cs.PROTOCOL
    cs.protocol.choice = cs.protocol.ALL
    cs.protocol.all.state = cs.protocol.all.START
    api.set_control_state(cs)

def start_transmit(api):
    print("%s Starting transmit on all flows    ..." % datetime.now())
    cs = api.control_state()
    cs.choice = cs.TRAFFIC
    cs.traffic.choice = cs.traffic.FLOW_TRANSMIT
    cs.traffic.flow_transmit.state = cs.traffic.flow_transmit.START
    api.set_control_state(cs)

def stop_transmit(api):
    print("%s Stopping transmit    ..." % datetime.now())
    cs = api.control_state()
    cs.choice = cs.TRAFFIC
    cs.traffic.choice = cs.traffic.FLOW_TRANSMIT
    cs.traffic.flow_transmit.state = cs.traffic.flow_transmit.STOP
    api.set_control_state(cs)

def start_capture(api):
    print("%s Starting capture  ..." % datetime.now())
    cs = api.control_state()
    cs.choice = cs.PORT
    cs.port.choice = cs.port.CAPTURE
    cs.port.capture.set(port_names = [], state="start")
    api.set_control_state(cs)

def stop_capture(api):
    print("%s Stopping capture  ..." % datetime.now())
    cs = api.control_state()
    cs.choice = cs.PORT
    cs.port.choice = cs.port.CAPTURE
    cs.port.capture.set(port_names = [], state="stop")
    api.set_control_state(cs)

def get_capture(api,port_name,file_name):
    print('Fetching capture from port %s' % port_name)
    capture_req = api.capture_request()
    capture_req.port_name = port_name
    pcap = api.get_capture(capture_req)
    with open(file_name, 'wb') as out:
        out.write(pcap.read())

def wait_for(func, condition_str, interval_seconds=None, timeout_seconds=None):
    """
    Keeps calling the `func` until it returns true or `timeout_seconds` occurs
    every `interval_seconds`. `condition_str` should be a constant string
    implying the actual condition being tested.

    Usage
    -----
    If we wanted to poll for current seconds to be divisible by `n`, we would
    implement something similar to following:
    ```
    import time
    def wait_for_seconds(n, **kwargs):
        condition_str = 'seconds to be divisible by %d' % n

        def condition_satisfied():
            return int(time.time()) % n == 0

        poll_until(condition_satisfied, condition_str, **kwargs)
    ```
    """
    if interval_seconds is None:
        interval_seconds = 1
    if timeout_seconds is None:
        timeout_seconds = 60
    start_seconds = int(time.time())

    print('\n\nWaiting for %s ...' % condition_str)
    while True:
        if func():
            print('Done waiting for %s' % condition_str)
            break
        if (int(time.time()) - start_seconds) >= timeout_seconds:
            msg = 'Time out occurred while waiting for %s' % condition_str
            raise Exception(msg)

        time.sleep(interval_seconds)
    

class Table(object):
    def __init__(self, title, headers, col_width=15):
        self.title = title
        self.headers = headers
        self.col_width = col_width
        self.rows = []

    def append_row(self, row):
        diff = len(self.headers) - len(row)
        for i in range(0, diff):
            row.append("_")

        self.rows.append(row)

    def __str__(self):
        out = ""
        border = "-" * (len(self.headers) * self.col_width)

        out += "\n"
        out += border
        out += "\n%s\n" % self.title
        out += border
        out += "\n"

        for h in self.headers:
            out += ("%%-%ds" % self.col_width) % str(h)
        out += "\n"

        for row in self.rows:
            for r in row:
                out += ("%%-%ds" % self.col_width) % str(r)
            out += "\n"
        out += border
        out += "\n\n"

        return out

#Test_otg_flows('172.16.14.106')