from mininet.topo import Topo

class CustomTopology(Topo):
    def __init__( self ):
        Topo.__init__( self )

        host1 = self.addHost( 'h1' )
        host2 = self.addHost( 'h2' )
        host3 = self.addHost( 'h3' )
        host4 = self.addHost( 'h4' )

        switch1 = self.addSwitch( 's1' )
        switch2 = self.addSwitch( 's2' )

        # self.addLink(host1, switch1)
        # self.addLink(host2, switch1)
        # self.addLink(host3, switch2)
        # self.addLink(host4, switch2)

        self.addLink(host1, switch1, delay = "20ms")
        self.addLink(host2, switch1, delay = "20ms")
        self.addLink(host3, switch2, delay = "15ms")
        self.addLink(host4, switch2, delay = "1ms")

        self.addLink(switch1, switch2, delay = "50ms")

topos = { 'mytopo': ( lambda: CustomTopology() ) }