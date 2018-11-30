# Copyright (C) 2016 Nippon Telegraph and Telephone Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller import dpset
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet


import json
import socket
import logging
import traceback

import config

logging.basicConfig(level=logging.DEBUG)

class ExampleSwitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(ExampleSwitch13, self).__init__(*args, **kwargs)
        # initialize mac address table.
        self.mac_to_port = {}
        self._dpid_to_nid = {}
        self._adj_graph = {}
        self._ipop_ctrl_comm_port = config.IPOP_CTRL_COMM_PORT

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # install the table-miss flow entry.
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # construct flow_mod message and send it.
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                match=match, instructions=inst)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # get Datapath ID to identify OpenFlow switches.
        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})

        # analyse the received packets using the packet library.
        pkt = packet.Packet(msg.data)
        eth_pkt = pkt.get_protocol(ethernet.ethernet)
        dst = eth_pkt.dst
        src = eth_pkt.src

        # get the received port number from packet_in message.
        in_port = msg.match['in_port']

        self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)

        # learn a mac address to avoid FLOOD next time.
        self.mac_to_port[dpid][src] = in_port

        # if the destination mac address is already learned,
        # decide which port to output the packet, otherwise FLOOD.
        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        # construct action list.
        actions = [parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time.
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
            self.add_flow(datapath, 1, match, actions)

            # TODO code for calling the IPOP controller to get the adjacency
            # list

        # construct packet_out message and send it.
        out = parser.OFPPacketOut(datapath=datapath,
                                  buffer_id=ofproto.OFP_NO_BUFFER,
                                  in_port=in_port, actions=actions,
                                  data=msg.data)
        datapath.send_msg(out)

    @set_ev_cls(dpset.EventDP, MAIN_DISPATCHER)
    def req_nid_on_node_join(self, ev):
        dpid = ev.dp.id
        switch_addr = self._get_ipop_ctrl_comm_address(ev)

        logging.debug(
            "Switch {} just joined controller. Querying IPOP controller"
            " at address {} requesting NID...".format(dpid, switch_addr))

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((switch_addr, self._ipop_ctrl_comm_port))
            s.send_msg(json.dumps({"RequestType": "NID"}))
            nid_resp = s.recv()
            nid = nid_resp.json()["NID"]

            logging.debug("Mapping DPID {} to NID {}".format(dpid, nid))
            self._dpid_to_nid[dpid] = nid
        except Exception:
            logging.error("An exception occurred while getting nid from"
                          " {}".format(switch_addr))
            logging.error(traceback.format_exc())

    @set_ev_cls(dpset.EventPortAdd, MAIN_DISPATCHER)
    def req_neighbours_list_on_port_add(self, ev):
        dpid = ev.dp.id
        nid = self._dpid_to_nid[dpid]
        switch_addr = self._get_ipop_ctrl_comm_address(ev)

        logging.debug("Switch {} added a new port. Querying IPOP controller"
                      "at address: {} requesting neighbours list..."
                      .format(dpid, switch_addr))

        try:
            # neighbours_resp = requests.post(
                # switch_addr, {"RequestType": "Neighbours"})
            # neighbours = neighbours_resp.json()["Neighbours"]

            # logging.debug(
                # "Got neighbours list {} from nid {}".format(neighbours, nid))
            # self._adj_graph[nid] = neighbours
            print("")
        except Exception:
            logging.error("An exception occurred while getting neighbours from"
                          "{}".format(switch_addr))
            logging.error(traceback.format_exc())

    def _get_ipop_ctrl_comm_address(self, ev):
        return ev.dp.address[0]
