from enum import Enum
import RPi.GPIO as GPIO
import time

class MotorRotationDirection(Enum):
    FORWARD = 0
    BACKWARD = 1

class Motor:
    def __init__(self, forward_pin, backward_pin, pwm_freq):
        print("Motor __init__")
        self.FORWARD_PIN = forward_pin
        self.BACKWARD_PIN = backward_pin
        self.PWM_FREQ = pwm_freq
        GPIO.setmode(GPIO.BCM)
        GPIO.setup([self.FORWARD_PIN, self.BACKWARD_PIN], GPIO.OUT)
        GPIO.output([self.FORWARD_PIN, self.BACKWARD_PIN], GPIO.LOW)
        self.forward_pwm = GPIO.PWM(self.FORWARD_PIN, self.PWM_FREQ)
        self.backward_pwm = GPIO.PWM(self.BACKWARD_PIN, self.PWM_FREQ)
        self.forward_pwm.start(0)
        self.backward_pwm.start(0)

    def __del__(self):
        print("Motor __del__")
        self.forward_pwm.stop()
        self.backward_pwm.stop()

    def change_status(self, direction, speed):
        if direction == MotorRotationDirection.FORWARD:
            self.forward_pwm.ChangeDutyCycle(int(speed * 100))
            self.backward_pwm.ChangeDutyCycle(0)
        elif direction == MotorRotationDirection.BACKWARD:
            self.forward_pwm.ChangeDutyCycle(0)
            self.backward_pwm.ChangeDutyCycle(int(speed * 100))

class MotorSelection(Enum):
    LEFT_MOTOR = 0
    RIGHT_MOTOR = 1

class MotorsController:
    def __init__(self, left_motor_forward_pin, left_motor_backward_pin, right_motor_forward_pin, right_motor_backward_pin, motors_pwm_freq):
        print("MotorsController __init__")
        self.left_motor = Motor(left_motor_forward_pin, left_motor_backward_pin, motors_pwm_freq)
        self.right_motor = Motor(right_motor_forward_pin, right_motor_backward_pin, motors_pwm_freq)

    def __del__(self):
        print("MotorsController __del__")
        GPIO.cleanup()

    def change_motor_status(self, motor_selection, direction, speed):
        if motor_selection == MotorSelection.LEFT_MOTOR:
            self.left_motor.change_status(direction, speed)
        elif motor_selection == MotorSelection.RIGHT_MOTOR:
            self.right_motor.change_status(direction, speed)

    def change_motors_status(self, direction, speed):
        self.left_motor.change_status(direction, speed)
        self.right_motor.change_status(direction, speed)

if __name__ == '__main__':
    mc = MotorsController(21, 20, 23, 24, 1000)
