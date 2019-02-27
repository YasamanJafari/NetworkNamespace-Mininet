from mininet.topo import Topo

class MyTopo( Topo ):

    def __init__( self ):
        "Create custom topo."

        Topo.__init__( self )

        firstHost = self.addHost( 'h1' )
        secondHost = self.addHost( 'h2' )
        
        firstSwitch = self.addSwitch( 's1' )
        secondSwitch = self.addSwitch( 's2' )

        self.addLink( firstHost, firstSwitch)
        # self.addLink( firstHost, firstSwitch, delay = '20ms')
        # self.addLink( firstHost, firstSwitch, delay = '90ms')
        # self.addLink( firstHost, firstSwitch, bw = 1)
        # self.addLink( firstHost, firstSwitch, bw = 15)
        # self.addLink( firstHost, firstSwitch, max_queue_size = 1)
        # self.addLink( firstHost, firstSwitch, max_queue_size = 15)

        self.addLink( secondHost, secondSwitch)
        # self.addLink( secondHost, secondSwitch, delay = '20ms' )
        # self.addLink( secondHost, secondSwitch, delay = '90ms')
        # self.addLink( secondHost, secondSwitch, bw = 1)
        # self.addLink( secondHost, secondSwitch, bw = 15)
		# self.addLink( secondHost, secondSwitch, max_queue_size = 1)
        # self.addLink( secondHost, secondSwitch, max_queue_size = 15)        

        self.addLink( firstSwitch, secondSwitch)
        # self.addLink( firstSwitch, secondSwitch, delay = '20ms' )
		# self.addLink( firstSwitch, secondSwitch, delay = '90ms')
        # self.addLink( firstSwitch, secondSwitch, bw = 1)
        # self.addLink( firstSwitch, secondSwitch, bw = 15)       
        # self.addLink( firstSwitch, secondSwitch, max_queue_size = 1) 
        # self.addLink( firstSwitch, secondSwitch, max_queue_size = 15)

topos = { 'mytopo': ( lambda: MyTopo() ) }
