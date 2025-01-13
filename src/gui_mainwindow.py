import sys
import os
import re
from PyQt5 import QtWidgets, QtCore
from downloader import Downloader

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("StreamlinkGUI-Downloader")
        self.setGeometry(100, 100, 600, 300)

        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)

        layout = QtWidgets.QVBoxLayout(central_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        self.url_input = QtWidgets.QLineEdit()
        self.url_input.setPlaceholderText("ダウンロードしたいVODのURLを入力してください...")
        self.url_input.textChanged.connect(self.on_url_changed)
        layout.addWidget(self.url_input)

        out_dir_layout = QtWidgets.QHBoxLayout()
        layout.addLayout(out_dir_layout)

        out_dir_label = QtWidgets.QLabel("出力先ディレクトリ:")
        out_dir_layout.addWidget(out_dir_label)

        self.output_dir_edit = QtWidgets.QLineEdit(os.path.join(os.getcwd(), "downloaded_vods"))
        out_dir_layout.addWidget(self.output_dir_edit)

        self.output_dir_btn = QtWidgets.QPushButton("参照")
        self.output_dir_btn.clicked.connect(self.select_output_dir)
        out_dir_layout.addWidget(self.output_dir_btn)

        file_name_layout = QtWidgets.QHBoxLayout()
        layout.addLayout(file_name_layout)

        file_name_label = QtWidgets.QLabel("ファイル名:")
        file_name_layout.addWidget(file_name_label)

        self.file_name_edit = QtWidgets.QLineEdit()
        self.file_name_edit.setPlaceholderText("保存するファイル名を入力してください...")
        file_name_layout.addWidget(self.file_name_edit)

        format_layout = QtWidgets.QHBoxLayout()
        layout.addLayout(format_layout)

        format_label = QtWidgets.QLabel("保存形式:")
        format_layout.addWidget(format_label)

        self.format_combo = QtWidgets.QComboBox()
        self.format_combo.addItems(["ts", "mp4"])
        format_layout.addWidget(self.format_combo)

        self.download_btn = QtWidgets.QPushButton("ダウンロード開始")
        self.download_btn.clicked.connect(self.start_download)
        layout.addWidget(self.download_btn)

        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.status_label = QtWidgets.QLabel("")
        layout.addWidget(self.status_label)

        self.thread = None
        self.downloader = None

    def detect_platform(self, url):
        """
        URLに基づいてプラットフォームを判別します。
        Returns:
            'youtube' or 'twitch' or 'unsupported'
        """
        if 'youtube.com' in url or 'youtu.be' in url:
            return 'youtube'
        elif 'twitch.tv' in url:
            return 'twitch'
        else:
            return 'unsupported'

    def adjust_format_options(self, platform):
        """
        プラットフォームに応じて保存形式の選択肢を調整します。
        """
        if platform == 'youtube':
            self.format_combo.blockSignals(True)
            self.format_combo.setCurrentText("mp4")
            self.format_combo.setEnabled(False)
            self.format_combo.blockSignals(False)
        elif platform == 'twitch':
            self.format_combo.setEnabled(True)
            self.format_combo.clear()
            self.format_combo.addItems(["ts", "mp4"])
        else:
            self.format_combo.setEnabled(False)
            self.format_combo.clear()

    def on_url_changed(self, text):
        platform = self.detect_platform(text)
        self.adjust_format_options(platform)
        if platform == 'unsupported' and text.strip() != "":
            self.status_label.setText("サポートされていないプラットフォームです。YouTubeとTwitchのみ対応しています。")
        else:
            self.status_label.setText("")

    def select_output_dir(self):
        directory = QtWidgets.QFileDialog.getExistingDirectory(self, "出力先ディレクトリを選択")
        if directory:
            self.output_dir_edit.setText(directory)

    def start_download(self):
        vod_url = self.url_input.text().strip()
        output_dir = self.output_dir_edit.text().strip()
        file_ext = self.format_combo.currentText()
        custom_filename = self.file_name_edit.text().strip()

        if not vod_url:
            self.status_label.setText("VODのURLを入力してください。")
            return
        if not output_dir:
            self.status_label.setText("出力先ディレクトリを選択してください。")
            return
        if custom_filename and not self.is_valid_filename(custom_filename):
            self.status_label.setText("無効なファイル名が含まれています。")
            return

        self.status_label.setText("ダウンロードを開始します...")
        self.download_btn.setEnabled(False)
        self.progress_bar.setVisible(True)

        self.downloader = Downloader(vod_url, output_dir, file_ext, custom_filename if custom_filename else None)
        self.downloader.progress.connect(self.update_status)
        self.downloader.finished.connect(self.download_finished)

        self.thread = QtCore.QThread()
        self.downloader.moveToThread(self.thread)
        self.thread.started.connect(self.downloader.run)
        self.downloader.finished.connect(self.thread.quit)
        self.downloader.finished.connect(self.downloader.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def update_status(self, message):
        self.status_label.setText(message)

    def download_finished(self, path):
        self.progress_bar.setVisible(False)
        self.download_btn.setEnabled(True)
        if path:
            self.status_label.setText(f"ダウンロード完了: {path}")
        else:
            self.status_label.setText("ダウンロードに失敗しました。")

    def is_valid_filename(self, filename):
        """
        ファイル名が有効かどうかを検証します。
        無効な文字が含まれていないか確認します。
        """
        return not re.search(r'[\\/*?:"<>|]', filename)

def run_app():
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
