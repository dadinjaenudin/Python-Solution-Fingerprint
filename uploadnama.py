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

from datetime import datetime

# Sound library
import winsound
from os.path import abspath, isfile

DBPool = cx_Oracle.SessionPool(user='hrs',password='hrs041972',dsn='xe',min=1,max=2,increment=1) 
DBPool.timeout = 120 #idle session timeout
connection = DBPool.acquire()

# Call from Python
# python 1 192.168.1.202
mesin_id   = sys.argv[1]
mesin_ip   = sys.argv[2]
url_mesin  = 'http://'+mesin_ip+':80/iWsService'

def UPLOAD_NAMA():
    
      try:

          print "Upload PIN dan Nama"
          # try to catch error if database not up
          cursor = connection.cursor()
          cursor.execute ("select pegawai_id, nama from pegawai order by pegawai_id")
          result_set = cursor.fetchall()
          for rec in result_set:
              print rec[0], rec[1]

              xml = """<?xml version='1.0' encoding='utf-8'?>
              <SetUserInfo>
              <ArgComKey xsi:type="xsd:integer">0</ArgComKey>
              <Arg>
              <PIN>%s</PIN>
              <Name>%s</Name>
              </Arg>
              </SetUserInfo>
              """ %(rec[0], rec[1])

              headers = {'Content-Type': 'text/xml'} # set what your server accepts          
              response = requests.post(url_mesin,  data=xml, headers=headers).text          
              tree = ET.fromstring(response)
              lst = tree.findall('Row')
              #print 'Row count:', len(lst)

          connection.commit()
          cursor.close()

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

def main():
    UPLOAD_NAMA()

if __name__ == "__main__":
    main()
