import socket
import time
import sys
import struct
import json
from thread import start_new_thread
import rtmidi
import platform

HOST = '' # all availabe interfaces
PORT = 9999 # arbitrary non privileged port 

def initRtmidi():
    midiout = rtmidi.MidiOut()
    if(platform.platform().find("Linux") != -1):
        midiout.open_port(0)
    elif(platform.platform().find("Windows") != -1):
        midiout.open_port(1)
    else:
        midiout.open_port(0)
    return midiout;

def readClientThread(conn, addr, valList, limitList):
    while True:
        try:
            buff = conn.recv(6)
            if len(buff) != 6 :
                print len(buff)
                continue
            deviceID = struct.unpack("I", buff[0:4])[0] 
            val = struct.unpack("H", buff[4:6])[0]
            print str(deviceID) + ": " + str(val)
            if(deviceID in limitList.keys()):
                if(val > limitList[deviceID]['max'] or val < limitList[deviceID]['min']):
                    buff  = struct.pack('H', limitList[deviceID]['min'])
                    buff += struct.pack('H', limitList[deviceID]['max'])
                    conn.send(buff)
            if not (deviceID in valList):
                print str(deviceID) + " Connected"
            valList[deviceID] = val
        except:
            print "Breaking the Connection with: " + str(addr)
            break;
    conn.close()



def serverThread(host, port, valList, limitList):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    except socket.error, msg:
        print("Could not create socket. Error Code: ", str(msg[0]), "Error: ", msg[1])
        sys.exit(0)
    
    print("[-] Socket Created")
    
    # bind socket
    try:
        s.bind((host, port))
        print("[-] Socket Bound to port " + str(PORT))
    except socket.error, msg:
        print("Bind Failed. Error Code: {} Error: {}".format(str(msg[0]), msg[1]))
        sys.exit()
    
    print("Listening...")
    while True:
        s.listen(1)
        conn, addr = s.accept()
        print("[-] Connected to " + addr[0] + ":" + str(addr[1]))
    
        start_new_thread(readClientThread, (conn, addr, valList, limitList))
    
    s.close()

def updateDefinitions(limitList):
    try:
        datafile = open('definitions.json')
        data = json.load(datafile)
        for device in data['devices']:
            if not device['id'] in limitList.keys():
                limitList[device['id']] = {}
                limitList[device['id']]['state'] = 0
                limitList[device['id']]['stateNum'] = 2
            limitList[device['id']]['min'] = device['min']
            limitList[device['id']]['max'] = device['max']
            limitList[device['id']]['num'] = device['num']
            limitList[device['id']]['pol'] = device['polarity']
        datafile.close()
    except:
        return
    
def checkLimits(limitList, valList, stateList, midiOut):
    for id in valList:
        val = valList[id]
        if not id in stateList:
            stateList[id] = limitList[id]['pol']
        if val >= 0:
            if val < limitList[id]['max']:
                if(stateList[id] == 0):
                    if(limitList[id]['pol'] == 0):
                        midiOut.send_message([0x90, 10*limitList[id]['num'] + limitList[id]['state'], 112])
                    else:
                        midiOut.send_message([0x80, 10*limitList[id]['num'] + limitList[id]['state'], 112])
                    stateList[id] = 1
                    print val
            else:
                if(stateList[id] == 1):
                    if(limitList[id]['pol'] == 0):
                        midiOut.send_message([0x80, 10*limitList[id]['num'] + limitList[id]['state'], 112])
                    else:
                        midiOut.send_message([0x90, 10*limitList[id]['num'] + limitList[id]['state'], 112])
                    stateList[id] = 0
                    limitList[id]['state'] = limitList[id]['state'] + 1
                    if(limitList[id]['state'] >= limitList[id]['stateNum']):
                        limitList[id]['state'] = 0
                    print str(id) + " State:" +  str(limitList[id]['state'])
                    print val
        valList[id] = -1;

stateList = {}
valList   = {}
limitList = {}
midiOut = initRtmidi()
start_new_thread(serverThread, (HOST, PORT, valList, limitList))
while 1:
    updateDefinitions(limitList)
    checkLimits(limitList, valList, stateList, midiOut)
    time.sleep(0.1)
