import logging as log
import snappi
from datetime import datetime
import time

print("KENG demo")
def Test_ebgp_route_prefix():
    test_const = {
        "pktRate": 200,
        "pktCount": 1000,
        "pktSize": 128,
        "trafficDuration": 20,
        "txMac": "00:00:01:01:01:01",
        "txIp": "192.168.11.2",
        "txGateway": "192.168.11.1",
        "txPrefix": 24,
        "txAs": 200,
        "rxMac": "00:00:01:01:01:02",
        "rxIp": "192.168.12.2",
        "rxGateway": "192.168.12.1",
        "rxPrefix": 4,
        "rxAs": 300,
        "txRouteCount": 5,
        "rxRouteCount": 5,
        "txAdvRouteV4": "200.1.1.1",
        "rxAdvRouteV4": "201.1.1.1",
    }

    api = snappi.api(location="https://10.36.86.26:8443", verify=False)

    c = ebgp_route_prefix_config(api, test_const)

    api.set_config(c)

    start_protocols(api)

    wait_for(lambda: bgp_metrics_ok(api, test_const),"correct bgp peering")

    wait_for(lambda: bgp_prefixes_ok(api, test_const),"correct bgp prefixes")

    # start_capture(api)

    start_transmit(api)

    wait_for(lambda: flow_metrics_ok(api, test_const), "flow metrics",2,90)

    # stop_capture(api)

    # get_capture(api, "prx", "prx.pcap")
    # get_capture(api, "ptx", "ptx.pcap")


def ebgp_route_prefix_config(api, tc):
    c = api.config()
    
    ptx = c.ports.add(name="ptx", location="10.36.86.26:5555;1+10.36.86.26:50071;ens4")
    prx = c.ports.add(name="prx", location="10.36.86.26:5555;2+10.36.86.26:50071;ens5")

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

    dtx.bgp.router_id = tc["txIp"]

    dtx_bgpv4 = dtx.bgp.ipv4_interfaces.add(ipv4_name=dtx_ip.name)

    dtx_bgpv4_peer = dtx_bgpv4.peers.add(name="dtx_bgpv4_peer")
    dtx_bgpv4_peer.set(
        as_number=tc["txAs"], as_type=dtx_bgpv4_peer.EBGP, peer_address=tc["txGateway"]
    )
    dtx_bgpv4_peer.learned_information_filter.set(
        unicast_ipv4_prefix=True, unicast_ipv6_prefix=True
    )

    dtx_bgpv4_peer_rrv4 = dtx_bgpv4_peer.v4_routes.add(name="dtx_bgpv4_peer_rrv4")

    dtx_bgpv4_peer_rrv4.addresses.add(
        address=tc["txAdvRouteV4"], prefix=16, count=tc["txRouteCount"], step=1
    )

    dtx_bgpv4_peer_rrv4.advanced.set(
        include_multi_exit_discriminator=False, include_local_preference=False
    )
    drx_eth = drx.ethernets.add(name="drx_eth")
    drx_eth.connection.port_name = prx.name
    drx_eth.mac = tc["rxMac"]

    drx_ip = drx_eth.ipv4_addresses.add(name="drx_ip")
    drx_ip.set(address=tc["rxIp"], gateway=tc["rxGateway"], prefix=tc["rxPrefix"])

    drx.bgp.router_id = tc["rxIp"]

    drx_bgpv4 = drx.bgp.ipv4_interfaces.add()
    drx_bgpv4.ipv4_name = drx_ip.name

    drx_bgpv4_peer = drx_bgpv4.peers.add(name="drx_bgpv4_peer")
    drx_bgpv4_peer.set(
        as_number=tc["rxAs"], as_type=drx_bgpv4_peer.EBGP, peer_address=tc["rxGateway"]
    )
    drx_bgpv4_peer.learned_information_filter.set(
        unicast_ipv4_prefix=True, unicast_ipv6_prefix=True
    )

    drx_bgpv4_peer_rrv4 = drx_bgpv4_peer.v4_routes.add(name="drx_bgpv4_peer_rrv4")

    drx_bgpv4_peer_rrv4.addresses.add(
        address=tc["rxAdvRouteV4"], prefix=16, count=tc["rxRouteCount"], step=1
    )
    drx_bgpv4_peer_rrv4.advanced.set(
        include_multi_exit_discriminator=False, include_local_preference=False
    )

    for i in range(0, 2):
        f = c.flows.add()
        f.duration.fixed_packets.packets = tc["pktCount"]
        f.rate.pps = tc["pktRate"]
        f.size.fixed = tc["pktSize"]
        f.metrics.enable = True

    ftx_v4 = c.flows[0]
    ftx_v4.name = "ftx_v4"
    ftx_v4.tx_rx.device.set(
        tx_names=[dtx_bgpv4_peer_rrv4.name], rx_names=[drx_bgpv4_peer_rrv4.name]
    )

    ftx_v4_eth, ftx_v4_ip, ftx_v4_udp = ftx_v4.packet.ethernet().ipv4().udp()
    ftx_v4_eth.src.value = dtx_eth.mac
    ftx_v4_ip.src.value = tc["txAdvRouteV4"]
    ftx_v4_ip.dst.value = tc["rxAdvRouteV4"]
    ftx_v4_udp.src_port.value = 5000
    ftx_v4_udp.dst_port.value = 6000

    frx_v4 = c.flows[1]
    frx_v4.name = "frx_v4"
    frx_v4.tx_rx.device.set(
        tx_names=[drx_bgpv4_peer_rrv4.name], rx_names=[dtx_bgpv4_peer_rrv4.name]
    )

    frx_v4_eth, frx_v4_ip, frx_v4_udp = frx_v4.packet.ethernet().ipv4().udp()
    frx_v4_eth.src.value = drx_eth.mac
    frx_v4_ip.src.value = tc["rxAdvRouteV4"]
    frx_v4_ip.dst.value = tc["txAdvRouteV4"]
    frx_v4_udp.src_port.value = 5000
    frx_v4_udp.dst_port.value = 6000

    # print("Config:\n%s", c)
    return c

def bgp_metrics_ok(api, tc):
    for m in get_bgpv4_metrics(api):
        if (
            m.session_state == m.DOWN
            or m.routes_advertised != 2 * tc["txRouteCount"]
            or m.routes_received != 2 * tc["rxRouteCount"]
        ):
            return False
    return True

def bgp_prefixes_ok(api, tc):
    prefix_count = 0
    for m in get_bgp_prefixes(api):
        for p in m.ipv4_unicast_prefixes:
            for key in ["tx", "rx"]:
                if (
                    p.ipv4_address == tc[key + "AdvRouteV4"]
                    and p.ipv4_next_hop == tc[key + "NextHopV4"]
                ):
                    prefix_count += 1
        for p in m.ipv6_unicast_prefixes:
            for key in ["tx", "rx"]:
                if (
                    p.ipv6_address == tc[key + "AdvRouteV6"]
                    and p.ipv6_next_hop == tc[key + "NextHopV6"]
                ):
                    prefix_count += 1

    return prefix_count == 4

def flow_metrics_ok(api, tc):
    for m in get_flow_metrics(api):
        if (
            m.transmit != m.STOPPED
            or m.frames_tx != tc["pktCount"]
            or m.frames_rx != tc["pktCount"]
        ):
            return False
    return True

def get_bgpv4_metrics(api):
    print("%s Getting bgpv4 metrics    ..." % datetime.now())
    req = api.metrics_request()
    req.bgpv4.peer_names = []

    metrics = api.get_metrics(req).bgpv4_metrics

    tb = Table(
        "BGPv4 Metrics",
        [
            "Name",
            "State",
            "Routes Adv.",
            "Routes Rec.",
        ],
    )

    for m in metrics:
        tb.append_row(
            [
                m.name,
                m.session_state,
                m.routes_advertised,
                m.routes_received,
            ]
        )

    print(tb)
    return metrics

def get_bgp_prefixes(api):
    print("%s Getting BGP prefixes    ..." % datetime.now())
    req = api.states_request()
    req.bgp_prefixes.bgp_peer_names = []
    bgp_prefixes = api.get_states(req).bgp_prefixes

    tb = Table(
        "BGP Prefixes",
        [
            "Name",
            "IPv4 Address",
            "IPv4 Next Hop",
            "IPv6 Address",
            "IPv6 Next Hop",
        ],
        20,
    )

    for b in bgp_prefixes:
        for p in b.ipv4_unicast_prefixes:
            tb.append_row(
                [
                    b.bgp_peer_name,
                    "{}/{}".format(p.ipv4_address, p.prefix_length),
                    p.ipv4_next_hop,
                    "",
                    "" if p.ipv6_next_hop is None else p.ipv6_next_hop,
                ]
            )
        for p in b.ipv6_unicast_prefixes:
            tb.append_row(
                [
                    b.bgp_peer_name,
                    "",
                    "" if p.ipv4_next_hop is None else p.ipv4_next_hop,
                    "{}/{}".format(p.ipv6_address, p.prefix_length),
                    p.ipv6_next_hop,
                ]
            )

    print(tb)
    return bgp_prefixes

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


if __name__ == "__main__":
    Test_ebgp_route_prefix()
