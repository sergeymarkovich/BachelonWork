#Provides an interface to USB Hexapod Adamantine Class devices.

import binascii
import usb.core
from usb.core import USBError
import usb.util
import sys
import time
import struct

HXA_VENDOR_ID = 0x0483
HXA_PRODUCT_ID = 0x02F0

class hxaServoControl(object):
    def __init__(self, packet_size):
        
        """
        __init__(self) -> None
        Initialize the device.
        """

        self.packet_size = packet_size

        print("Initialize Servomotors controller...")

        # print all connected devices
        print("Connected USB devices:")
        usbDeviceList = usb.core.find(find_all=True)
        for device in usbDeviceList:
            try:
                name = usb.util.get_string(device,device.iProduct)
            except usb.core.USBError:
                name = "Can't get USB device name"
            finally:
                print("%04X:%04X -> %s" % (device.idVendor,device.idProduct,name))
        print("="*60)
        # find our device
        self.__usbDev = usb.core.find(idVendor=HXA_VENDOR_ID, idProduct=HXA_PRODUCT_ID)

        if self.__usbDev is None:
            print("Device %04X:%04X not found." % (HXA_VENDOR_ID,HXA_PRODUCT_ID))
            raise ValueError('Servomotors controller device not found')

        self.Manufacturer = usb.util.get_string(self.__usbDev,self.__usbDev.iManufacturer)
        self.Product = usb.util.get_string(self.__usbDev,self.__usbDev.iProduct)
        self.SerialNumber = usb.util.get_string(self.__usbDev,self.__usbDev.iSerialNumber)

        print("%s %s %s" % (self.Manufacturer,self.Product,self.SerialNumber))

        # set the active configuration. With no arguments, the first
        # configuration will be the active one
        self.__usbDev.set_configuration()

        # get an endpoint instance
        self.__usbConf = self.__usbDev.get_active_configuration()
        interface_number = self.__usbConf[(0,0)].bInterfaceNumber

        self.__usbInf = usb.util.find_descriptor(self.__usbConf,
            bInterfaceNumber = interface_number)

        print("Configure USB endpoints:")
        # match the first OUT endpoint
        self.__usbOut = usb.util.find_descriptor(
            self.__usbInf,
            custom_match = \
            lambda e: \
                usb.util.endpoint_direction(e.bEndpointAddress) == \
                usb.util.ENDPOINT_OUT
        )
        if self.__usbOut is None:
            ValueError('Servomotors controller output endpoint not found')
        print("OUTPUT EP Address = 0x%02X" %
            self.__usbOut.bEndpointAddress)

        # match the first IN endpoint
        self.__usbIn = usb.util.find_descriptor(
            self.__usbInf,
            custom_match = \
            lambda e: \
                usb.util.endpoint_direction(e.bEndpointAddress) == \
                usb.util.ENDPOINT_IN
        )
        if self.__usbIn is None:
            ValueError('Servomotors controller input endpoint not found')
        print("INPUT EP Address = 0x%02X" %
            self.__usbIn.bEndpointAddress)

        print("Device intialize successfully...")

    def __del__(self):
        try:
            self.__usbDev.releaseInterface(self.__usbInf)
            del self.__usbDev
        except:
            pass

    def softReset(self, timeout = 100):
        """
        softReset(timeout = 100) -> None
            Request flushes all buffers and resets the Bulk OUT
            and Bulk IN pipes to their default states.
            timeout: the operation timeout.
        """
        self.__usbDev.ctrl_transfer(bmRequestType = 0x21, bRequest = 2,
            wValue = 0, wIndex = self.__usbInf, data_or_wLength = 0)

    def write(self, buffer, timeout = 100):
        """
        write(buffer, timeout = 100) -> written
        Write data to printer.
            buffer: data buffer.
            timeout: operation timeout.
        """
        try:
            writeCount = self.__usbOut.write(buffer,timeout)
            #readOut = self.__usbIn.read(self.packet_size,timeout).tostring()[0]
            #print("USB Device write response: %s" % binascii.hexlify(readOut))
        except USBError:
            print("Error writing USB [%s]: %s" % (e.errno,e.strerror))
            writeCount = 0
        return writeCount

    def read(self, numbytes, timeout = 100):
        """
        read(numbytes, timeout = 100) -> data
        Read data from printer.
            numbytes: number of bytes to read.
            timeout: operation timeout.
        """
        try:
            # Output is an array.array(), so translate it into string
            readOut = self.__usbIn.read(self.packet_size,timeout).tostring()
        except USBError:
            print("Error reading USB [%s]: %s" % (e.errno,e.strerror))
            readOut = None
        if readOut is not None:
            readOut = readOut[:numbytes]
            #print("USB receive data: %s" % binascii.hexlify(readOut))
        return readOut
