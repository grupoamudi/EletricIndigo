import socket
import time
import sys
import struct
import json
from thread import start_new_thread

HOST = '' # all availabe interfaces
PORT = 9999 # arbitrary non privileged port 

def readClientThread(conn, addr, valList, limitList):
    while True:
        try:
            buff = conn.recv(6)
            if len(buff) != 6 :
                print len(buff)
                continue
            deviceID = struct.unpack("I", buff[0:4])[0] 
            val = struct.unpack("H", buff[4:6])[0]
            if(deviceID in limitList.keys()):
                if(val > limitList[deviceID]['max'] or val < limitList[deviceID]['min']):
                    buff  = struct.pack('H', limitList[deviceID]['min'])
                    buff += struct.pack('H', limitList[deviceID]['max'])
                    conn.send(buff)
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
            limitList[device['id']]['min'] = device['min']
            limitList[device['id']]['max'] = device['max']
        datafile.close()
    except:
        return
    
def checkLimits(limitList, valList, stateList, midiOut):
    for id in valList:
        val = valList[id]
        if not id in stateList:
            stateList[id] = 0
        if val > 0:
            if val < 2000:
                if(stateList[id] == 0):
                    #midiOut.send_message([0x90, 120, 112])
                    stateList[id] = 1
                    print val
            else:
                if(stateList[id] == 1):
                    #midiOut.send_message([0x90, 60, 112])
                    stateList[id] = 0
                    print val
        valList[id] = -1;

stateList = {}
valList   = {}
limitList = {}
midiOut = []
start_new_thread(serverThread, (HOST, PORT, valList, limitList))
while 1:
    updateDefinitions(limitList)
    checkLimits(limitList, valList, stateList, midiOut)
    time.sleep(0.1)
