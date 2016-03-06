#!/usr/bin/python
                  
from time import *
import sys,os,serial,subprocess
from string import *

PIN='1151'
Zeichen='AT:ATE0:AT+CPIN='+PIN+':AT+CMGF=1:AT+CLIP=1:AT+CLCK="AI",1'.replace("\n","").replace("\n","")
Port=2
Zeichenkette=Zeichen.split(":")


SMSSpeicher="2"
debug=0
GPIO1="18"
GPIO2="4"
summzeit=2
Einlass="/etc/einlass"
Admin="/etc/key_admin"

if debug: print """

Theorie:
--------------------------------
EchoOFF='ATE0'
PINEingabe='AT+CPIN=?'
Textmode='AT+CMGF=1'
Rufbereitschaft='AT+CLCK="AI",1'
???Nummernausgabe='AT+CLIP=1'
AT='AT'
Geraet='ATI'
Guthaben='AT+CUSD=1,"*101#"'
SMSAbfrage='AT+CMGL="ALL"'

probiere mal:
dmesg | grep "usb .-.: Product:" | sed 'si\[.*\] usb ii1' | sed 'siProduct:ii1'
und:
ls -l /sys/class/tty/ | grep ttyUSB
--------------------------------
Praxis:

"""

if debug: print Zeichen

# moegliche GPIOs 4,18 Auswahl fuer 18

os.popen('echo '+GPIO1+' > /sys/class/gpio/export')
sleep(1)
os.popen('echo out > /sys/class/gpio/gpio'+GPIO1+'/direction')
os.popen('echo 1 > /sys/class/gpio/gpio'+GPIO1+'/value')

#os.popen('echo '+GPIO2+' > /sys/class/gpio/export')
#os.popen('echo out > /sys/class/gpio/gpio'+GPIO2+'/direction')
#os.popen('echo 0 > /sys/class/gpio/gpio'+GPIO2+'/value')


#os.popen('echo 4 > /sys/class/gpio/export')
#os.popen('echo out > /sys/class/gpio/gpio4/direction')
#os.popen('echo 0 > /sys/class/gpio/gpio4/value')

#os.popen('echo 4 > /sys/class/gpio/export')
#os.popen('echo out > /sys/class/gpio/gpio4/direction')
#os.popen('echo 0 > /sys/class/gpio/gpio4/value')




#Zeichenkette = sys.stdin.readline().replace("\n","").replace("\n","").split(":")


#print "Gesendet: "+Zeichen
#print "Ausgabe-Zeilen: "+sys.argv[2]


while(1):
	seri=-1
	erg=subprocess.Popen("ls /dev/ttyUSB*", stdout=subprocess.PIPE, stderr=None, shell=True).communicate()[0]
	erg=erg.replace("/dev/ttyUSB","").split("\n")
	erg.pop()
	if debug: print "Serialports:",erg
	try:
		if debug: print "versuche serialport",erg[Port],"zu oeffnen"
		seri = serial.Serial(port="/dev/ttyUSB"+erg[Port], baudrate=19200, timeout=None, bytesize=8, parity='N', stopbits=1, xonxoff=False, rtscts=False )
		if debug: print "serialport",erg[Port],"geoeffnet"
	except:
		ausgvenid=os.popen("usbmode -l").readlines()
		for venid in ausgvenid:
			if debug: print "Reset: ",venid
			os.popen('usbreset '+venid.split(" ")[2])
			sleep(10)
	if seri==-1:
		if debug:
			print "kein Geraet"
	                ausgvenid=os.popen("usbmode -l").readlines()
	                for venid in ausgvenid:
	                        if debug: print "Reset: ",venid
	                        os.popen('usbreset '+venid.split(" ")[2])
	                        sleep(10)
																		
	else:
		if debug: print "verbunden"
		Anruf=3
		while(1):
			einlass=subprocess.Popen("cat "+Einlass, stdout=subprocess.PIPE, stderr=None, shell=True).communicate()[0]
			einlass=einlass.replace("\r","").split("\n")
			admin=subprocess.Popen("cat "+Admin, stdout=subprocess.PIPE, stderr=None, shell=True).communicate()[0]
			admin=admin.replace("\r","").split("\n")
			if debug :
				print "einlass: ",einlass
				print "Admin ",admin
			AT=1
			i=0
			while(AT):
				if debug: print "AT-Mode"
				if (i<len(Zeichenkette)):
					sleep(1)
					if debug: print "Schreibe Zeichen",Zeichenkette[i]
					seri.write(Zeichenkette[i]+"\r\n")
					OK=1
					while(OK):
						ausg=seri.readline()
						if debug: print ausg
						if "OK" or "ERROR" in ausg:
							OK=0
							i+=1
				else:
					AT=0
			while(Anruf):
				if debug: print "Anruf-Mode"
				ausg=seri.readline()
				if debug : print ausg
				if "+CLIP:" in ausg or "RING" in ausg:
					if debug: print "clip oder ring in ausg, Anruf:",Anruf
					#i=0
					Anruf-=1
					if "+CLIP" in ausg:
						Anruf=0
						if debug: print "clip in ausg, es wird spannend"
						for j in einlass:
							if debug: print "teste fuer:",j,"-",ausg
							if (j!="") and j.isdigit() and (j in ausg):
								if debug: 
									print "GPIO on"
								else:
									os.popen('echo 0 > /sys/class/gpio/gpio'+GPIO1+'/value')
								sleep(summzeit)
								if debug:
									print "GPIO off"
								else:
									os.popen('echo 1 > /sys/class/gpio/gpio'+GPIO1+'/value')
								#Anruf=0
				#if "OK" or "ERROR" in ausg:
				#	i+=1
			#Auslesen der SMS
			seri.write('AT+CMGL="ALL"\r\n')
			if Anruf==0:
				SMS=1
			Freischalten=0
			while(SMS):
				if debug : print "SMS-Mode"
				if Freischalten==0 or Freischalten==1:
					ausg=seri.readline()
					if debug: print ausg
				else:
					ausg=""
				if debug : print "Fr: ",Freischalten
				if debug : print "Anruf",Anruf
				if (Freischalten==1) and not ("+CMGL:" in ausg):
					if ausg.replace("\r","").replace("\n","").isdigit():
						os.popen('echo "'+ausg+'" >> '+Einlass)
					else:
						if debug : print "kein digit"
					if "delete" in ausg:
						os.popen('echo ""  > '+Einlass)
				for a in admin:
					if ("+CMGL:" in ausg) and ( a != "" ) and (a in ausg) and (Freischalten==0):
						if debug: print "Freischalten=1: ",a,"?=",ausg
						Freischalten=1
				if (("OK" in ausg) or ("ERROR" in ausg) or (("+CGML:"in ausg)) and Freischalten):
					seri.write('AT+CMGD='+SMSSpeicher+',3\r\n')
					SMS=0
					Freischalten=5
				Anruf=3

