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

def readClientThread(conn, addr, devicesList):
    while True:
        try:
            buff = conn.recv(6)
            if len(buff) != 6 :
                continue
            deviceID = struct.unpack("I", buff[0:4])[0] 
            val = struct.unpack("H", buff[4:6])[0]
            if(deviceID in devicesList.keys()):
                if(val > devicesList[deviceID]['max'] or val < devicesList[deviceID]['min']):
                    buff  = struct.pack('H', devicesList[deviceID]['min'])
                    buff += struct.pack('H', devicesList[deviceID]['max'])
                    conn.send(buff)
                devicesList[deviceID]['val'] = val
                devicesList[deviceID]['run'] = 0
                devicesList[deviceID]['last'] = time.time()
            else:
                print str(deviceID) + " Connected"
        except:
            print "Breaking the Connection with: " + str(addr)
            break;
    conn.close()



def serverThread(host, port, devicesList):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    except socket.error, msg:
        print("Could not create socket. Error Code: ", str(msg[0]), "Error: ", msg[1])
        sys.exit(0)
    
    
    # bind socket
    try:
        s.bind((host, port))
        print("[-] Socket Bound to port " + str(PORT))
    except socket.error, msg:
        print("Bind Failed. Error Code: {} Error: {}".format(str(msg[0]), msg[1]))
        sys.exit()
    
    while True:
        s.listen(1)
        conn, addr = s.accept()
    
        start_new_thread(readClientThread, (conn, addr, devicesList))
    
    s.close()

def updateDefinitions(devicesList):
    try:
        datafile = open('definitions.json')
        data = json.load(datafile)
        for device in data['devices']:
            if not device['id'] in devicesList.keys():
                devicesList[device['id']] = {}
                devicesList[device['id']]['state'] = 0
                devicesList[device['id']]['fase'] = 0
                devicesList[device['id']]['faseNum'] = 2
                devicesList[device['id']]['val'] = 0
                devicesList[device['id']]['run'] = 0
                devicesList[device['id']]['last'] = 0
            devicesList[device['id']]['min'] = device['min']
            devicesList[device['id']]['max'] = device['max']
            devicesList[device['id']]['num'] = device['num']
            devicesList[device['id']]['pol'] = device['polarity']
        datafile.close()
    except:
        return
    
def checkLimits(devicesList, midiOut):
    for id in devicesList:
        if devicesList[id]['run'] == 0:
            val = devicesList[id]['val']
            if val < devicesList[id]['max']:
                if(devicesList[id]['state'] == 0):
                    if(devicesList[id]['pol'] == 0):
                        midiOut.send_message([0x90, 10*devicesList[id]['num'] + devicesList[id]['fase'], 112])
                    else:
                        midiOut.send_message([0x80, 10*devicesList[id]['num'] + devicesList[id]['fase'], 112])
                    devicesList[id]['state'] = 1
            else:
                if(devicesList[id]['state'] == 1):
                    if(devicesList[id]['pol'] == 0):
                        midiOut.send_message([0x80, 10*devicesList[id]['num'] + devicesList[id]['fase'], 112])
                    else:
                        midiOut.send_message([0x90, 10*devicesList[id]['num'] + devicesList[id]['fase'], 112])
                    devicesList[id]['state'] = 0
                    devicesList[id]['fase'] = devicesList[id]['fase'] + 1
                    if(devicesList[id]['fase'] >= devicesList[id]['faseNum']):
                        devicesList[id]['fase'] = 0
            devicesList[id]['run'] = 1

def printDevices(devicesList):
    print '\n'*1000
    print '-'*(54+15)
    print '{:^10s} | {:^10s} | {:^10s} | {:^4s} | {:^10s} | {:^10s}'.format("id", 'Connected', 'Value', 'Fase', 'Min', 'Max')
    print '-'*(54+15)
    for id in devicesList:
        device = devicesList[id]
        if(time.time() - device['last']) > 10:
            state = 'Offline'
            color = '\033[93m'
        else:
            state = 'Online'
            color = '\033[92m'
        print color + '{:^10d} | {:^10s} | {:^10d} | {:^4d} | {:^10d} | {:^10d}'.format(id, state, device['val'], device['fase'], device['min'], device['max']) + '\033[0m'
        print '-'*(54+15)


stateList = {}
valList   = {}
devicesList = {}
midiOut = initRtmidi()
start_new_thread(serverThread, (HOST, PORT, devicesList))
while 1:
    printDevices(devicesList)
    updateDefinitions(devicesList)
    checkLimits(devicesList, midiOut)
    time.sleep(0.1)
