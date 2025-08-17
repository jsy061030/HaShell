import subprocess
import os
import threading
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide" # 隐藏pygame导入的欢迎词
import pygame
from pynput import keyboard  # Avoid permission issues on Linux (Root unrequired)
import time
import sys
import random

playing = threading.Event()
stop_playing = threading.Event()
stopable = True
playList = 'Victory'

def pygame_audio_worker():
    global stopable, playList
    pygame.mixer.init()
    while True:
        if playing.is_set():
            if os.name == 'nt':
                path_separator = '\\'
            if os.name == 'posix':
                path_separator = '/'
            try:
                path = 'resources' + path_separator + playList + '.wav'
                pygame.mixer.music.load(path)
                pygame.mixer.music.play()
                    
            except Exception as e:
                print(f'音频播放出错: {e}')
                playing.clear()
                continue

            while playing.is_set() and pygame.mixer.music.get_busy():
                if stopable and stop_playing.is_set():
                    pygame.mixer.music.stop()
                    stop_playing.clear()
                    print('哈基米被制裁了！\n')
                    break
                time.sleep(0.1)
            playing.clear()
        time.sleep(0.1)

def key_listener():
    def on_press(key):
        try:
            if key == keyboard.Key.esc and playing.is_set() and stopable:
                stop_playing.set()
        except AttributeError:
            pass

    listener = keyboard.Listener(on_press=on_press)
    listener.daemon = True
    listener.start()

audio_thread = threading.Thread(target=pygame_audio_worker, daemon=True)
audio_thread.start()
key_listener()

if __name__ == "__main__":
    try:
        while True:
            stopable = False
            print('Ha ! ', end='')
            command = input()
            match command:
                case ':ha':
                    print('伟大的哈基米胜利！')
                    playList = 'Victory'
                    stopable = True
                    playing.set()
                    while playing.is_set():
                        time.sleep(0.1)
                case ':q':
                    print('Exiting HaShell')
                    pygame.mixer.quit()
                    sys.exit()
                case ':h':
                    print('可用的提示符有: \n:h (help) \n:ha 播放哈基米胜利曲，用ESC键制裁哈基米 \n:q (quit) \n当然可以直接输入命令或程序。\n输的对有奖励，输错了有惩罚。\n')
                case _:
                    result = subprocess.run(command, shell=True)
                    if result.returncode != 0:
                        print(f'Command failed with return code {result.returncode}\n')
                        playList = 'haqi' + random.choice(['1','2','3'])
                        stopable = False
                        playing.set()
                        while playing.is_set():
                            time.sleep(0.1)
    except KeyboardInterrupt:
        print('Exiting HaShell')
        pygame.mixer.quit()
        sys.exit()
