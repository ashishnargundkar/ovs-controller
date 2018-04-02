from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import HANDSHAKE_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.controller import dpset
from ryu.ofproto import ofproto_v1_0


class L2Switch(app_manager.RyuApp):
    _my_switches = list()

    def __init__(self, *args, **kwargs):
        super(L2Switch, self).__init__(self, *args, **kwargs)

    # @set_ev_cls(dpset.EventDP, HANDSHAKE_DISPATCHER)
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def do_when_switch_conn(self, ev):
        msg = ev.msg
        dp = msg.datapath
        print "Addr of switch is ", ev.switch.dp.address

