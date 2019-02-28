
"""
	A pure python ping implementation using raw sockets.

	Note that ICMP messages can only be send from processes running as root
	
"""

# "return$" + self.source + "$" + file_name
# file_name + "$" + chunk + "$" + str(chunk_id)


import os
import select
import signal
import struct
import time
import sys
import time
import socket,sys
from impacket import ImpactPacket
import commands
import random

if sys.platform.startswith("win32"):
	# On Windows, the best timer is time.clock()
	default_timer = time.clock
else:
	# On most other platforms the best timer is time.time()
	default_timer = time.time


# ICMP parameters
ICMP_ECHOREPLY = 0 # Echo reply (per RFC792)
ICMP_ECHO = 8 # Echo request (per RFC792)
ICMP_MAX_RECV = 2048 # Max size of incoming buffer

MAX_SLEEP = 1000
CHUNK_SIZE = 8


def is_valid_ip4_address(addr):
	parts = addr.split(".")
	if not len(parts) == 4:
		return False
	for part in parts:
		try:
			number = int(part)
		except ValueError:
			return False
		if number > 255 or number < 0:
			return False
	return True

def to_ip(addr):
	if is_valid_ip4_address(addr):
		return addr
	return socket.gethostbyname(addr)


class Response(object):
	def __init__(self):
		self.max_rtt = None
		self.min_rtt = None
		self.avg_rtt = None
		self.packet_lost = None
		self.ret_code = None
		self.output = []

		self.packet_size = None
		self.timeout = None
		self.source = None
		self.destination = None
		self.destination_ip = None

class Ping(object):
	def __init__(self, source, destination, timeout=1000, packet_size=55, own_id=None, quiet_output=False, udp=False, bind=None):
		self.quiet_output = quiet_output
		if quiet_output:
			self.response = Response()
			self.response.destination = destination
			self.response.timeout = timeout
			self.response.packet_size = packet_size

		self.destination = destination
		self.source = source
		self.timeout = timeout
		self.packet_size = packet_size
		self.udp = udp
		self.bind = bind

		if own_id is None:
			self.own_id = os.getpid() & 0xFFFF
		else:
			self.own_id = own_id

		try:
			self.dest_ip = to_ip(self.destination)
			if quiet_output:
				self.response.destination_ip = self.dest_ip
		except socket.gaierror as e:
			self.print_unknown_host(e)
		else:
			self.print_start()

		self.seq_number = 0
		self.send_count = 0
		self.receive_count = 0
		self.min_time = 999999999
		self.max_time = 0.0
		self.total_time = 0.0

		self.file_names_to_return = []
		self.return_msg_to_home = False
		self.host_ip_addr = {}
		self.uploaded_files = []
		self.file_name_chunks_count_received = {}
		self.file_size_and_name = {}

	#--------------------------------------------------------------------------

	def print_start(self):
		msg = "\nPYTHON-PING %s (%s): %d data bytes" % (self.destination, self.dest_ip, self.packet_size)
		if self.quiet_output:
			self.response.output.append(msg)
		else:
			print(msg)

	def print_unknown_host(self, e):
		msg = "\nPYTHON-PING: Unknown host: %s (%s)\n" % (self.destination, e.args[1])
		if self.quiet_output:
			self.response.output.append(msg)
			self.response.ret_code = 1
		else:
			print(msg)

		raise Exception, "unknown_host"
		#sys.exit(-1)

	def print_success(self, delay, ip, packet_size, ip_header, icmp_header, header=False):
		if ip == self.destination:
			from_info = ip
		else:
			from_info = "%s (%s)" % (self.destination, ip)

	   	msg = "%d bytes from %s: icmp_seq=%d ttl=%d time=%.1f ms" % (packet_size, from_info, icmp_header["seq_number"], ip_header["ttl"], delay)
	   	# msg = ""

		if self.quiet_output:
			self.response.output.append(msg)
			self.response.ret_code = 0
		# else:
		# 	print(msg)
		if header:
			print("IP header: %r" % ip_header)
			print("ICMP header: %r" % icmp_header)

	def print_failed(self):
		msg = "Request timed out."

		if self.quiet_output:
			self.response.output.append(msg)
			self.response.ret_code = 1
		else:
			print(msg)

	def print_exit(self):
		msg = "\n----%s PYTHON PING Statistics----" % (self.destination)

		if self.quiet_output:
			self.response.output.append(msg)
		else:
			print(msg)

		lost_count = self.send_count - self.receive_count
		#print("%i packets lost" % lost_count)
		lost_rate = float(lost_count) / self.send_count * 100.0

		msg = "%d packets transmitted, %d packets received, %0.1f%% packet loss" % (self.send_count, self.receive_count, lost_rate)
	
		if self.quiet_output:
			self.response.output.append(msg)
			self.response.packet_lost = lost_count
		else:
			print(msg)

		if self.receive_count > 0:
			msg = "round-trip (ms)  min/avg/max = %0.3f/%0.3f/%0.3f" % (self.min_time, self.total_time / self.receive_count, self.max_time)
			if self.quiet_output:
				self.response.min_rtt = '%.3f' % self.min_time
				self.response.avg_rtt = '%.3f' % (self.total_time / self.receive_count)
				self.response.max_rtt = '%.3f' % self.max_time
				self.response.output.append(msg)
			else:
				print(msg)

		if self.quiet_output:
			self.response.output.append('\n')
		else:
			print('')

	#--------------------------------------------------------------------------

	def signal_handler(self, signum, frame):
		self.print_exit()
		msg = "\n(Terminated with signal %d)\n" % (signum)

		if self.quiet_output:
			self.response.output.append(msg)
			self.response.ret_code = 0
		else:
			print(msg)

		sys.exit(0)

	def setup_signal_handler(self):
		signal.signal(signal.SIGINT, self.signal_handler)   # Handle Ctrl-C
		if hasattr(signal, "SIGBREAK"):
			# Handle Ctrl-Break e.g. under Windows 
			signal.signal(signal.SIGBREAK, self.signal_handler)

	#--------------------------------------------------------------------------

	def header2dict(self, names, struct_format, data):
		unpacked_data = struct.unpack(struct_format, data)
		return dict(zip(names, unpacked_data))

	def createSocket(self):
		try: 
			current_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
			current_socket.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)

			# Bind the socket to a source address
			if self.bind:
				print('self.bind: ', self.bind)
				current_socket.bind((self.bind, 0)) # Port number is irrelevant for ICMP
			return current_socket

		except socket.error, (errno, msg):
			if errno == 1:
				# Operation not permitted - Add more information to traceback
				#the code should run as administrator
				etype, evalue, etb = sys.exc_info()
				evalue = etype(
					"%s - Note that ICMP messages can only be sent from processes running as root." % evalue
				)
				raise etype, evalue, etb
			raise # raise the original error

	def run(self, count=None, deadline=None):
		current_socket = self.createSocket()  
		while True:  
			inputs = [sys.stdin, current_socket]
			outputs = [current_socket]
			readable, writable, exceptional = select.select(inputs, outputs, [])

			# if (current_socket in writable) and ():
			# 	self.send_one_ping(current_socket)
			# if current_socket in readable:
			# 	self.recieve_packet(current_socket)
			# if sys.stdin in readable:
			# 	self.send_packet(current_socket)
			

			for s in readable:	
				if s == sys.stdin:
					self.send_packet(current_socket)
			
				if s == current_socket:
					self.recieve_packet(current_socket)
        
        # self.print_exit()
        # if self.quiet_output:
        #     return self.response

	def send_packet(self, current_socket):
		print("send_packet\n")
		cmd = raw_input()
		if cmd == "upload":
			file_name = raw_input("What is your file address? (upload)\n")
			chunkID = 1;
			f = open(file_name, 'rb')
			chunk = f.read(CHUNK_SIZE)
			self.uploaded_files.append(file_name)
			self.file_name_chunks_count_received[file_name] = 0
			while(chunk):
				print("CHUNK __--____--_______--____--__ " + chunk)
				send_time = self.send_one_ping(current_socket, file_name, chunk, chunkID)
				chunkID += 1
				chunk = f.read(CHUNK_SIZE)
			self.file_size_and_name[file_name] = chunkID - 1
			f.close()
			if send_time == None:
				return
			self.send_count += 1
		elif cmd == "download":
			file_name = raw_input("What is your file address? (download)\n")

			if(file_name in self.uploaded_files):
				send_time = self.send_one_ping(current_socket, file_name, "return$" + self.source + "$" + file_name)
			else:
				print("You do not have access to this file.")
		else:
			print("The command you entered is not available!\n")
    

	def recieve_packet(self, current_socket):
		receive_time, packet_size, ip, ip_header, icmp_header, data = self.receive_one_ping(current_socket)
		time.sleep(0.1)
		if(not packet_size == 0 ):
			print("recieve_packet " + data + "\n");
			self.print_success(0, ip, packet_size, ip_header, icmp_header)

			print("()()()()()  from " + data)
			if data.split('$')[1] == "return":
				self.return_msg_to_home = True;
				self.file_names_to_return.append(data.split('$')[0])
				self.host_ip_addr[data.split('$')[0]] = data.split('$')[2]

			# 0      1       2         3
			# 1 $ chunk $ chunkID $ filename
			elif icmp_header['type'] == ICMP_ECHO and data.split('$')[0] == "1":
				print("SUCCESSFULLY RECEIVED file: " + data.split('$')[3] + " chunk: " + data.split('$')[1])
				self.file_name_chunks_count_received[data.split('$')[3]] = self.file_name_chunks_count_received[data.split('$')[3]] + 1
				if(self.file_name_chunks_count_received[data.split('$')[3]] == self.file_size_and_name[data.split('$')[3]]):
					print("SUCCESSFULLY RECEIVED ALL FILE ____ " + data.split('$')[3])

			elif icmp_header['type'] == ICMP_ECHOREPLY:
				if not data.split('$')[0] == "1":
					self.send_one_ping(current_socket, data.split('$')[0], data.split('$')[1], data.split('$')[2])
		

	# send an ICMP ECHO_REQUEST packet
	def send_one_ping(self, current_socket, file_name = "", chunk = "", chunk_id = 0):
		
		#Create a new IP packet and set its source and destination IP addresses
		randomSrc = random.randrange(1, hostsCount + 1)
		while ("10.0.0." + str(randomSrc)) == self.source:
			randomSrc = random.randrange(1, hostsCount + 1)
		src = "10.0.0." + str(randomSrc)
		# print("Random Source: " + src)

		randomDst = random.randrange(1, hostsCount + 1)
		while (randomDst == randomSrc) or (("10.0.0." + str(randomDst)) == self.source):
			randomDst = random.randrange(1, hostsCount + 1)
		dst = "10.0.0." + str(randomDst)

		print("!@#!@#!@#!@#!@#! " + chunk)
		if self.return_msg_to_home == True and not chunk.split('$')[0] == "return":
			print "chunk %s is file %s "%(chunk, file_name)
			dst = self.host_ip_addr[file_name]
			src = self.source
		# print("Random Dst: " + dst + "\n")

		ip = ImpactPacket.IP()
		ip.set_ip_src(src)
		ip.set_ip_dst(dst)	

		#Create a new ICMP ECHO_REQUEST packet 
		icmp = ImpactPacket.ICMP()
		icmp.set_icmp_type(icmp.ICMP_ECHO)

		#inlude a small payload inside the ICMP packet
		#and have the ip packet contain the ICMP packet
		print "src is %s and dst is %s"%(src, dst)
		if(self.return_msg_to_home == True and not chunk.split('$')[0] == "return"):
			print ("!!!!!!!!! " + chunk.split('$')[0] + "\n")
			if(file_name in self.file_names_to_return):
				icmp.contains(ImpactPacket.Data("1$" + chunk + "$" + chunk_id + "$" + file_name))
		else:
			icmp.contains(ImpactPacket.Data(file_name + "$" + chunk + "$" + str(chunk_id)))
		ip.contains(icmp)


		#give the ICMP packet some ID
		icmp.set_icmp_id(0x03)
		
		#set the ICMP packet checksum
		icmp.set_icmp_cksum(0)
		icmp.auto_checksum = 1

		send_time = default_timer()

		# send the provided ICMP packet over a 3rd socket
		try:
			current_socket.sendto(ip.get_packet(), (dst, 1)) # Port number is irrelevant for ICMP
		except socket.error as e:
			self.response.output.append("General failure (%s)" % (e.args[1]))
			current_socket.close()
			return

		return send_time

	# Receive the ping from the socket. 
	#timeout = in ms		

	def receive_one_ping(self, current_socket):
		
		timeout = self.timeout / 1000.0
		

		while True: # Loop while waiting for packet or timeout
			select_start = default_timer()
			inputready, outputready, exceptready = select.select([current_socket], [], [], timeout)
			select_duration = (default_timer() - select_start)
			if inputready == []: # timeout
				return None, 0, 0, 0, 0


			packet_data, address = current_socket.recvfrom(ICMP_MAX_RECV)

			icmp_header = self.header2dict(
				names=[
					"type", "code", "checksum",
					"packet_id", "seq_number"
				],
				struct_format="!BBHHH",
				data=packet_data[20:28]
			)

			receive_time = default_timer()

			# if icmp_header["packet_id"] == self.own_id: # Our packet!!!
			# it should not be our packet!!!Why?
			if True:
				ip_header = self.header2dict(
					names=[
						"version", "type", "length",
						"id", "flags", "ttl", "protocol",
						"checksum", "src_ip", "dest_ip"
					],
					struct_format="!BBHHHBBHII",
					data=packet_data[:20]
				)
				packet_size = len(packet_data) - 28
				ip = socket.inet_ntoa(struct.pack("!I", ip_header["src_ip"]))
				# XXX: Why not ip = address[0] ???
				return receive_time, packet_size, ip, ip_header, icmp_header, packet_data[28:]

			timeout = timeout - select_duration
			if timeout <= 0:
				return None, 0, 0, 0, 0

def ping(source, hostname, timeout=1000, count=3, packet_size=55, *args, **kwargs):
    p = Ping(source, hostname, timeout, packet_size, *args, **kwargs)
    return p.run(count)

curr_ip = commands.getoutput('/sbin/ifconfig').split('\n')[1][20:28]

print(curr_ip)

hostsCount = input("How many hosts do you have?\n")

ping(curr_ip, "0.0.0.0")    #put your IP and destination IP address as the ping function argument and run the code. you can ping
							#the destination with your own code!!!


