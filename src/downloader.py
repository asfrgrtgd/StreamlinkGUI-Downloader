import os
import subprocess
import re
from yt_dlp import YoutubeDL
from PyQt5.QtCore import QObject, pyqtSignal

class Downloader(QObject):
    progress = pyqtSignal(str)
    finished = pyqtSignal(str)

    def __init__(self, vod_url, output_dir, file_extension='ts', custom_filename=None):
        super().__init__()
        self.vod_url = vod_url
        self.output_dir = output_dir
        self.file_extension = file_extension
        self.custom_filename = self.sanitize_filename(custom_filename) if custom_filename else None

    def is_youtube_url(self, url):
        return 'youtube.com' in url or 'youtu.be' in url

    def is_twitch_url(self, url):
        return 'twitch.tv' in url

    def extract_youtube_id(self, url):
        """
        YouTubeの動画IDを抽出します。
        """
        regex = r'(?:v=|\/)([0-9A-Za-z_-]{11}).*'
        match = re.search(regex, url)
        if match:
            return match.group(1)
        return None

    def sanitize_filename(self, filename):
        """
        ファイル名から無効な文字を削除します。
        """
        return re.sub(r'[\\/*?:"<>|]', "_", filename)

    def download_with_streamlink(self):
        """
        Streamlinkを使用してTwitchのVODを最高品質でダウンロードします。
        """
        if self.custom_filename:
            final_path = os.path.join(self.output_dir, f"{self.custom_filename}.{self.file_extension}")
        else:
            vod_id = self.vod_url.rstrip('/').split('/')[-1]
            final_path = os.path.join(self.output_dir, f"{vod_id}.{self.file_extension}")

        self.progress.emit(f"Twitch VODのダウンロードを開始: {self.vod_url}")
        try:
            command = [
                'streamlink',
                self.vod_url,
                'best',
                '-o',
                final_path
            ]
            subprocess.run(command, check=True)
            self.progress.emit(f"Streamlinkによるダウンロード完了: {final_path}")
            self.finished.emit(final_path)
        except subprocess.CalledProcessError as e:
            self.progress.emit(f"Streamlinkによるダウンロード失敗: {e}")
            self.finished.emit("")

    def download_with_ytdlp(self):
        """
        yt-dlpを使用してYouTubeのVODを最高品質でダウンロードします。
        """
        if self.custom_filename:
            final_path = os.path.join(self.output_dir, f"{self.custom_filename}.{self.file_extension}")
        else:
            vod_id = self.extract_youtube_id(self.vod_url)
            if not vod_id:
                vod_id = self.vod_url.rstrip('/').split('/')[-1]
            final_path = os.path.join(self.output_dir, f"{vod_id}.{self.file_extension}")

        ydl_opts = {
            'outtmpl': final_path,
            'format': 'bestvideo+bestaudio/best',
            'merge_output_format': 'mp4' if self.file_extension.lower() == 'mp4' else 'ts',
            'quiet': True,
            'no_warnings': True,
        }

        self.progress.emit(f"YouTube VODのダウンロードを開始: {self.vod_url}")
        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.vod_url])
            self.progress.emit(f"yt-dlpによるダウンロード完了: {final_path}")

            self.finished.emit(final_path)
        except Exception as e:
            self.progress.emit(f"yt-dlpによるダウンロード失敗: {e}")
            self.finished.emit("")

    def run(self):
        """
        ダウンロードを開始します。
        """
        if self.is_twitch_url(self.vod_url):
            self.download_with_streamlink()
        elif self.is_youtube_url(self.vod_url):
            if self.file_extension.lower() != 'mp4':
                self.progress.emit("YouTubeの保存形式はmp4のみです。")
                self.finished.emit("")
            else:
                self.download_with_ytdlp()
        else:
            self.progress.emit("サポートされていないプラットフォームです。YouTubeとTwitchのみ対応しています。")
            self.finished.emit("")
