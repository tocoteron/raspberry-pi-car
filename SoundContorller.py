import pyaudio
import socket
import threading
import utility
import configparser

class SoundController(threading.Thread):
    def __init__(self, audio_format, audio_channels, audio_rate, audio_chunk, server_ip, server_port):
        print("SoundController __init__")
        self.FORMAT = audio_format
        self.CHANNELS = audio_channels
        self.RATE = audio_rate
        self.CHUNK = audio_chunk
        self.SERVER_IP = server_ip
        self.SERVER_PORT = server_port
        threading.Thread.__init__(self)

    def __del__(self):
        print("SoundController __del__")

    def run(self):
        # ログ表示用インデント
        INDENT = '    '

        # オーディオストリーム生成
        audio = pyaudio.PyAudio()
        stream = audio.open(format=self.FORMAT, channels=self.CHANNELS, rate=self.RATE, output=True, frames_per_buffer=self.CHUNK)

        # オーディオストリーム情報表示
        print('SoundController Stream {')
        print(INDENT + 'FORMAT   : {},'.format(self.FORMAT))
        print(INDENT + 'CHANNNELS: {},'.format(self.CHANNELS))
        print(INDENT + 'RATE     : {},'.format(self.RATE))
        print(INDENT + 'CHUNK    : {}'.format(self.CHUNK))
        print('}')

        # サーバーソケット生成
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
            server_sock.bind((self.SERVER_IP, self.SERVER_PORT))
            server_sock.listen(1)

            # サーバ情報表示
            print('SoundController Server {')
            print(INDENT + 'IP   : {},'.format(self.SERVER_IP))
            print(INDENT + 'PORT : {}'.format(self.SERVER_PORT))
            print('}')

            # クライアント接続
            client_sock, client_addr = server_sock.accept()
            with client_sock:

                # クライアント情報表示
                print('SoundController Client {')
                print(INDENT + 'ip   : {},'.format(client_addr[0]))
                print(INDENT + 'port : {}'.format(client_addr[1]))
                print('}')

                while True:
                    data = client_sock.recv(self.CHUNK)
                    stream.write(data)

            stream.stop_stream()
            stream.close()
            audio.terminate()

if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('./settings.ini', 'UTF-8')
    sound_controller = SoundController(pyaudio.paInt16, int(config.get('sound', 'channels')), int(config.get('sound', 'rate')), int(config.get('sound', 'chunk')), utility.get_server_ip(), int(config.get('sound', 'port')))
    sound_controller.start()
    sound_controller.join()