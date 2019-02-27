from mininet.topo import Topo

class MyTopo( Topo ):

    def __init__( self ):
        "Create custom topo."

        Topo.__init__( self )

        host1 = self.addHost( 'h1' )
        host2 = self.addHost( 'h2' )
        
        switch1 = self.addSwitch( 's1' )
        switch2 = self.addSwitch( 's2' )
        switch3 = self.addSwitch( 's3' )
        switch4 = self.addSwitch( 's4' )
        switch5 = self.addSwitch( 's5' )
        switch6 = self.addSwitch( 's6' )
        switch7 = self.addSwitch( 's7' )


        self.addLink( host1, switch1)
        # self.addLink( firstHost, firstSwitch, delay = '90')
        # self.addLink( firstHost, firstSwitch, bw = '1')
        # self.addLink( firstHost, firstSwitch, bw = '15')
        # self.addLink( firstHost, firstSwitch, max_queue_size = '1')
        # self.addLink( firstHost, firstSwitch, max_queue_size = '15')

        self.addLink( host2, switch7)
        # self.addLink( secondHost, secondSwitch, delay = '90')
        # self.addLink( secondHost, secondSwitch, bw = '1')
        # self.addLink( secondHost, secondSwitch, bw = '15')
		# self.addLink( secondHost, secondSwitch, max_queue_size = '1')
        # self.addLink( secondHost, secondSwitch, max_queue_size = '15')        

        self.addLink( switch1, switch2,)
        self.addLink( switch2, switch3)
        self.addLink( switch3, switch4)
        self.addLink( switch4, switch5)
        self.addLink( switch5, switch6)
        self.addLink( switch6, switch7)

topos = { 'mytopo': ( lambda: MyTopo() ) }