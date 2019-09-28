import sys
import socket
from inputs import get_gamepad
import configparser

config = configparser.ConfigParser()
config.read('./settings.ini')

host = sys.argv[1]
port = int(config.get('gamepad', 'port'))

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((host, port))

COORDINATE_MAX = 32767
prev_y = 0
prev_x = 0
partition_number = 4
operable_list = ["ABS_Y", "ABS_RX", "BTN_NORTH", "BTN_WEST", "BTN_SOUTH", "BTN_EAST", "BTN_TR"]

while True:
    events = get_gamepad()
    for event in events:
        if  event.code in operable_list:
            button_type = event.code
            button_flag = event.state
            
            if event.code in ['ABS_Y', 'ABS_RX']:
                button_flag = int(max(event.state, -COORDINATE_MAX) / (COORDINATE_MAX / partition_number))
                
                if event.code == 'ABS_Y':
                    if button_flag == prev_y:
                        continue
                    prev_y = button_flag
                
                if event.code == 'ABS_RX':
                    if button_flag == prev_x:
                        continue
                    prev_x = button_flag

            client.send((button_type + ' ' + str(button_flag) + ',').encode('utf-8'))
