import socket
import utility
import threading
import MotorsController

class GamepadController(threading.Thread):
    def __init__(self, left_motor_forward_pin, left_motor_backward_pin, right_motor_forward_pin, right_motor_backward_pin, motors_pwm_freq, server_ip, server_port):
        self.SERVER_IP = server_ip
        self.SERVER_PORT = server_port
        #self.motors_controller = MotorsController.MotorsController(21, 20, 23, 24, 1000)
        self.motors_controller = MotorsController.MotorsController(left_motor_forward_pin, left_motor_backward_pin, right_motor_forward_pin, right_motor_backward_pin, motors_pwm_freq)
        threading.Thread.__init__(self)

    def run(self):
        serversock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serversock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        serversock.bind((self.SERVER_IP, self.SERVER_PORT))
        serversock.listen(1)

        print('Waiting for connections...')
        clientsock, client_address = serversock.accept()

        x_vector = [1, 1]

        while True:
            receive_control = clientsock.recv(2048).decode('utf-8').split(' ')

            print(receive_control)

            if len(receive_control[1]) != receive_control[1].find(',') + 1:
                continue

            command_type = receive_control[0]
            command_val = int(receive_control[1].rstrip(','))

            print(command_type + ' ' + str(command_val))

            if command_type == 'ABS_Y':
                if command_val >= 0:
                    self.motors_controller.change_motor_status(MotorsController.MotorSelection.LEFT_MOTOR, MotorsController.MotorRotationDirection.FORWARD, x_vector[0] * command_val / 4.0)
                    self.motors_controller.change_motor_status(MotorsController.MotorSelection.RIGHT_MOTOR, MotorsController.MotorRotationDirection.FORWARD, x_vector[1] * command_val / 4.0)
                else:
                    self.motors_controller.change_motor_status(MotorsController.MotorSelection.LEFT_MOTOR, MotorsController.MotorRotationDirection.BACKWARD, x_vector[0] * -command_val / 4.0)
                    self.motors_controller.change_motor_status(MotorsController.MotorSelection.RIGHT_MOTOR, MotorsController.MotorRotationDirection.BACKWARD, x_vector[1] * -command_val / 4.0)

            if command_type == 'ABS_RX':
                if command_val >= 0:
                    x_vector = [1.0, 1.0 - command_val / 4.0]
                else:
                    x_vector = [1.0 + command_val / 4.0, 1.0]


        serversock.close()
