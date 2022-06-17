import base64
import binascii
import os
import select
import struct
import sys
import socket
import signal
import getpass
import json
from argparse import ArgumentParser
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Cipher import PKCS1_v1_5
from Crypto.Hash import SHA,MD5
from Crypto.Cipher import AES
from Crypto import Random
import threading

from hxaDefinitions import *

import hxaServoControl
import hxaControlConverter

privateKeyPath = 'private.key'
publicKeyPath = 'public.key'
passwdPath = 'shadow'

END_MARKER = "\t\t\t"

# Process input options

def process_cmd_option(options):
    return options

# Get command line option

def get_cmd_option(argv):
    progname = os.path.basename(argv[0])
    parser = ArgumentParser(usage=progname, version='v1.0')
    parser.add_argument('-a', '--adduser', action='store', dest='user_name', help='Add new user\n')
    options = parser.parse_args(argv[1:])
    options = process_cmd_option(options)
    return options

def decryptAuthPrivate(buffer,key):
    cipher = PKCS1_v1_5.new(key)
    try:
        message = base64.b64decode(cipher.decrypt(buffer.decode('hex'),''))
    except ValueError:
        print("AUTH: PKCS1# v1.5 %s" % ValueError.message)
        return None
    if message == '':
        print("AUTH: Sentinel is empty, decryption error")
        return None
    return message

def encryptAuthPublicKey(message,key):
    cipher = PKCS1_OAEP.new(key)
    ciphertext = cipher.encrypt(message)
    return ciphertext

def createKeyAndIv(password,salt,nBits=128):
    key = None
    iv = None
    if nBits not in [128,192,256]:
        print("Key length must be 128, 192 or 256 bits!")
        return key,iv

    data00 = password + salt
    keyMaterials = [data00]
    #print("keyMaterials[%s] = %s" % (0,keyMaterials[0]))
    result = MD5.new(data00).hexdigest()
    for k in xrange(3):
        keyMaterials.append(result)
        result = MD5.new(result.decode('hex') + data00).hexdigest()
        #print("keyMaterials[%s] = %s" % (k+1,keyMaterials[k+1]))

    if nBits == 128:
        key = keyMaterials[1]
        iv = keyMaterials[2]
    elif nBits == 192:
        key = keyMaterials[1] + keyMaterials[2][:16]
        iv = keyMaterials[3]
    elif nBits == 256:
        key = keyMaterials[1] + keyMaterials[2]
        iv = keyMaterials[3]

    return key.decode('hex'),iv.decode('hex')

def decryptMessage(cipherText,password):
    try:
        decodeCipherText = base64.b64decode(cipherText)
        if decodeCipherText[:8] != "Salted__":
            return None
        salt = decodeCipherText[8:16]
        #print("Salt = %s" % salt.encode('hex'))
        key,iv = createKeyAndIv(password,salt)
        #print(" iv = %s\nkey = %s" % (iv.encode('hex'),key.encode('hex')))
        cipher = AES.new(key, AES.MODE_CBC, iv)
        text = cipher.decrypt(decodeCipherText[16:])
        #print "text = %s [%s]" % (text,len(text))
        #print("last byte = %d" % int(text[-1].encode('hex'),16))
        text = text[:-(int(text[-1].encode('hex'),16)+1)]
    except:
        print("Cannot decrypt message")
        return None
    else:
        return text

def encryptMessage(message,password):
    # Generate random salt
    salt = Random.new().read(8)
    # Calculate key and init. vector
    key,iv = createKeyAndIv(password,salt)
    # Create cipher object
    cipher = AES.new(key, AES.MODE_CBC, iv)
    # PKCS5 padding count
    charDiv = AES.block_size - ((len(message)+1) % AES.block_size)
    # 0xA0 padding + PKCS5 padding
    message += '\x0A' + struct.pack("%sB" % charDiv,*([charDiv]*charDiv))
    cipherText = cipher.encrypt(message)
    # Make result and return
    return base64.b64encode("Salted__" + salt + cipherText)

def CheckPasswd(auth):
    if os.path.exists(passwdPath):
        tmp = auth.split(':')
        username = tmp[0]
        passwd = tmp[1]
        with open(passwdPath,'r') as passwdFile:
            for line in passwdFile:
                #users = passwdFile.read()
                tmp = line.split(':')
                if username == tmp[0] and SHA.new(passwd).hexdigest() == tmp[1]:
                    #print("User login found: auth %s accepted" % username)
                    return 1
            return 0
    else:
        return 0

def sockRecvTimeout(comSocket,bufferSize=1024,timeout=100):
    # Timeout wait period in ms
    ready = select.select([comSocket], [], [], timeout)
    return comSocket.recv(bufferSize) if ready[0] else None

class hxaServer(object):
    def __init__(self,host,port):
        # Used to save current servo horns angles state
        self.currentControlBuffer = None

        # Initialize value converter
        self.Convert =  hxaControlConverter.hxaControlConverter()
        #default = [900,1200,1200,900,1150,1500,950,1100,1500,2200,2100,1300,2200,2100,1600,2200,2100,1500]
        #for (k,pulse) in enumerate(default):
            #sys.stdout.write("%s," % self.Convert.toAngle(servoIndexesList[k],pulse))
            #print("%3s: %7s -> %7s" % (servoIndexesList[k],pulse,self.Convert.toAngle(servoIndexesList[k],pulse)))
        #for pulse in range(500,2600,10): print("%7s -> %7s" % (pulse,self.Convert.toAngle("RLF",pulse)))
        #for angle in range(-900,901,1): print("%7s -> %7s" % (float(angle)/10.0,self.Convert.toControl("RLF",float(angle)/10.0)))
        #sys.exit(0)

        # Initializing USB servo driver
        try:
            self.hxaController = hxaServoControl.hxaServoControl(USB_PACKET_SIZE)
        except ValueError as e:
            print("ERROR: %s" % e)
            raise SystemExit

        # String values
        self.DeviceName = 'Hexapod Adamant'
        self.ServerName = 'hxaServer v.1'

        # Generate server key pairs (using only for authentication)
        self.AuthenticationKeysGenerate()

        # Stand up server
        self.comSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.comSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        #self.comSocket.setblocking(0)
        self.comSocket.bind((host,port))
        self.comSocket.listen(5)
        signal.signal(signal.SIGINT, self.KeyboardInterruptHandler)
        print("hxaServer[START] Server on %s:%s started" % (host,port))

    def AuthenticationKeysGenerate(self):
        if not (os.path.exists(publicKeyPath) and os.path.exists(privateKeyPath)):
            print("hxaServer[KEY  ] Generate authentication keys pair ...")
            self.privateKey = RSA.generate(1024)
            self.publicKey = self.privateKey.publickey()
            print("hxaServer[KEY  ] Save generated authentication keys")
            with open(privateKeyPath,'w') as privateKeyFile:
                privateKeyFile.write(self.privateKey.exportKey())
            with open(publicKeyPath,'w') as publicKeyFile:
                publicKeyFile.write(self.publicKey.exportKey())
        else:
            print("hxaServer[KEY  ] Load generated authentication keys")
            with open(privateKeyPath,'r') as privateKeyFile:
                self.privateKey = RSA.importKey(privateKeyFile.read())
            with open(publicKeyPath,'r') as publicKeyFile:
                self.publicKey = RSA.importKey(publicKeyFile.read())
                #print("%x" % self.publicKey.n)
                #print("%x" % self.publicKey.e)

    def AcceptConnection(self):
        while True:
            print("hxaServer[INFO ] Waiting for client connection")
            sock, addr = self.comSocket.accept()
            # Set timeout of receive/send operation in seconds
            sock.settimeout(2.0)
            print("hxaServer[INFO ] Client connected: %s:%s\n" % (addr[0],addr[1]))
            try:
                # Send greeting message
                sock.send("%s (%s)%s" % (self.DeviceName,self.ServerName,END_MARKER))
                # Send public key for authentication information and symmetric key
                sock.send(self.publicKey.exportKey())
                # Receive authentication information: username+password
                result = sock.recv(4096)
                #result = sockRecvTimeout(sock,1024)
                # Decrypt information using private key
                #print("%s" % encryptAuthPublicKey("test:test",self.publicKey))
                result = decryptAuthPrivate(result,self.privateKey)
                if result is None:
                    print("hxaServer[AUTH ] Cannot decrypt authentication information")
                    sock.send("FAIL")
                    sock.close()
                    continue
                # Checkout authentication info
                if not CheckPasswd(result):
                    print("hxaServer[AUTH ] User %s login failed" % result.split(':')[0])
                    # Response to client authentication failed
                    sock.send("FAIL")
                    sock.close()
                else:
                    print("hxaServer[AUTH ] User %s login accepted" % result.split(':')[0])
                    # Response to client authentication successful
                    sock.send("SUCCESS")
                    # Receive symmetric key from client
                    buf = sock.recv(4096)
                    print("hxaServer[AUTH ] Encrypted symmetric key info %s" % repr(buf))

                    # Decrypt key
                    SymmetricKeyData = decryptAuthPrivate(buf,self.privateKey)
                    if SymmetricKeyData is None:
                        print("hxaServer[AUTH ] Cannot decrypt session symmetric key password info")
                        sock.send("FAIL")
                        sock.close()
                        continue

                    print("hxaServer[AUTH ] Decrypted password string: %s" % SymmetricKeyData)

                    password,nBits = SymmetricKeyData.split("|")

                    try:
                        nBits = int(nBits)
                        if nBits not in [128,192,256]:
                            print("hxaServer[AUTH ] Symmetric key incorrect length: %s" % nBits)
                            raise ValueError
                    except ValueError as e:
                        print("hxaServer[AUTH ] Cannot get key length: %s" % e.message)
                        sock.send("FAIL")
                        sock.close()
                        continue

                    # After that we waiting command from client with out timeout
                    sock.settimeout(None)
                    while True:
                        # TODO: If client has been disconnected check it and quit
                        # Otherwise server is blocked...
                        buf = sock.recv(4096)
                        # Check client has been disconnected
                        if not buf:
                            print("hxaServer[WARN ] Client closed connection unexpected")
                            break

                        # Decrypt input message from client
                        message = decryptMessage(buf,password)
                        if message is None:
                            print("hxaServer[RECV ] MESSAGE CANNOT BE DECRYPTED")

                        print("hxaServer[RECV ] Decrypted message: %s" % message)

                        # HERE MAIN PROCESSING OF INPUT MESSAGE IS EXECUTING
                        isSessionClosed,response = self.ProcessReceivedMessage(message)

                        # Encrypt answer message and send it to client
                        sock.send(encryptMessage(response,password))

                        # Check if client want to disconnect, then close session
                        if isSessionClosed:
                            print("hxaServer[INFO ] Connection successfully closed")
                            break

                    # Close sock with current client
                    sock.close()
                    print("hxaServer[INFO ] Client %s has been disconnected" % addr[0])
            except socket.timeout:
                print("hxaServer[AUTH ] Client timeout occurred while authentication ... exit")
                sock.close()
                continue
            except socket.error:
                if e.errno in [32,104]:
                    print("hxaServer[WARN ] Client %s reset connection (Error = %s)" % (e.strerror,addr[0]))
                    pass
                elif e.errno == 4:
                    return
                else:
                    print("hxaServer[ERROR] Socket unknown exception: %s" % e)
                    raise

    # Servo control functionality

    def usbCmdGetControlValues(self):
        data = struct.pack('<B',USB_CMD_GET_CONTROL_VALUES)
        writeCount = self.hxaController.write(data)
        print("Send data [%s]: %s" % (writeCount,binascii.hexlify(data)))
        buf = self.hxaController.read(USB_PACKET_SIZE)
        if buf is not None:
            print("Received data: %s" % binascii.hexlify(buf))
            if buf[:3] == USB_UNKNOWN_SERVO_POSITION:
                print("Driver unknown current servo position")
                return None
            else:
                buf = buf[:SERVO_COUNT*2]
                print("Reading data: %s" % binascii.hexlify(buf))
                return list(struct.unpack('<%sH' % SERVO_COUNT,buf))
        else:
            print("Can't get current servo state ... ")
            return None

    def usbCmdSetControlValues(self,buf):
        data = struct.pack('<B%sH' % len(buf),USB_CMD_SET_CONTROL_VALUES,*buf)
        writeCount = self.hxaController.write(data)
        print("Send data [%s]: %s" % (writeCount,binascii.hexlify(data)))
        return writeCount

    def convertAnglesToControls(self,lastStateBuffer,listOfNames,listOfAngles):
        if listOfNames[0] == SERVO_ALL:
            result = SERVO_COUNT*[0]
            for k in range(SERVO_COUNT):
                result[k] = self.Convert.toControl(
                    servoIndexesList[k],listOfAngles[k])
        else:
            result = lastStateBuffer
            for (k,name) in enumerate(listOfNames):
                nameIndx = servoNamesList[name]
                result[nameIndx] = self.Convert.toControl(
                    name,listOfAngles[k])
        return result

    def convertControlsToAngles(self,currentStateBuffer,listOfNames):
        if listOfNames[0] == SERVO_ALL:
            result = SERVO_COUNT*[0.0]
            for k in range(SERVO_COUNT):
                result[k] = self.Convert.toAngle(
                    servoIndexesList[k],currentStateBuffer[k])
        else:
            result = len(listOfNames)*[0.0]
            for (k,name) in enumerate(listOfNames):
                nameIndx = servoNamesList[name]
                result[k] = self.Convert.toAngle(
                    name,currentStateBuffer[nameIndx])
        return result

    def ProcessReceivedMessage(self, message):

        errorTextMessage = "Received message can't be parsed"
        errorTextLength = "Length of servo names array and servo positions array are different"
        errorTextNames = "Servo names list length != 1, but SERVO_ALL specified"
        errorTextServo = "Unknown servo name"
        errorTextField = "Servo name or servo position field is absent"
        errorTextFloat = "All new servo positions must be floating type"
        errorTextLimit = "All new servo positions must be => %s <= %s" % (SERVO_ANGLE_MIN,SERVO_ANGLE_MAX)
        errorTextUnknown = "Unknown current servo horn positions"
        errorTextUSB = "USB servo driver not response while transmitting"
        responseTextOK = "Servos angular position changed successfully"
        errorTextCommand = "Received command is unknown"
        responseTextServoPosition = "Current servo position"

        # Trying to parse json string and return error if we can't
        try:
            result = json.loads(message)
        except ValueError:
            response = genErrorMessage(HXAS_ERROR_BAD_FORMAT,errorTextMessage)
            return False, response

        # Check if command field is exist
        if HXAS_JSON_CMD not in result:
            response = genErrorMessage(HXAS_ERROR_BAD_FORMAT,errorTextMessage)
            return False, response

        # Parse client disconnect command
        if result[HXAS_JSON_CMD] == HXAS_CMD_DISCONNECT:
            response = genResponseMessage("Session closed. Wait for new connections")
            return True, response
        # Parse client send text message to server
        elif result[HXAS_JSON_CMD] == HXAS_CMD_RESPONSE:
            if HXAS_JSON_MESSAGE not in result:
                response = genErrorMessage(HXAS_ERROR_BAD_FORMAT,errorTextMessage)
                return False, response
            print("Client send message: %s" % result[HXAS_JSON_MESSAGE])
            response = genResponseMessage("Message received")
            return False, response
        # Parse client send new angle position to servos
        elif result[HXAS_JSON_CMD] == HXAS_CMD_SET_ANGLE:
            # Check if we have all parameters for this command
            if HXAS_JSON_SERVO_NAME not in result or HXAS_JSON_SERVO_POS not in result:
                response = genErrorMessage(HXAS_ERROR_BAD_FORMAT,errorTextField)
                return False, response

            if SERVO_ALL in result[HXAS_JSON_SERVO_NAME]:
                if len(result[HXAS_JSON_SERVO_NAME]) != 1:
                    response = genErrorMessage(HXAS_ERROR_BAD_FORMAT,errorTextNames)
                    return False, response
                # Check if length of servo names count and servo positions count are equal
                if len(result[HXAS_JSON_SERVO_POS]) != SERVO_COUNT:
                    response = genErrorMessage(HXAS_ERROR_BAD_FORMAT,errorTextLength)
                    return False, response
            else:
                # Check if length of servo names count and servo positions count are equal
                if len(result[HXAS_JSON_SERVO_NAME]) != len(result[HXAS_JSON_SERVO_POS]):
                    response = genErrorMessage(HXAS_ERROR_BAD_FORMAT,errorTextLength)
                    return False, response
                    # Check if all servo names in received list is also in known servo names list
                if any(x not in servoNamesList for x in result[HXAS_JSON_SERVO_NAME]):
                    response = genErrorMessage(HXAS_ERROR_BAD_FORMAT,errorTextServo)
                    return False, response

            # Check if all new servo positions is float type
            if any(type(x) != float for x in result[HXAS_JSON_SERVO_POS]):
                response = genErrorMessage(HXAS_ERROR_BAD_FORMAT,errorTextFloat)
                return False, response
            # Check if all servo position is in the angle limits
            if any(x > SERVO_ANGLE_MAX or x < SERVO_ANGLE_MIN for x in result[HXAS_JSON_SERVO_POS]):
                response = genErrorMessage(HXAS_ERROR_BAD_FORMAT,errorTextLimit)
                return False, response

            # If not all servos position set, then we need to know positions of
            # others servos (that is not in command string).
            # Else we set new initial position for all servos
            if result[HXAS_JSON_SERVO_NAME][0] != SERVO_ALL:
                # If current state of servo horns is not set,
                # then try to query angles from USB servo driver
                #if self.currentControlBuffer is None:
                pos = self.usbCmdGetControlValues()
                if pos is not None:
                    self.currentControlBuffer = pos
                else:
                    response = genErrorMessage(HXAS_ERROR_STATE_UNK,errorTextUnknown)
                    return False, response

            # Using interpolation tables translate angles to pulse width
            # for all servos base on input values
            output = self.convertAnglesToControls(self.currentControlBuffer,
                result[HXAS_JSON_SERVO_NAME],result[HXAS_JSON_SERVO_POS])

            print("%s: Control pulse width %s" % (result[HXAS_JSON_CMD],output))

            # Send result buffer to USB servo driver
            writeCount = self.usbCmdSetControlValues(output)
            #writeCount = 1
            # If data send OK then change state of buffer
            if writeCount != 0:
                self.currentControlBuffer = output
                response = genResponseMessage(responseTextOK)
            else:
                response = genErrorMessage(HXAS_ERROR_USB_TRANSMIT,errorTextUSB)
            return False, response
        # Parse client send new angle position to servos
        elif result[HXAS_JSON_CMD] == HXAS_CMD_GET_ANGLE:
            if HXAS_JSON_SERVO_NAME not in result:
                response = genErrorMessage(HXAS_ERROR_BAD_FORMAT,errorTextField)
                return False, response

            if SERVO_ALL in result[HXAS_JSON_SERVO_NAME]:
                if len(result[HXAS_JSON_SERVO_NAME]) != 1:
                    response = genErrorMessage(HXAS_ERROR_BAD_FORMAT,errorTextNames)
                    return False, response
            else:
                if any(x not in servoNamesList for x in result[HXAS_JSON_SERVO_NAME]):
                    response = genErrorMessage(HXAS_ERROR_BAD_FORMAT,errorTextServo)
                    return False, response

            # If current state of servo horns is not set,
            # then try to query angles from USB servo driver
            #if self.currentControlBuffer is None:
            pos = self.usbCmdGetControlValues()
            if pos is not None:
                self.currentControlBuffer = pos
            else:
                response = genErrorMessage(HXAS_ERROR_STATE_UNK,errorTextUnknown)
                return False, response

            # Translate pulse width to angles
            output = self.convertControlsToAngles(
                self.currentControlBuffer,
                result[HXAS_JSON_SERVO_NAME])
            # Generate response in json format
            response = genResponseServoState(
                result[HXAS_JSON_SERVO_NAME],output,
                responseTextServoPosition)
            return False, response

        else:
            response = genErrorMessage(HXAS_ERROR_BAD_FORMAT,errorTextCommand)
            return False, response

    # Shutdown server

    def Shutdown(self):
        print("hxaServer[INFO ] Server shutdown ...")
        self.comSocket.shutdown(1)
        self.comSocket.close()

    def KeyboardInterruptHandler(self, signal, iframe):
        print("hxaServer[INFO ] CTRL+C pressed - command to terminate")
        self.Shutdown()
        return

import tornado.web
import tornado.websocket
import tornado.ioloop

class WebSocketHandler(tornado.websocket.WebSocketHandler):
    #def __init__(self,controlServerAddress,controlServerPort):
    def __init__(self, application, request, **kwargs):
        super(WebSocketHandler,self).__init__(application, request, **kwargs)
        self.comSocket = None
        self.controlServerInit = False
        self.receiverThreadStop = False
        self.threadReceiver = threading.Thread(target=self.comSocketReceiveHandler)
        self.threadReceiver.setDaemon(True)
        self.terminateFlag = False
        #self.controlServerAddress = controlServerAddress
        #self.controlServerPort = controlServerPort

    def comSocketReceiveHandler(self):
        while not self.receiverThreadStop:
            try:
                buf = self.comSocket.recv(4096)
                print("WebSocket[RECV ] < socket:    %s" % repr(buf))
                if buf.strip():
                    for x in buf.split(END_MARKER):
                        if not x.strip(): continue
                        print("WebSocket[SEND ] > websocket: %s" % repr(x))
                        self.write_message(x)
                else:
                    print("Websocket[WARN ] Control server close connection")
                    self.close()
                    return
            except socket.timeout:
                #print("WebSocket[INFO ] Message waiting timeout")
                pass
            except socket.error:
                print("Websocket[ERROR] %s : %s" % (e.strerror,e.errno))
                self.receiverThreadStop = True
                self.comSocket.close()
                self.terminateFlag = True
                self.close()
                return

    def open(self):
        print("WebSocket[INFO ] Opened")
        self.comSocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        try:
            #self.comSocket.connect((self.controlServerAddress,
            #                        self.controlServerPort))
            self.comSocket.connect(("localhost",28139))
        except socket.error:
            print("Websocket[ERROR] Can't connect to control daemon server")
            self.write_message(u"CONTROL_SERVER_NOT_RESPONSE")
            self.close()
            return
        self.write_message(u"CONNECT_OK")
        self.controlServerInit = True
        self.comSocket.settimeout(5.0)
        self.receiverThreadStop = False
        self.threadReceiver.start()


    def on_message(self, message):
        if message == "IS_INIT":
            response = u"TRUE" if self.controlServerInit else u"FALSE"
            self.write_message(response)
        else:
            if self.controlServerInit:
                # TODO: check that transmit is ok
                print("WebSocket[RECV ] < websocket: %s" % repr(message))
                if message.strip():
                    for x in message.split(END_MARKER):
                        if not x.strip(): continue
                        print("WebSocket[SEND ] > socket:    %s" % repr(x))
                        self.comSocket.send(x)
            else:
                self.write_message(u"CONTROL_SERVER_NOT_INITIALIZED")

    def on_close(self):
        print("WebSocket[INFO ] Stopping socket receiver thread ...")
        if not self.terminateFlag:
            self.receiverThreadStop = True
            self.threadReceiver.join()
            self.comSocket.close()
        else:
            self.terminateFlag = False

        self.controlServerInit = False
        print("WebSocket[INFO ] Closed")

def main():
    print("Parse command line options")
    options = get_cmd_option(sys.argv)
    if options is None : return -1

    if not options.user_name is None:
        passwd = getpass.getpass(prompt='Password for %s: ' % options.user_name)
        with open(passwdPath,'w') as passwdFile:
            passwdFile.write('%s:%s' % (options.user_name,SHA.new(passwd).hexdigest()))
        print("User has been added")
        return 0

    #server = hxaServer('192.168.1.33',28139)
    #server.AcceptConnection()

    server = hxaServer("localhost",28139)

    threadControlServer = threading.Thread(target=server.AcceptConnection)
    threadControlServer.setDaemon(True)
    threadControlServer.start()

    application = tornado.web.Application(
        handlers=[(r"/websocket",WebSocketHandler)],
        debug=True)
    application.listen(9050)
    io_loop = tornado.ioloop.IOLoop.instance()
    io_loop.start()

    return 0

if __name__ == '__main__':
    sys.exit(main())
