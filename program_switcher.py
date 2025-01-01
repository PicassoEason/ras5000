import RPi.GPIO as GPIO
import time
import subprocess
import signal
import sys
import os

class ProgramSwitcher:
    def __init__(self):
        # 設定GPIO按鈕腳位
        self.BUTTON_1 = 17  # GPIO17 for audiobook_OCR
        self.BUTTON_2 = 27  # GPIO27 for audiobook_player
        self.BUTTON_3 = 22  # GPIO22 for RAG_helper
        
        # 初始化GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.BUTTON_1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.BUTTON_2, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.BUTTON_3, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        # 當前執行的程式進程
        self.current_process = None
        
        # 程式路徑
        self.programs = {
            self.BUTTON_1: "audiobook_OCR_cam_ras.py",
            self.BUTTON_2: "audiobook_player.py",
            self.BUTTON_3: "RAG_helper.py"
        }

    def button_callback(self, channel):
        """按鈕回調函數"""
        time.sleep(0.1)  # 消除按鈕彈跳
        
        if GPIO.input(channel) == GPIO.LOW:  # 按鈕被按下
            print(f"Button on GPIO {channel} pressed")
            self.switch_program(channel)

    def switch_program(self, button_pin):
        """切換程式"""
        # 如果有正在運行的程式，先終止它
        if self.current_process:
            print("Terminating current program...")
            self.current_process.terminate()
            self.current_process.wait()
            self.current_process = None

        # 啟動新程式
        program = self.programs.get(button_pin)
        if program:
            print(f"Starting {program}...")
            try:
                # 使用 Python 解釋器執行程式
                self.current_process = subprocess.Popen(['python3', program])
            except Exception as e:
                print(f"Error starting program: {e}")

    def cleanup(self):
        """清理GPIO和進程"""
        if self.current_process:
            self.current_process.terminate()
            self.current_process.wait()
        GPIO.cleanup()

    def run(self):
        """主運行循環"""
        # 設置按鈕事件檢測
        GPIO.add_event_detect(self.BUTTON_1, GPIO.FALLING, 
                            callback=self.button_callback, bouncetime=300)
        GPIO.add_event_detect(self.BUTTON_2, GPIO.FALLING, 
                            callback=self.button_callback, bouncetime=300)
        GPIO.add_event_detect(self.BUTTON_3, GPIO.FALLING, 
                            callback=self.button_callback, bouncetime=300)

        print("Program switcher running. Press Ctrl+C to exit.")
        print("Button 1: OCR Camera Reader")
        print("Button 2: Audiobook Player")
        print("Button 3: RAG Helper")

        try:
            # 保持程式運行
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nExiting program")
            self.cleanup()

def main():
    switcher = ProgramSwitcher()
    switcher.run()

if __name__ == "__main__":
    main()