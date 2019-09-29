import socket
import utility
import threading
import configparser
import MotorsController

class GamepadController(threading.Thread):
    def __init__(self, left_motor_forward_pin, left_motor_backward_pin, right_motor_forward_pin, right_motor_backward_pin, motors_pwm_freq, server_ip, server_port):
        print("GamepadController __init__")
        self.SERVER_IP = server_ip
        self.SERVER_PORT = int(server_port)
        self.LEFT_MOTOR_FORWARD_PIN = int(left_motor_forward_pin)
        self.LEFT_MOTOR_BACKWARD_PIN = int(left_motor_backward_pin)
        self.RIGHT_MOTOR_FORWARD_PIN = int(right_motor_forward_pin)
        self.RIGHT_MOTOR_BACKWARD_PIN = int(right_motor_backward_pin)
        self.MOTORS_PWM_FREQ = int(motors_pwm_freq)
        threading.Thread.__init__(self)

    def __del__(self):
        print("GamepadController __del__")

    def run(self):
        # ログ表示用インデント
        INDENT = '    '

        # モーター制御用
        x_vector = [1, 1]
        motors_controller = MotorsController.MotorsController(self.LEFT_MOTOR_FORWARD_PIN, self.LEFT_MOTOR_BACKWARD_PIN, self.RIGHT_MOTOR_FORWARD_PIN, self.RIGHT_MOTOR_BACKWARD_PIN, self.MOTORS_PWM_FREQ)

        while(True):
            try:
                # サーバーソケット生成
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
                    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    server_sock.bind((self.SERVER_IP, self.SERVER_PORT))
                    server_sock.listen(1)

                    # サーバ情報表示
                    print('GamepadController Server {')
                    print(INDENT + 'IP   : {},'.format(self.SERVER_IP))
                    print(INDENT + 'PORT : {}'.format(self.SERVER_PORT))
                    print('}')

                    # クライアント接続
                    client_sock, client_addr = server_sock.accept()
                    with client_sock:

                        # クライアント情報表示
                        print('GamepadController Client {')
                        print(INDENT + 'IP   : {},'.format(client_addr[0]))
                        print(INDENT + 'PORT : {}'.format(client_addr[1]))
                        print('}')

                        while True:
                            # 操作情報取得
                            receive_control = client_sock.recv(2048).decode('utf-8').split(' ')

                            if not receive_control: break

                            # 操作情報表示
                            print('GamepadController Command {')
                            print(INDENT + 'Type : {}'.format(receive_control[0]))
                            print(INDENT + 'Value: {}'.format(receive_control[1]))
                            print('}')

                            # 複数のコマンドが連結されていた場合は操作を拒否
                            if len(receive_control[1]) != receive_control[1].find(',') + 1:
                                continue

                            # 操作情報をもとにモーターを制御
                            command_type = receive_control[0]
                            command_val = int(receive_control[1].rstrip(','))

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
            except:
                pass

if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('./settings.ini', 'UTF-8')
    gamepad_controller = GamepadController(21, 20, 23, 24, 1000, utility.get_server_ip(), config.get('gamepad', 'port'))
    gamepad_controller.start()
    gamepad_controller.join()
