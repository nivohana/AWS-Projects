#niv ohana 203538624
#moriah 329835771

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient
import logging
import time
import argparse
import json
from datetime import datetime
import Adafruit_DHT
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008
import numpy as np
#############################################################
### accelometer
from time import sleep
from mpu6050 import mpu6050
##############################################################
### temperature
temp_sensor = Adafruit_DHT.DHT22
temp_pin = 4
##############################################################

##############################################################
### mcp3008
CLK = 18
MISO = 23
MOSI = 24
CS = 25
mcp = Adafruit_MCP3008.MCP3008(clk=CLK, cs=CS, miso=MISO, mosi=MOSI)
## mcp.read_adc(value)
##############################################################

# Change according to your configuration
host = 'a1rpddawph4ysg-ats.iot.eu-west-1.amazonaws.com'
rootCA = '/home/pi/final_project/certificates/root-CA.crt'
privateKey = '/home/pi/final_project/certificates/56075c5af2-private.pem.key'
cert = '/home/pi/final_project/certificates/56075c5af2-certificate.pem.crt'
thingName = 'final_niv_moriah'
deviceId = thingName
topic = '/final_project/final_niv_moriah'
topic_name = topic
interval = 5

# Custom MQTT message callback
def customCallback(client, userdata, message):
    print("Received a new message: ")
    print(message.payload)
    print("from topic: ")
    print(message.topic)
    print("--------------\n\n")

# Custom Shadow callbacks
def customShadowCallback_Update(payload, responseStatus, token):
    # payload is a JSON string ready to be parsed using json.loads(...)
    # in both Py2.x and Py3.x
    if responseStatus == "timeout":
        print("Update request " + token + " time out!")
    if responseStatus == "accepted":
        payloadDict = json.loads(payload)
        print("~~~~~~~~~~~~~~~~~~~~~~~")
        print("Update request with token: " + token + " accepted!")
        print("property: " + str(payloadDict["state"]))
        print("~~~~~~~~~~~~~~~~~~~~~~~\n\n")
    if responseStatus == "rejected":
        print("Update request " + token + " rejected!")

def customShadowCallback_Get(payload, responseStatus, token):
    global topic
    # payload is a JSON string ready to be parsed using json.loads(...)
    # in both Py2.x and Py3.x
    payloadDict = json.loads(payload)
    print("++++++++GET++++++++++")
    print(payloadDict)
    if 'delta' in payloadDict['state']:
        if 'topic' in payloadDict['state']['delta']:
            topic = str(payloadDict['state']['delta']['topic'])
            print("topic: " + topic)
            print("version: " + str(payloadDict["version"]))
            print("+++++++++++++++++++++++\n\n")
        else :
            topic = '/final_project/final_niv_moriah'
            print("No topic found, using {}".format(topic))
        newPayload = '{"state":{"reported":' + json.dumps(payloadDict['state']['delta']) + '}}'
        deviceShadowHandler.shadowUpdate(newPayload, customShadowCallback_Update, 5)
    elif 'reported' in payloadDict['state']:
        if 'topic' in payloadDict['state']['reported']:
            topic = str(payloadDict['state']['reported']['topic'])
            print("topic: " + topic)
            print("version: " + str(payloadDict["version"]))
            print("+++++++++++++++++++++++\n\n")
        else :
            topic = '/final_project/final_niv_moriah'
            print("No topic found, using {}".format(topic))
    else:
        topic = '/final_project/final_niv_moriah'
        print("No topic found, using {}".format(topic))
        newPayload = '{"state":{"reported": {"topic" : '+json.dumps(topic)+'}}}'
        deviceShadowHandler.shadowUpdate(newPayload, customShadowCallback_Update, 5)

def customShadowCallback_Delta(payload, responseStatus, token):
    global topic
    # payload is a JSON string ready to be parsed using json.loads(...)
    # in both Py2.x and Py3.x
    payloadDict = json.loads(payload)
    print(payloadDict)
    print("++++++++DELTA++++++++++")
    if 'topic' in payloadDict['state']:
            topic = str(payloadDict['state']['topic'])
            print("topic: " + topic)
            print("version: " + str(payloadDict["version"]))
            print("+++++++++++++++++++++++\n\n")
    else :
        topic = '/final_project/final_niv_moriah'
        print("No topic found, using {}".topic)
    newPayload = '{"state":{"reported":' + json.dumps(payloadDict['state']) + '}}'
    deviceShadowHandler.shadowUpdate(newPayload, customShadowCallback_Update, 5)

# Configure logging
logger = logging.getLogger("AWSIoTPythonSDK.core")
logger.setLevel(logging.WARNING)
streamHandler = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

# Init AWSIoTMQTTClient
myAWSIoTMQTTShadowClient = None
myAWSIoTMQTTShadowClient = AWSIoTMQTTShadowClient(deviceId)
myAWSIoTMQTTShadowClient.configureEndpoint(host, 8883)
myAWSIoTMQTTShadowClient.configureCredentials(rootCA, privateKey, cert)

# AWSIoTMQTTClient connection configuration
myAWSIoTMQTTShadowClient.configureAutoReconnectBackoffTime(1, 32, 20)
myAWSIoTMQTTShadowClient.configureConnectDisconnectTimeout(10)  # 10 sec
myAWSIoTMQTTShadowClient.configureMQTTOperationTimeout(5)  # 5 sec

# Connect and subscribe to AWS IoT
isNotConnected = True
while (isNotConnected):
    try:
        myAWSIoTMQTTShadowClient.connect()
        isNotConnected = False
    except:
        print("connection failure")

# Create a deviceShadow with persistent subscription
deviceShadowHandler = myAWSIoTMQTTShadowClient.createShadowHandlerWithName(
    thingName, True)


# Listen on deltas
deviceShadowHandler.shadowRegisterDeltaCallback(customShadowCallback_Delta)

isNotConnected = True
while (isNotConnected):
    try:
        deviceShadowHandler.shadowGet(customShadowCallback_Get, 5)
        isNotConnected = False
    except:
        print("shadowGet failure")

myMQTTClient = myAWSIoTMQTTShadowClient.getMQTTConnection()
# Infinite offline Publish queueing
myMQTTClient.configureOfflinePublishQueueing(-1)
myMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
myMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
myMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec
# Loop forever and wait for shadow

##############################################################
##sound 
def initNoise():
    noise_sum = 0
    for i in range(1, 100):
        noise_sum += mcp.read_adc(6)
        time.sleep(0.05)
    return noise_sum / 100

AVG_sound = initNoise()
##############################################################

sensor = mpu6050(0x68)

while True:
    accel_data = sensor.get_accel_data()
    gyro_data = sensor.get_gyro_data()
    temperature = Adafruit_DHT.read_retry(temp_sensor,temp_pin)
    currentNoise = initNoise()
    sound = abs(currentNoise - AVG_sound)

    payload = {
        'name' : "final_niv_moriah",
        'temperature' : temperature[1] ,
        'noise' : sound ,
        'light' : mcp.read_adc(0) ,
        'proximity' : mcp.read_adc(5) ,
        'fire' : mcp.read_adc(4) ,
        'acc-x' : accel_data['x'],
        'acc-y' : accel_data['y'],
        'acc-z' : accel_data['z'],
        "time" : str(datetime.now().time())
    }
   ## print(topic)
    print(json.dumps(payload))
    try:
        myMQTTClient.publish(topic_name,json.dumps(payload),1)
    except:
        print("connection failure")
    time.sleep(float(interval))
