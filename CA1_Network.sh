#!/bin/bash
sudo ip netns delete h1 &>/dev/null
sudo ip netns delete h2 &>/dev/null
sudo ip netns delete h3 &>/dev/null
sudo ovs-vsctl del-br s1 &>/dev/null
sudo ovs-vsctl del-br s2 &>/dev/null
sudo ip link s1-eth1 &>/dev/null
sudo ip link s1-eth2 &>/dev/null
sudo ip link s1-eth3 &>/dev/null
sudo ip link s2-eth1 &>/dev/null
sudo ip link s2-eth2 &>/dev/null
sudo ip link h1-eth0 &>/dev/null
sudo ip link h2-eth0 &>/dev/null
sudo ip link h3-eth0 &>/dev/null
sudo ip netns add h1
sudo ip netns add h2
sudo ip netns add h3
sudo ovs-vsctl add-br s1
sudo ovs-vsctl add-br s2
sudo ip link add s1-eth1 type veth peer name h1-eth0
sudo ip link add s1-eth2 type veth peer name h2-eth0
sudo ip link add s1-eth3 type veth peer name s2-eth1
sudo ip link add s2-eth2 type veth peer name h3-eth0
sudo ip link set h1-eth0 netns h1
sudo ip link set h2-eth0 netns h2
sudo ip link set h3-eth0 netns h3
sudo ovs-vsctl add-port s1 s1-eth1
sudo ovs-vsctl add-port s1 s1-eth2
sudo ovs-vsctl add-port s1 s1-eth3
sudo ovs-vsctl add-port s2 s2-eth1
sudo ovs-vsctl add-port s2 s2-eth2
sudo ip netns exec h1 ifconfig h1-eth0 10.0.0.1 up
sudo ip netns exec h1 ifconfig lo up
sudo ip netns exec h2 ifconfig h2-eth0 10.0.0.2 up
sudo ip netns exec h2 ifconfig lo up
sudo ip netns exec h3 ifconfig h3-eth0 10.0.0.3 up
sudo ip netns exec h3 ifconfig lo up
sudo ip link set s1-eth1 up
sudo ip link set s1-eth2 up
sudo ip link set s1-eth3 up
sudo ip link set s2-eth1 up
sudo ip link set s2-eth2 up
sudo ip netns exec h1 ping 10.0.0.3 
