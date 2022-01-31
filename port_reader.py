#!/usr/bin/python3
import os
import sys
import glob
from collections import namedtuple
import pyudev #That could be the best way how to find out usb serial port.
import random
import serial
Readed = namedtuple("Readed", "x_data y_data z_data")

class Reader:
    def list_serial_ports(self):
        #Just for debug. Generate random data option.
        available = ['Test']
        name = os.uname()
        if name[0] == "Windows":
            #Scan for available ports.
            for port in range(256):
                if self.check_if_plugged(port):
                    available.append(port)
            return available
        elif name[0] == "Linux":
            #I am not sure, if this will work. So if it will not, uncomment code under.
            context = pyudev.Context()
            for device in context.list_devices(subsystem='tty', ID_BUS='usb'):
                if device.is_initialized:
	                available.append(device.device_path)
            #for port in glob.glob('/dev/tty*'):
            #    if self.check_if_plugged(port):
            #        available.append(port)
            return available
        return None

    #Try to open serial port to figure out if is plugged.
    def check_if_plugged(self, port):
        try:
            sr_p = serial.Serial(port)
            sr_p.close()
            return True
        except serial.SerialException:
            return False

    def read_chunk_from_port(self, usb_name):
        size_of_char = sys.getsizeof(',')
        #Tried with and without the last 3 parameters
        self.data_for_graphs = []
        try:
            ser = serial.Serial(usb_name)
        except:
            #Permission denied error.
            return None

        #Find start of data frame. Destroy all data before * char.
        header_char = str(ser.read(size_of_char))
        while header_char != '*':
            header_char = str(ser.read(size_of_char))

        x_y_z = []
        #Read until we have data for all graphs
        while len(self.data_for_graphs) != 3:
            float_number_str = '' #Stored in string because, matplotlib takes only string or int.
            while True:
                char = str(ser.read(size_of_char))
                if char == ',' or '\n': #If delimeter or end of data frame
                    break
                #If the char is wrong in context of float (ie. a,$).
                #In float is allowed only . char and digits.
                elif char != '.' or ord(char) < ord('0') or ord(char) > ('9'):
                    float_number_str = '0' #Replace corrupted value with zero
                    break
                #Else append digit to float.
                else:
                    float_number_str = float_number_str + char

            if float_number_str == '': #If value is empty
                float_number_str = '0' #Replace corrupted value with zero

            x_y_z.__add__(float_number_str)
            if len(x_y_z) == 3:
                #If the data frame is complete("*%f,%f....%f/n")
                self.data_for_graphs.append(Readed(x_y_z[0], x_y_z[1], x_y_z[2]))
                x_y_z = []
                
        return self.data_for_graphs

    def generate_random_data(self):
        random_data = []
        for i in range(0, 3):
            random_data.append(Readed(random.randint(-100, 200),\
                    random.randint(-100, 200), random.randint(-100, 200)))
        return random_data
