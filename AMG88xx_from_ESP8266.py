"""
Python MQTT Subscription client - No Username/Password
Thomas Varnish (https://github.com/tvarnish), (https://www.instructables.com/member/Tango172)
Written for my Instructable - "How to use MQTT with the Raspberry Pi and ESP8266"
"""
import paho.mqtt.client as mqtt
from Adafruit_AMG88xx import Adafruit_AMG88xx
import pygame
import os
import math
import time
import random

import numpy as np
from scipy.interpolate import griddata

from colour import Color

rcvd_index = 0
pixels_rx = []

# Don't forget to change the variables for the MQTT broker!
mqtt_topic = "esp8266"
mqtt_broker_ip = "192.168.0.12"

#low range of the sensor (this will be blue on the screen)
MINTEMP = 26

#high range of the sensor (this will be red on the screen)
MAXTEMP = 32

#how many color values we can have
COLORDEPTH = 1024

client = mqtt.Client()
os.putenv('SDL_FBDEV', '/dev/fb1')
pygame.init()

points = [(math.floor(ix / 8), (ix % 8)) for ix in range(0, 64)]
grid_x, grid_y = np.mgrid[0:7:32j, 0:7:32j]

#sensor is an 8x8 grid so lets do a square
height = 240
width = 240

#the list of colors we can choose from
blue = Color("indigo")
colors = list(blue.range_to(Color("red"), COLORDEPTH))

#create the array of colors
colors = [(int(c.red * 255), int(c.green * 255), int(c.blue * 255)) for c in colors]

displayPixelWidth = width / 30
displayPixelHeight = height / 30

lcd = pygame.display.set_mode((width, height))

lcd.fill((255,0,0))
pygame.display.set_caption('AMG88xx')
#pygame.display.update()
pygame.display.flip()
pygame.mouse.set_visible(False)

lcd.fill((0,0,0))
pygame.display.update()

#some utility functions
def constrain(val, min_val, max_val):
    return min(max_val, max(min_val, val))

def map(x, in_min, in_max, out_min, out_max):
  return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

def updateScreen():
    global pixels_rx

    pixels = [map(p, MINTEMP, MAXTEMP, 0, COLORDEPTH - 1) for p in pixels_rx]

    #perdorm interpolation
    bicubic = griddata(points, pixels, (grid_x, grid_y), method='cubic')

    #draw everything
    for ix, row in enumerate(bicubic):
        for jx, pixel in enumerate(row):
            pygame.draw.rect(lcd, colors[constrain(int(pixel), 0, COLORDEPTH- 1)], (displayPixelHeight * ix, displayPixelWidth * jx, displayPixelHeight, displayPixelWidth))

    pygame.display.update()


# These functions handle what happens when the MQTT client connects
# to the broker, and what happens then the topic receives a message
def on_connect(client, userdata, flags, rc):
    # rc is the error code returned when connecting to the broker
    print "Connected!", str(rc)
    pixels_rx = []
    # Once the client has connected to the broker, subscribe to the topic
    client.subscribe(mqtt_topic)
    
def on_message(client, userdata, msg):
    global rcvd_index
    global pixels_rx
    # This function is called everytime the topic is published to.
    # If you want to check each message, and do something depending on
    # the content, the code to do this should be run in this function
    
    #print "Topic: ", msg.topic + "\nMessage: " + str(msg.payload)
    
    # The message itself is stored in the msg variable
    # and details about who sent it are stored in userdata
    pixels_rx.append(float(msg.payload))
    #print "pixels_rx[" , rcvd_index ,"] = ", pixels_rx[rcvd_index]
    rcvd_index+=1
    if rcvd_index == 64:
        rcvd_index = 0
        updateScreen()
        pixels_rx = []
            

# Here, we are telling the client which functions are to be run
# on connecting, and on receiving a message
client.on_connect = on_connect
client.on_message = on_message

# Once everything has been set up, we can (finally) connect to the broker
# 1883 is the listener port that the MQTT broker is using
client.connect(mqtt_broker_ip, 1883)

# Once we have told the client to connect, let the client object run itself
client.loop_forever()
client.disconnect()
