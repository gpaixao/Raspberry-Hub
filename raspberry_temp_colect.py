#!/usr/bin/python
# -*- coding: utf-8 -*- 

# comentario "comentario"
import os
import glob
import time
import datetime
import MySQLdb
import RPi.GPIO as GPIO
import smtplib
from time import strftime
from smtplib import SMTPException

GPIO.setwarnings(False)

# to use Raspberry Pi board pin numbers  
#GPIO.setmode(GPIO.BOARD)

# to use Raspberry Pi BCM numbers
GPIO.setmode(GPIO.BCM)
# set up GPIO output channel
LEDverde = 23
LEDvermelho = 24
GPIO.setup(LEDverde, GPIO.OUT)
GPIO.setup(LEDvermelho, GPIO.OUT)

os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

temp_sensor = '/sys/bus/w1/devices/28-000004f8a15c/w1_slave'

#base_dir='/sys/bus/w1/devices/'
#device_folder=glob.glob(base_dir+'28*')[0]
#device_file=device_folder+'/w1_slave'

def temp_raw():

	f = open(temp_sensor, 'r')
	lines = f.readlines()
	f.close()
	return lines


def read_temp():

	lines = temp_raw()
	while lines[0].strip()[-3:] != 'YES':
		time.sleep(0.2)
		lines = temp_raw()

	temp_output = lines[1].find('t=')

	if temp_output != -1:
		temp_string = lines[1].strip()[temp_output+2:]
		temp_c = float(temp_string) / 1000.0
#		temp_f = temp_c * 9.0 / 5.0 + 32.0
#		return temp_c, temp_f
		return temp_c

# pin e tempo
def blink(pin,x):
	for i in range(0,x):
		GPIO.output(pin,GPIO.HIGH)
		print "LED HIGH"
		time.sleep(0.5)
		GPIO.output(pin,GPIO.LOW)
		print "LED LOW"
		time.sleep(0.5)
		#return

# imput temperatura e tempo
def LEDtemp(t,x):
	if read_temp() < t:
		GPIO.output(LEDverde,GPIO.HIGH)
		GPIO.output(LEDvermelho,GPIO.LOW)
		time.sleep(x)
	else:
		#GPIO.output(LEDvermelho,GPIO.HIGH)
		GPIO.output(LEDverde,GPIO.LOW)
		#blink(LEDvermelho)
		for i in range(0,1):
			blink(LEDvermelho,x)
			GPIO.output(LEDvermelho,GPIO.HIGH)
		#time.sleep(x)

# Escreve para a DB
def writeDB():
	temp = read_temp()
	datetimeWrite = (time.strftime("%Y-%m-%d ") + time.strftime("%H:%M:%S"))
	print datetimeWrite
	print temp

	# Variables for MySQL
	db = MySQLdb.connect(host="host.xdomain2x.pt", user="user", passwd="password", db="prodDBs_monitoring")
        cur = db.cursor()
	sql = ("""INSERT INTO dataCenterTempLog (datetime, temperature) VALUES (%s, %s)""",(datetimeWrite, temp))

	try:
		print "Writing to database..."
		# Execute the SQL command
		cur.execute(*sql)
		# Commit your changes in the database
		db.commit()
		print "Write Complete"
 
	except:
		# Rollback in case there is any error
		db.rollback()
		print "Failed writing to database"
 
	cur.close()
	db.close()


def sendEmail(temperatura, mensagem):

	smtpUser = 'xxx@xxxdomainxxx.pt'
	smtpPass = 'nnnmm.-.'

	toAdd  = 'domotics@xxxdomainxxx.pt'
	fromAdd = smtpUser

	subject = 'Temperatura - sala dos servidores'
	header = 'To: ' + toAdd + '\n' + 'From: ' + fromAdd + '\n' + 'Subject: ' + subject
	body = 'Temperatura na sala dos servidores: \n' + str(temperatura) + ' graus em ' + str(time.strftime("%Y-%m-%d %A ") + time.strftime("%H:%M:%S")) + '\n\n' +  mensagem

	print header + '\n' + body

#	message = """From: From Person <xxx@xxxdomainxxx.pt>
#	To: To Person <xxx@xxxdomainxxx.pt>
#	Subject: SMTP e-mail test
#	
#	This is a test e-mail message.
#	"""

	try:
		smtpObj = smtplib.SMTP('minerva.xdomain2x.pt')
		smtpObj.ehlo()
		#smtpObj.starttls()
		smtpObj.ehlo()

		#smtpObj.login(smtpUser, smtpPass)
		smtpObj.sendmail(fromAdd, toAdd, header + '\n\n' + body)
		smtpObj.quit()         
		print "Successfully sent email"
	except SMTPException:
		print "Error: unable to send email"


readTemp1 = 0
while True:
	print 'Temperatura = ', read_temp()
	print "readTemp1 = ", readTemp1
	readTemp2 = int(round(read_temp(),0))
	print "readTemp2 = ", readTemp2
	# Se a temperatura detetada nao for inferior à introduzida, o LED vermelho pisca
	# 22 graus - 10 segundos
	LEDtemp(22,10)
	
	if readTemp1 != readTemp2:	
		# escreve na base de dados e envia email
		# se a diferença de temperatura entre leituras for igual ou superior a 2 graus
		if ((readTemp2 >= readTemp1 + 2) or (readTemp2 <= readTemp1 - 2)):
		
			if readTemp1 != 0 and readTemp2 <= 21:
				m = 'A temperatura voltou ao normal'
				sendEmail(read_temp(), m)
		
			readTemp1 = int(round(read_temp(),0))
			writeDB()
			
			if readTemp1 >= 22 and readTemp1 <= 24:
				m = 'Temperatura a cima do normal - atenção'
				sendEmail(read_temp(), m)
			if readTemp1 > 24 and readTemp1 <= 30:
				m = 'Temperatura muito a cima do normal - Averiguar situação'
				sendEmail(read_temp(), m)
			if readTemp1 > 30 and readTemp1 <= 40:
				m = 'PERIGO - Temperatura extremamente elevada - Averiguar situação'
				sendEmail(read_temp(), m)
			if readTemp1 > 40:
				m = 'Poderá estar a ocorrer um incêndio - Tomar providências'
				sendEmail(read_temp(), m)


GPIO.cleanup()
