import sys
import cv2
import numpy as np
from PIL import Image, ImageQt
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QFileDialog, \
    QProgressBar, QMessageBox
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QObject, pyqtSignal, QThread


class WatermarkApp(QWidget):
    def __init__(self):
        super().__init__()

        self.video_path = ""
        self.logo_path = ""

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('视频添加水印')
        self.setGeometry(100, 100, 400, 250)

        self.video_label = QLabel('选择视频:')
        self.logo_label = QLabel('选择Logo:')

        self.video_button = QPushButton('选择视频', self)
        self.video_button.clicked.connect(self.load_video)

        self.logo_button = QPushButton('选择Logo', self)
        self.logo_button.clicked.connect(self.load_logo)

        self.process_button = QPushButton('添加水印', self)
        self.process_button.clicked.connect(self.start_processing)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)

        layout = QVBoxLayout()
        layout.addWidget(self.video_label)
        layout.addWidget(self.video_button)
        layout.addWidget(self.logo_label)
        layout.addWidget(self.logo_button)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.process_button)

        self.setLayout(layout)

        self.worker = VideoProcessingWorker()

        self.worker.finished.connect(self.processing_finished)
        self.worker.progress.connect(self.update_progress)

    def load_video(self):
        self.video_path, _ = QFileDialog.getOpenFileName(self, '选择视频', '', '视频文件 (*.mp4; *.avi)')

    def load_logo(self):
        self.logo_path, _ = QFileDialog.getOpenFileName(self, '选择Logo', '', '图像文件 (*.png; *.jpg; *.jpeg)')

    def start_processing(self):
        if not self.video_path or not self.logo_path:
            return

        output_path = self.video_path.split('.')[0] + '_watermarked.mp4'

        # Start the worker thread for video processing
        self.worker.set_paths(self.video_path, self.logo_path, output_path)
        self.worker.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def processing_finished(self):
        self.show_message('水印添加完成，输出路径：' + self.worker.output_path)

    def show_message(self, message):
        QMessageBox.information(self, '消息', message)


class VideoProcessingWorker(QThread):
    finished = pyqtSignal()
    progress = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.video_path = ""
        self.logo_path = ""
        self.output_path = ""

    def set_paths(self, video_path, logo_path, output_path):
        self.video_path = video_path
        self.logo_path = logo_path
        self.output_path = output_path

    def run(self):
        cap = cv2.VideoCapture(self.video_path)
        width = int(cap.get(3))
        height = int(cap.get(4))
        fps = cap.get(5)

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(self.output_path, fourcc, fps, (width, height))

        logo = Image.open(self.logo_path)
        logo = logo.convert("RGBA")
        logo = logo.resize((int(width * 0.05), int(height * 0.05)))

        logo_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        logo_layer.paste(logo, (width - logo.width-20, 20,), logo)

        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            pil_frame = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            frame_with_logo = Image.alpha_composite(pil_frame.convert("RGBA"), logo_layer)
            result_frame = cv2.cvtColor(np.array(frame_with_logo), cv2.COLOR_RGBA2BGR)

            out.write(result_frame)

            # Update progress
            current_frame = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
            progress_value = int((current_frame / frame_count) * 100)
            self.progress.emit(progress_value)

        cap.release()
        out.release()
        self.finished.emit()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = WatermarkApp()
    window.show()
    sys.exit(app.exec_())
