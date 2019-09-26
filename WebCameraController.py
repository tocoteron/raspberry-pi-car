# coding:utf-8
import threading
import socket
import numpy as np
import cv2
import time
import configparser

class WebCameraController(threading.Thread):
    def __init__(self, camera_id, camera_fps, camera_width, camera_height, server_ip, server_port, header_size, image_width, image_height, image_quality):
        self.CAMERA_ID = camera_id
        self.CAMERA_FPS = camera_fps
        self.CAMERA_WIDTH = camera_width
        self.CAMERA_HEIGHT = camera_height
        self.SERVER_IP = server_ip
        self.SERVER_PORT = server_port
        self.HEADER_SIZE = header_size
        self.IMAGE_WIDTH = image_width
        self.IMAGE_HEIGHT = image_height
        self.IMAGE_QUALITY = image_quality
        threading.Thread.__init__(self)

    def run(self):
        # 設定
        FPS = 30
        INDENT = '    '

        # カメラ設定適用
        cam = cv2.VideoCapture(self.CAMERA_ID)
        cam.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'));
        cam.set(cv2.CAP_PROP_FPS, self.CAMERA_FPS)
        cam.set(cv2.CAP_PROP_FRAME_WIDTH, self.CAMERA_WIDTH)
        cam.set(cv2.CAP_PROP_FRAME_HEIGHT, self.CAMERA_HEIGHT)

        # カメラ情報表示
        print('Camera {')
        print(INDENT + 'ID    : {},'.format(self.CAMERA_ID))
        print(INDENT + 'FORMAT: {},'.format(cam.get(cv2.CAP_PROP_FOURCC)))
        print(INDENT + 'FPS   : {},'.format(cam.get(cv2.CAP_PROP_FPS)))
        print(INDENT + 'WIDTH : {},'.format(cam.get(cv2.CAP_PROP_FRAME_WIDTH)))
        print(INDENT + 'HEIGHT: {}'.format(cam.get(cv2.CAP_PROP_FRAME_HEIGHT)))
        print('}')

        # サーバ情報表示
        print('Server {')
        print(INDENT + 'IP   : {},'.format(self.SERVER_IP))
        print(INDENT + 'PORT : {}'.format(self.SERVER_PORT))
        print('}')

        # クライアントに接続
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.SERVER_IP, self.SERVER_PORT))
        s.listen(1)
        soc, addr = s.accept()

        # クライアント情報表示
        print('Client {')
        print(INDENT + 'IP   : {},'.format(addr[0]))
        print(INDENT + 'PORT : {}'.format(addr[1]))
        print('}')

        # メインループ
        while True:
            loop_start_time = time.time()

            # 送信用画像データ作成
            flag, img = cam.read()
            resized_img = cv2.resize(img, (self.IMAGE_WIDTH, self.IMAGE_HEIGHT))
            (status, encoded_img) = cv2.imencode('.jpg', resized_img, [int(cv2.IMWRITE_JPEG_QUALITY), self.IMAGE_QUALITY])

            # パケット構築
            packet_body = encoded_img.tostring()
            packet_header = len(packet_body).to_bytes(self.HEADER_SIZE, 'big') 
            packet = packet_header + packet_body

            # パケット送信
            try:
                soc.sendall(packet)
            except socket.error as e:
                print('Connection closed.')
                break

            # FPS制御
            time.sleep(max(0, 1 / FPS - (time.time() - loop_start_time)))

        s.close()
