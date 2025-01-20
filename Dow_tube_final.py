import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QFileDialog, QMessageBox
from PyQt6.QtGui import QCloseEvent
from PyQt6.uic import loadUi
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QTextBrowser
import os
from moviepy.editor import VideoFileClip
from pytube import YouTube
import threading
from PyQt6.QtCore import QTimer
import subprocess
import MySQLdb
import dow_face2

ffmpeg_path = os.path.join(os.path.dirname(__file__), 'ffmpeg/ffmpeg.exe')

class VideoDownloaderThread(threading.Thread):
    def __init__(self, getlink, save_dir, option,info, completed_callback):
        super().__init__()
        self.getlink = getlink
        self.save_dir = save_dir
        self.option = option
        self.info = info
        self.completed_callback = completed_callback

    def run(self):
        try:
            yt = YouTube(self.getlink)
            if self.option == 2:
                out = yt.streams.get_highest_resolution().download(output_path=self.save_dir)
                
            elif self.option == 1:
                out = yt.streams.get_lowest_resolution().download(output_path=self.save_dir)
            elif self.option == 3:
                out = yt.streams.get_audio_only().download(output_path=self.save_dir)
                mp4_filename = os.path.basename(out)
                mp3_filename = mp4_filename.replace('.mp4', '.mp3')
                mp3_path = os.path.join(self.save_dir, mp3_filename)
                ffmpeg_cmd = [
                ffmpeg_path,'-i', out,
                '-vn', '-acodec', 'libmp3lame', '-q:a', '2',
                 "-y",  
                mp3_path
                ]
                subprocess.run(ffmpeg_cmd, shell=True)
                os.remove(out)

            video_message = f"<font color='green'> >>> Link {self.getlink} finished downloading! </font>"
            self.info.append(video_message)
            if self.option != 3:
                output = VideoFileClip(out)
                output.close()

            self.completed_callback(self.getlink)
        except Exception as e:
            # self.err = self.err+1
            self.completed_callback(self.getlink)
            error_message = f"<font color='red'> >>> Error link {self.getlink}: {e}</font>"
            self.info.append(error_message)


class downloadShorts(threading.Thread):
    def __init__(self, getlink, save_dir,option,info,completed_callback):  
        super().__init__()
        self.getlink = getlink
        self.save_dir = save_dir
        self.option = option
        self.info = info
        self.completed_callback = completed_callback
        self.err =0
        
    def run(self):
        try:
            yt = YouTube(self.getlink)
            if self.option == 2:
                out = yt.streams.get_highest_resolution().download(output_path=self.save_dir)
                
            elif self.option == 1:
                out = yt.streams.get_lowest_resolution().download(output_path=self.save_dir)
            elif self.option == 3:
                out = yt.streams.get_audio_only().download(output_path=self.save_dir)
                mp4_filename = os.path.basename(out)
                mp3_filename = mp4_filename.replace('.mp4', '.mp3')
                mp3_path = os.path.join(self.save_dir, mp3_filename)
                ffmpeg_cmd = [
                ffmpeg_path,'-i', out,
                '-vn', '-acodec', 'libmp3lame', '-q:a', '2',
                 "-y",
                mp3_path
                ]
                subprocess.run(ffmpeg_cmd, shell=True)
                os.remove(out)
            # self.err =0
            video_message = f"<font color='green'> >>> Link {self.getlink} finished downloading! </font>"
            self.info.append(video_message)
            if self.option != 3:
                output = VideoFileClip(out)
                output.close()
            #self.completed_callback(self.getlink, self.err)
            self.completed_callback(self.getlink)
        except Exception as e:
            self.completed_callback(self.getlink)
            error_message = f"<font color='red'> >>> Error link {self.getlink}: {e}</font>"
            self.info.append(error_message)

class TTHINDOWNLOAD(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi()
        self.time.setValue(0)  
        self.time.setMaximum(100)  

    def setupUi(self):
        gui = os.path.join(os.path.dirname(__file__), 'dowtube.ui')
        loadUi(gui, self)
        self.batdau.clicked.connect(self.download_tube)
        self.sele.clicked.connect(self.select_outputfolder)
        self.sd.toggled.connect(self.select_op)
        self.hd.toggled.connect(self.select_op)
        self.audio.toggled.connect(self.select_op)
        self.info = self.findChild(QTextBrowser, 'info')
       
    def select_op(self):
        if self.sd.isChecked(): 
            option = 1
        elif self.hd.isChecked(): 
            option = 2
        elif self.audio.isChecked(): 
            option = 3
        return option
        
    def select_outputfolder(self):
        self.sele.setEnabled(False)
        outfolder = QFileDialog.getExistingDirectory(self, "Select folder saving video")
        self.output.setText(outfolder)

    def download_tube(self):
        self.batdau.setEnabled(False)
        self.time.setValue(0) 
        op = self.select_op()
        getlinks = self.link.toPlainText().split('\n')
        save_dir = self.output.text()
        
        num_videos = len(getlinks)
        completed_videos = 0

        def on_video_completed(link):
            nonlocal completed_videos
            # err1 = err
            completed_videos += 1 

            progress = int((completed_videos / (num_videos) ) * 100)
            self.time.setValue(progress)
            if completed_videos == num_videos :
                QTimer.singleShot(0, self.show_completed_message)
           
        for getlink in getlinks:
                thread = VideoDownloaderThread(getlink.strip(), save_dir, op,self.info, on_video_completed)
                thread.start()
        
    def show_completed_message(self):
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Thông báo")
        msg_box.setText("Đã tải xong!")
        msg_box.exec()
        self.batdau.setEnabled(True)
        self.sele.setEnabled(True)
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWindow = TTHINDOWNLOAD()
    mainWindow.show()
    sys.exit(app.exec())
    

