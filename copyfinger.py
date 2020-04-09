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
# python mesin_name ip_source ip_target
# python 1 192.168.1.202 192.168.1.202 

mesin_id          = sys.argv[1]
mesin_ip_source   = sys.argv[2]
mesin_ip_target   = sys.argv[3]

url_mesin_source  = 'http://'+mesin_ip_source+':80/iWsService'
url_mesin_target  = 'http://'+mesin_ip_target+':80/iWsService'

def DOWNLOAD_FINGER():
  
      try:

          print "Check Delete Operation"
          # try to catch error if database not up
          cursor = connection.cursor()
          cursor.execute ("select pegawai_id, nama from pegawai order by pegawai_id")
          result_set = cursor.fetchall()
          for rec in result_set:
              print rec[0], rec[1]
 
              xml = """<?xml version='1.0' encoding='utf-8'?>
                        <GetUserTemplate>
                        <ArgComKey xsi:type=xsd:integer>0</ArgComKey>
                        <Arg>
                        <PIN xsi:type=xsd:integer>%s</PIN>
                        <FingerID xsi:type=xsd:integer>0</FingerID>
                        </Arg>
                        </GetUserTemplate>
                    """ % (rec[0])

              headers = {'Content-Type': 'text/xml'} # set what your server accepts          
              response = requests.post(url_mesin_source,  data=xml, headers=headers).text          
              tree = ET.fromstring(response)
              #print response
              lst = tree.findall('Row')

              results = []
              for item in lst:
                  print 'Uplaod data to Mesin target'
                  print item.find('PIN').text
                  print item.find('FingerID').text
                  print item.find('Size').text
                  print item.find('Template').text

                  xml_upload =  """
                                <?xml version='1.0' encoding='utf-8'?>
                                <SetUserTemplate>
                                <ArgComKey xsi:type=xsd:integer>0</ArgComKey>    
                                <Arg>
                                <PIN xsi:type=xsd:integer>%s</PIN>
                                <FingerID xsi:type=xsd:integer>0</FingerID>
                                <Size>%s</Size>
                                <Valid>1</Valid>
                                <Template>%s</Template>                                  
                                </Arg>
                                </SetUserTemplate>                                  
                                """  % ( item.find('PIN').text, item.find('Size').text, item.find('Template').text   )

                  headers = {'Content-Type': 'text/xml'} # set what your server accepts
                  response = requests.post(url_mesin_target, data=xml_upload, headers=headers).text

                  xml_refresh_db =  """
                                <?xml version='1.0' encoding='utf-8'?>
                                <RefreshDB>
                                <ArgComKey xsi:type=xsd:integer>0</ArgComKey>    
                                <Arg>
                                </RefreshDB>                                  
                                """  

                  response = requests.post(url_mesin_target, data=xml_refresh_db, headers=headers).text

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

  try:
      DOWNLOAD_FINGER()

  except KeyboardInterrupt:
      print('Exit')

if __name__ == "__main__":
    main()
