import sys
import os
import threading
import requests
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QFileDialog, QMessageBox, QTextBrowser
from PyQt6.QtGui import QCloseEvent
from PyQt6.uic import loadUi
from PyQt6.QtCore import QTimer, QThread, pyqtSignal, Qt

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class FacebookDownloader:
    def __init__(self, video_urls, program_version_number, base_url, custom_directory, info, completed_callback):
        super().__init__()
        self.home_directory = os.path.expanduser("~")

        if custom_directory:
            self.downloads_directory = custom_directory
        else:
            self.downloads_directory = os.path.join(self.home_directory, "facebook-videos")
        self.program_version_number = program_version_number
        self.base_url = base_url
        self.video_urls = video_urls
        self.info = info
        self.completed_callback = completed_callback

    @staticmethod
    def __format_output_filename(user_defined_name) -> str:
        from datetime import datetime

        dt_now = datetime.now()
        if os.name == "nt":
            output_name = dt_now.strftime(f"{user_defined_name}_%d-%m-%Y %I-%M-%S%p-facebook-downloader.mp4")
        else:
            output_name = dt_now.strftime(f"{user_defined_name}_%d-%m-%Y %I:%M:%S%p-facebook-downloader.mp4")

        return output_name

    def path_finder(self) -> None:
        os.makedirs(self.downloads_directory, exist_ok=True)

    def download_video(self, video_url):
        option = webdriver.FirefoxOptions()
        option.add_argument('--headless')
        driver = webdriver.Firefox(options=option)

        try:
            driver.get(self.base_url)
            url_entry_field = driver.find_element(By.NAME, "url")
            url_entry_field.send_keys(video_url)
            url_entry_field.send_keys(Keys.ENTER)
            print(f"* Loading web resources for video: {video_url}. Please wait.")

            video_message1 = f"<font color='yellow'> >>> Link {video_url} start downloading! </font>"
            self.info.append(video_message1)

            download_btn_xpath = "/html/body/div[2]/div/div/div[1]/div/div[2]/div/div[3]/p[1]/a"
            download_btn = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, download_btn_xpath))
            )
            download_url = download_btn.get_attribute('href')

            with requests.get(download_url, stream=True) as response:
                response.raise_for_status()
                output_filename = self.__format_output_filename("facebook-video")
                output_path = os.path.join(self.downloads_directory, output_filename)
                with open(output_path, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        file.write(chunk)
                    print(f"* Downloaded: {output_path}")
                    self.completed_callback(video_url)
                    video_message = f"<font color='green'> >>> Link {video_url} finished downloading! </font>"
                    self.info.append(video_message)

        except Exception as e:
            self.completed_callback(video_url)
            error_message = f"<font color='red'> >>> Error link {video_url}: {e}</font>"
            self.info.append(error_message)
        finally:
            driver.quit()

    def download_videos_multithreaded(self):
        threads = []
        for video_url in self.video_urls:
            thread = threading.Thread(target=self.download_video, args=(video_url,))
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()


class DownloadThread(QThread):
    update_signal = pyqtSignal(str)

    def __init__(self, video_urls, downloader):
        super().__init__()
        self.video_urls = video_urls
        self.downloader = downloader

    def run(self):
        self.downloader.download_videos_multithreaded()


class TTHINDOWNLOAD(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi()
        self.time.setValue(0)
        self.time.setMaximum(100)
        self.download_thread = None

    def setupUi(self):
        gui = os.path.join(os.path.dirname(__file__), 'dowface.ui')
        loadUi(gui, self)
        self.batdau.clicked.connect(self.download_fbvideo)
        self.sele.clicked.connect(self.select_outputfolder)
        self.info = self.findChild(QTextBrowser, 'info')

    def select_outputfolder(self):
        self.sele.setEnabled(False)
        outfolder = QFileDialog.getExistingDirectory(self, "Select folder saving video")
        self.output.setText(outfolder)

    def download_fbvideo(self):
        self.batdau.setEnabled(False)
        self.time.setValue(0)
        video_urls = self.link.toPlainText().split('\n')
        custom_directory = self.output.text()
        num_videos = len(video_urls)
        completed_videos = 0

        def on_video_completed(link):
            nonlocal completed_videos
            completed_videos += 1

            progress = int((completed_videos / num_videos) * 100)
            self.time.setValue(progress)
            if completed_videos == num_videos:
                QTimer.singleShot(0, self.show_completed_message)

        self.download_thread = DownloadThread(video_urls, FacebookDownloader(
            video_urls=video_urls,
            program_version_number="1.4.0",
            base_url="https://getfvid.com",
            custom_directory=custom_directory,
            info=self.info,
            completed_callback=on_video_completed
        ))
        self.download_thread.update_signal.connect(self.update_info)
        self.download_thread.start()

    def update_info(self, message):
        self.info.append(message)

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
