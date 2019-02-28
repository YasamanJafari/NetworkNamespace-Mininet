from mininet.topo import Topo

class MyTopo( Topo ):

    def __init__( self , hostNum):
        "Create custom topo."
        Topo.__init__( self )

        hosts = []
        for i in range(hostNum):
            newHost = self.addHost('h'+ str(i+1))
            hosts.append(newHost)
    
        switch1 = self.addSwitch( 's1' )

        for i in range(hostNum):
            self.addLink(hosts[i], switch1)

hostNum = input("Enter number of Hosts please.\n")
topos = { 'mytopo': ( lambda: MyTopo(hostNum) ) }