from kivy.app import App
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.core.window import Window
import sys
import cv2
import numpy as np
import socket
import configparser
from kivy.uix.widget import Widget
from kivy.properties import StringProperty, ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
import threading
import glob
import pyaudio
import wave

class SoundStream(threading.Thread):
    def __init__(self, wav_filename):
        config = configparser.ConfigParser()
        config.read('./settings.ini', 'UTF-8')
        self.SERVER_IP = App.get_running_app().SERVER_IP
        self.SERVER_PORT = int(config.get('sound', 'port'))
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = int(config.get('sound', 'channels'))
        self.RATE = int(config.get('sound', 'rate'))
        self.CHUNK = int(config.get('sound', 'chunk'))
        threading.Thread.__init__(self)
        self.load_audio(wav_filename)

    def run(self):
        audio = pyaudio.PyAudio()
        stream = audio.open(format=self.FORMAT, channels=self.CHANNELS, rate=self.RATE, input=True, frames_per_buffer=self.CHUNK)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((self.SERVER_IP, self.SERVER_PORT))

            while True:
                voice_data = stream.read(self.CHUNK)
                music_data = self.wav_file.readframes(self.CHUNK)

                # リピート処理
                if music_data == b'':
                    self.wav_file.rewind()
                    music_data = self.wav_file.readframes(self.CHUNK)

                sock.send(self.mix_sounds(voice_data, music_data, self.CHANNELS, self.CHUNK))

        stream.stop_stream()
        stream.close()
        audio.terminate()

    def mix_sounds(self, data1, data2, channels, chunk):
        decoded_data1 = np.frombuffer(data1, np.int16).copy()
        decoded_data2 = np.frombuffer(data2, np.int16).copy()
        decoded_data1.resize(channels * chunk, refcheck=False)
        decoded_data2.resize(channels * chunk, refcheck=False)
        return (decoded_data1 * 0.5 + decoded_data2 * 0.5).astype(np.int16).tobytes()
    
    def load_audio(self, wav_filename):
        self.wav_file = wave.open(wav_filename, 'rb')

class RootWidget(BoxLayout):
    def __init__(self, **kwargs):
        super(RootWidget, self).__init__(**kwargs)

class AudioListWidget(Widget):
    def __init__(self, **kwargs):
        super(AudioListWidget, self).__init__(**kwargs)

        layout = GridLayout(cols=1, spacing=0, size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))
        audio_list = glob.glob("./*.wav")
        for audio_filename in audio_list:
            btn = Button(text=audio_filename, size_hint_y=None, height=40)
            btn.bind(on_press=self.audio_select)
            layout.add_widget(btn)

        scroll_view = ScrollView(size_hint=(None, None), size=(200, Window.height))
        scroll_view.add_widget(layout)
        scroll_view.pos = (800, 0)
        
        self.add_widget(scroll_view)

        self.sound_stream = SoundStream(audio_list[0])
        self.sound_stream.setDaemon(True)
        self.sound_stream.start()
    
    def audio_select(self, instance):
        print('The button <%s> is being pressed' % instance.text)
        self.sound_stream.load_audio(instance.text)

class WebCameraWidget(Widget):

    web_camera_image = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(WebCameraWidget, self).__init__(**kwargs)

        config = configparser.ConfigParser()
        config.read('./settings.ini', 'UTF-8')

        # 通信用設定
        self.buff = bytes()
        self.soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.SERVER_IP = App.get_running_app().SERVER_IP
        self.SERVER_PORT = int(config.get('web_camera', 'port'))
        self.PACKET_HEADER_SIZE = int(config.get('web_camera', 'header_size'))
        self.IMAGE_WIDTH = int(config.get('web_camera', 'image_width'))
        self.IMAGE_HEIGHT = int(config.get('web_camera', 'image_height'))

        # 表示設定
        self.VIEW_FPS = 30
        self.VIEW_WIDTH = 800
        self.VIEW_HEIGHT = 600

        # 画面更新メソッドの呼び出し設定
        Clock.schedule_interval(self.update, 1.0 / self.VIEW_FPS)

        # サーバに接続
        try:
            self.soc.connect((self.SERVER_IP, self.SERVER_PORT))
        except socket.error as e:
            print('Connection failed.')
            sys.exit(-1)

    def update(self, dt):
        # サーバからのデータをバッファに蓄積
        data = self.soc.recv(self.IMAGE_HEIGHT * self.IMAGE_WIDTH * 3)
        self.buff += data

        # 最新のパケットの先頭までシーク
        # バッファに溜まってるパケット全ての情報を取得
        packet_head = 0
        packets_info = list()
        while True:
            if len(self.buff) >= packet_head + self.PACKET_HEADER_SIZE:
                binary_size = int.from_bytes(self.buff[packet_head:packet_head + self.PACKET_HEADER_SIZE], 'big')
                if len(self.buff) >= packet_head + self.PACKET_HEADER_SIZE + binary_size:
                    packets_info.append((packet_head, binary_size))
                    packet_head += self.PACKET_HEADER_SIZE + binary_size
                else:
                    break
            else:
                break

        # バッファの中に完成したパケットがあれば、画像を更新
        if len(packets_info) > 0:
            # 最新の完成したパケットの情報を取得
            packet_head, binary_size = packets_info.pop()
            # パケットから画像のバイナリを取得
            img_bytes = self.buff[packet_head + self.PACKET_HEADER_SIZE:packet_head + self.PACKET_HEADER_SIZE + binary_size]
            # バッファから不要なバイナリを削除
            self.buff = self.buff[packet_head + self.PACKET_HEADER_SIZE + binary_size:]

            # 画像をバイナリから復元
            img = np.frombuffer(img_bytes, dtype=np.uint8)
            img = cv2.imdecode(img, 1)
            # 画像を表示用に加工
            img = cv2.flip(img, 0)
            img = cv2.resize(img, (self.VIEW_WIDTH, self.VIEW_HEIGHT))
            # 画像をバイナリに変換
            img = img.tostring()

            # 作成した画像をテクスチャに設定
            img_texture = Texture.create(size=(self.VIEW_WIDTH, self.VIEW_HEIGHT), colorfmt='bgr')
            img_texture.blit_buffer(img, colorfmt='bgr', bufferfmt='ubyte')
            #self.texture = img_texture
            self.web_camera_image.texture = img_texture

    def disconnect(self):
        # サーバとの接続を切断
        self.soc.shutdown(socket.SHUT_RDWR)
        self.soc.close()

class CarClientApp(App):

    def __init__(self, window_width, window_height, server_ip, **kwargs):
        super(CarClientApp, self).__init__(**kwargs)
        self.WINDOW_WIDTH = window_width
        self.WINDOW_HEIGHT = window_height
        self.SERVER_IP = server_ip

    def build(self):
        Window.size = (self.WINDOW_WIDTH, self.WINDOW_HEIGHT)
        return RootWidget()

    def on_stop(self):
        pass

if __name__ == '__main__':
    cca = CarClientApp(window_width=1000, window_height=600, server_ip=sys.argv[1])
    cca.run()
