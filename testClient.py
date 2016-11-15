#!/usr/bin/env python

import socket
import time
import struct 
import random

TCP_IP = '127.0.0.1'
TCP_PORT = 9999

FAST_WAIT_TIME = 0.1
SLOW_WAIT_TIME = 5

val = 13
while 1:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((TCP_IP, TCP_PORT))
        s.settimeout(0.05)
        connInfo = s.getsockname()
        fakeID = int(connInfo[0].replace('.','')) + connInfo[1]
        print fakeID
        limits = [0, pow(2,16)]
        lastSend = time.time()
        while 1:
            if (val >= limits[0] and val <= limits[1]):
                waitTime = FAST_WAIT_TIME
            else:
                waitTime = SLOW_WAIT_TIME
            if(time.time() - lastSend) > waitTime:
                buff = struct.pack("I", fakeID)
                buff = buff + struct.pack("H", val) 
                s.send(buff)
                lastSend = time.time()
                try:
                    buff = s.recv(4)
                except:
                    buff = ''
                if len(buff) == 4:
                    limits[0] = struct.unpack('H',buff[0:2])[0]
                    limits[1] = struct.unpack('H',buff[2:4])[0]
                    print limits

            val += int(random.random()*20 - 10)
            if val < 0:
                val = 0
        s.close()
    except:
        print 'ERROR'
        time.sleep(2)
