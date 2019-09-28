import socket
import utility
import threading
import MotorsController

class GamepadController(threading.Thread):
    def __init__(self, left_motor_forward_pin, left_motor_backward_pin, right_motor_forward_pin, right_motor_backward_pin, motors_pwm_freq, server_ip, server_port):
        print("GamepadController __init__")
        self.SERVER_IP = server_ip
        self.SERVER_PORT = server_port
        self.LEFT_MOTOR_FORWARD_PIN = left_motor_forward_pin
        self.LEFT_MOTOR_BACKWARD_PIN = left_motor_backward_pin
        self.RIGHT_MOTOR_FORWARD_PIN = right_motor_forward_pin
        self.RIGHT_MOTOR_BACKWARD_PIN = right_motor_backward_pin
        self.MOTORS_PWM_FREQ = motors_pwm_freq
        threading.Thread.__init__(self)

    def __del__(self):
        print("GamepadController __del__")

    def run(self):
        serversock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serversock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        serversock.bind((self.SERVER_IP, self.SERVER_PORT))
        serversock.listen(1)

        clientsock, client_address = serversock.accept()

        x_vector = [1, 1]
        motors_controller = MotorsController.MotorsController(self.LEFT_MOTOR_FORWARD_PIN, self.LEFT_MOTOR_BACKWARD_PIN, self.RIGHT_MOTOR_FORWARD_PIN, self.RIGHT_MOTOR_BACKWARD_PIN, self.MOTORS_PWM_FREQ)

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
                    motors_controller.change_motor_status(MotorsController.MotorSelection.LEFT_MOTOR, MotorsController.MotorRotationDirection.FORWARD, x_vector[0] * command_val / 4.0)
                    motors_controller.change_motor_status(MotorsController.MotorSelection.RIGHT_MOTOR, MotorsController.MotorRotationDirection.FORWARD, x_vector[1] * command_val / 4.0)
                else:
                    motors_controller.change_motor_status(MotorsController.MotorSelection.LEFT_MOTOR, MotorsController.MotorRotationDirection.BACKWARD, x_vector[0] * -command_val / 4.0)
                    motors_controller.change_motor_status(MotorsController.MotorSelection.RIGHT_MOTOR, MotorsController.MotorRotationDirection.BACKWARD, x_vector[1] * -command_val / 4.0)

            if command_type == 'ABS_RX':
                if command_val >= 0:
                    x_vector = [1.0, 1.0 - command_val / 4.0]
                else:
                    x_vector = [1.0 + command_val / 4.0, 1.0]


        serversock.close()

if __name__ == '__main__':
    gc = GamepadController(21, 20, 23, 24, 1000, "127.0.0.1", 8000)
    gc.start()
