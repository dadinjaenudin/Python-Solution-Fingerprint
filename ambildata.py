import json
import time
import sys
import select
import os
import cx_Oracle
import threading
import requests
import xml.etree.cElementTree as ET
import urllib2
import logging

import tornado.ioloop, tornado.web, tornado.websocket, os.path
import tornado.httpserver
import tornado.auth
import tornado.escape
import tornado.options
import tornado.web
from datetime import datetime
# Sound library
import winsound
from os.path import abspath, isfile

import zmq
from zmq.eventloop import ioloop, zmqstream
ioloop.install()

## ZeroMQ Server
context = zmq.Context()
# Subscriber tells us when it's ready here
receiver = context.socket(zmq.PULL)
receiver.bind("tcp://*:5571")

# We send updates via this socket
publisher = context.socket(zmq.PUB)
publisher.bind("tcp://*:5561")

DBPool = cx_Oracle.SessionPool(user='hrs',password='hrs041972',dsn='xe',min=1,max=2,increment=1) 
DBPool.timeout = 120 #idle session timeout
connection = DBPool.acquire()

# Call from Python
# python 1 192.168.1.202
mesin_id   = sys.argv[1]
mesin_ip   = sys.argv[2]
url_mesin  = 'http://'+mesin_ip+':80/iWsService'

def MESIN():

      xml = """<?xml version='1.0' encoding='utf-8'?>
      <GetAttLog>
      <ArgComKey xsi:type="xsd:integer">0</ArgComKey>
      <Arg>
      <PIN xsi:type="xsd:integer">All</PIN>
      </Arg>
      </GetAttLog>
      """
      
      try:
          headers = {'Content-Type': 'text/xml'} # set what your server accepts          
          response = requests.post(url_mesin,  data=xml, headers=headers).text          
          tree = ET.fromstring(response)
          lst = tree.findall('Row')
          #print lst
          print response

          # harus nya tampilan seperti ini waktu response nya  
          """          
          <?xml version="1.0" encoding="iso8859-1" standalone="no"?>
          <GetAttLogResponse>
          <Row><PIN>1</PIN><DateTime>2016-03-18 12:59:58</DateTime><Verified>1</Verified><
          Status>0</Status><WorkCode>0</WorkCode></Row>
          </GetAttLogResponse>
          """

          #print 'Row count:', len(lst)

          if len(lst)==0:
              print("Waiting Next Finger ...." )

          results = []
          for item in lst:

              print("Incoming Finger ..." )

              # try to catch error if database not up
              cursor = connection.cursor()

              # Date from Server
              i = datetime.now()
              #tglabsen      = i.strftime('%Y%m%d %H:%M:%S')
              #tglabsen1     = i.strftime('%Y/%m/%d %H:%M:%S') # Buat di di tampilkan saja

              # Date from Mesin
              tglabsen  = item.find('DateTime').text
              tglabsen1 = item.find('DateTime').text

              # in  from sp 
              i_pin     = cursor.var(cx_Oracle.STRING)
              i_pin.setvalue(0, item.find('PIN').text ) # come from mesin
              i_mesin   = cursor.var(cx_Oracle.STRING)
              i_mesin.setvalue(0, mesin_id ) # Nomor Mesin
              i_tanggal = cursor.var(cx_Oracle.STRING)
              i_tanggal.setvalue(0, tglabsen )

              # out from sp 
              o_retur   = cursor.var(cx_Oracle.STRING)
              o_nama    = cursor.var(cx_Oracle.STRING)
              o_bagian  = cursor.var(cx_Oracle.STRING)

              l_query   = cursor.callproc('HR_PKG.add_mesin_absensi', ( i_pin , i_tanggal, i_mesin, o_nama, o_bagian, o_retur ))
              # Get Value From l_out in index 3
              row_nama     = l_query[3] # [2] index dimuladi dari 0
              row_bagian   = l_query[4] # [2] index dimuladi dari 0
              row_retur    = l_query[5] # [2] index dimuladi dari 0      

              connection.commit()
              cursor.close()

              print row_retur
              # Berhasil insert ke database    
              results = []
              if row_retur == '0':
                  path = abspath('C://HRS//sound//0863.wav')
                  if isfile(path):
                      with open(path, 'rb') as f:
                          data = f.read()
                      winsound.PlaySound(data, winsound.SND_MEMORY)

                  print "Record inserted!." 
                  results.append({"pin": '1', "status": 0, "nama" : row_nama, "bagian" : row_bagian, "tanggal" : tglabsen1 })
                  json_encoded = json.dumps(results, indent=4)
                  print json_encoded
                  publisher.send_multipart(('MESIN1', json_encoded))

          # after that ClearLogData will be executed
          # Clear Log will be executd after loop just in case 
          # Clear log after all data insert to database if there is more than 1 data  
          # Just Make sure data entered to database before clear log
          # Make sure Call from application in case database not up 
          if len(lst) > 0:            
              print("Clearing Data Log" )

              xml = """<?xml version='1.0' encoding='utf-8'?>
              <ClearData>
              <ArgComKey xsi:type="xsd:integer">0</ArgComKey>
              <Arg><Value xsi:type="xsd:integer">3</Value></Arg>
              </ClearData>
              """

              headers = {'Content-Type': 'text/xml'} # set what your server accepts
              response = requests.post(url_mesin, data=xml, headers=headers).text

      except requests.exceptions.Timeout:
          print "Network Problem, Network Too Slow Request Timeout" 
          # Maybe set up for a retry, or continue in a retry loop
      except requests.exceptions.TooManyRedirects:
          print "Network Problem, TooManyRedirects" 
          # Tell the user their URL was bad and try a different one
      except requests.exceptions.RequestException as e:
          print "Tidak dapat konek ke Mesin 1, Silahkan Periksa Jaringan"
          # catastrophic error. bail.
          #print e
          #sys.exit(1)
          
# Sample def
def publish():
  publisher.send_multipart(("heartbeat", "OHAI"))

def main():
  try:

      worker  = threading.Thread(target=MESIN)
      worker.daemon  =True
      worker.start()

      print "Ctrl + C Untuk Close "
      ioloop.PeriodicCallback(MESIN, 100).start()
      ioloop.IOLoop.instance().start()

  except KeyboardInterrupt:
      print('Exit')

if __name__ == "__main__":
    main()
