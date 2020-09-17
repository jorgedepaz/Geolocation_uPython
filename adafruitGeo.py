import network
import time
from umqtt.robust import MQTTClient
import os
import gc
import sys

import network
import ubinascii
import ujson
import urequests as requests

# WiFi connection information
apikey = "yourapikey"
url = "https://www.googleapis.com/geolocation/v1/geolocate?key="+ apikey

WIFI_SSID = 'CASA'
WIFI_PASSWORD = '321321'

# turn off the WiFi Access Point
ap_if = network.WLAN(network.AP_IF)
ap_if.active(False)

# connect the device to the WiFi network
wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect(WIFI_SSID, WIFI_PASSWORD)

# wait until the device is connected to the WiFi network
MAX_ATTEMPTS = 20
attempt_count = 0
while not wifi.isconnected() and attempt_count < MAX_ATTEMPTS:
    attempt_count += 1
    time.sleep(1)

if attempt_count == MAX_ATTEMPTS:
    print('could not connect to the WiFi network')
    sys.exit()


random_num = int.from_bytes(os.urandom(3), 'little')
mqtt_client_id = bytes('client_'+str(random_num), 'utf-8')


ADAFRUIT_IO_URL = b'io.adafruit.com' 
ADAFRUIT_USERNAME = b'alejorivera'
ADAFRUIT_IO_KEY = b'aio_ogFk85bsz8r3oNvcXWKJ45BIQNfj'
ADAFRUIT_IO_FEEDNAME = b'gps'

client = MQTTClient(client_id=mqtt_client_id, 
                    server=ADAFRUIT_IO_URL, 
                    user=ADAFRUIT_USERNAME, 
                    password=ADAFRUIT_IO_KEY,
                    ssl=False)
try:            
    client.connect()
except Exception as e:
    print('could not connect to MQTT server {}{}'.format(type(e).__name__, e))
    sys.exit()


mqtt_feedname = bytes('{:s}/feeds/{:s}'.format(ADAFRUIT_USERNAME, ADAFRUIT_IO_FEEDNAME), 'utf-8')
PUBLISH_PERIOD_IN_SEC = 10 
while True:
    try:
        req = {}
        aps = []
        print("Analizando puntos de acceso cercanos")
        redes = wifi.scan()
        for x in redes:
            ap = {}
            ap["macAddress"] = ubinascii.hexlify((x[1]),':').decode()
            ap["signalStrength"] = x[3]
            ap["age"] = 0
            ap["channel"] = x[2]
            ap["signalToNoiseRatio"] = 0
            aps.append(ap)
    
        req["wifiAccessPoints"] = aps
        toSend = ujson.dumps(req)
        response = requests.post(url, data = toSend)
        print("Coordenadas del dispositivo")
        
        position=dict(response.json())
        lat = position["location"]["lat"]
        lng = position["location"]["lng"]
        print(lat,lng)
        free_heap_in_bytes ='{"value": 22.587, "lat":'+str(lat)+',"lon":'+str(lng)+',"ele": 112}'
        
        
        client.publish(mqtt_feedname,    
                   free_heap_in_bytes, 
                   qos=0)
        print("Publicado", free_heap_in_bytes)
        time.sleep(PUBLISH_PERIOD_IN_SEC)
    except KeyboardInterrupt:
        print('Ctrl-C pressed...exiting')
        client.disconnect()
        sys.exit()
