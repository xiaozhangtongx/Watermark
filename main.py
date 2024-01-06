import sys
import cv2
import numpy as np
from PIL import Image, ImageQt
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QFileDialog, \
    QProgressBar, QMessageBox, QSlider, QHBoxLayout, QSpinBox
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, pyqtSignal, QThread


class WatermarkApp(QWidget):
    def __init__(self):
        super().__init__()

        self.video_path = ""
        self.logo_path = ""
        self.logo_position = (20, 20)
        self.logo_scale = 0.5

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('视频添加水印')
        self.setGeometry(100, 100, 600, 450)

        self.video_label = QLabel('选择视频:')
        self.logo_label = QLabel('选择Logo:')
        self.x_label = QLabel('X:')
        self.y_label = QLabel('Y:')
        self.scale_label = QLabel('缩放比例:0.5')

        self.video_button = QPushButton('选择视频', self)
        self.video_button.clicked.connect(self.load_video)

        self.logo_button = QPushButton('选择Logo', self)
        self.logo_button.clicked.connect(self.load_logo)

        self.x_spinbox = QSpinBox(self)
        self.x_spinbox.setMinimum(0)
        self.x_spinbox.setMaximum(9999)
        self.x_spinbox.setValue(self.logo_position[0])
        self.x_spinbox.valueChanged.connect(self.update_logo_position)

        self.y_spinbox = QSpinBox(self)
        self.y_spinbox.setMinimum(0)
        self.y_spinbox.setMaximum(9999)
        self.y_spinbox.setValue(self.logo_position[1])
        self.y_spinbox.valueChanged.connect(self.update_logo_position)

        self.scale_slider = QSlider(Qt.Horizontal)
        self.scale_slider.setMinimum(1)
        self.scale_slider.setMaximum(100)
        self.scale_slider.setValue(int(self.logo_scale * 100))
        self.scale_slider.valueChanged.connect(self.update_logo_scale)

        self.preview_label = QLabel(self)
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setFixedSize(400, 300)

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

        position_layout = QHBoxLayout()
        position_layout.addWidget(self.x_label)
        position_layout.addWidget(self.x_spinbox)
        position_layout.addWidget(self.y_label)
        position_layout.addWidget(self.y_spinbox)

        layout.addLayout(position_layout)

        layout.addWidget(self.scale_label)
        layout.addWidget(self.scale_slider)
        layout.addWidget(self.preview_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.process_button)

        self.setLayout(layout)

        self.worker = VideoProcessingWorker()

        self.worker.finished.connect(self.processing_finished)
        self.worker.progress.connect(self.update_progress)

    def load_video(self):
        self.video_path, _ = QFileDialog.getOpenFileName(self, '选择视频', '', '视频文件 (*.mp4; *.avi)')
        self.update_preview()

    def load_logo(self):
        self.logo_path, _ = QFileDialog.getOpenFileName(self, '选择Logo', '', '图像文件 (*.png; *.jpg; *.jpeg)')
        self.update_preview()

    def update_preview(self):

        # 显示视频的第一帧预览图
        if self.video_path and self.logo_path:
            cap = cv2.VideoCapture(self.video_path)
            ret, frame = cap.read()
            if ret:
                logo = Image.open(self.logo_path)
                logo = logo.convert("RGBA")
                logo = logo.resize((int(logo.width * self.logo_scale), int(logo.height * self.logo_scale)))

                logo_layer = Image.new("RGBA", (frame.shape[1], frame.shape[0]), (0, 0, 0, 0))
                self.logo_position = [frame.shape[1] - logo.width - 20, 20]
                self.x_spinbox.setValue(self.logo_position[0])
                self.y_spinbox.setValue(self.logo_position[1])

                logo_layer.paste(logo, (self.logo_position[0], self.logo_position[1]), logo)

                pil_frame = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                frame_with_logo = Image.alpha_composite(pil_frame.convert("RGBA"), logo_layer)
                result_frame = cv2.cvtColor(np.array(frame_with_logo), cv2.COLOR_RGBA2BGR)

                height, width, channel = result_frame.shape

                bytes_per_line = 3 * width
                q_img = QImage(result_frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(q_img).scaledToWidth(400)

                self.preview_label.setPixmap(pixmap)

    def update_logo_position(self):
        self.logo_position = (self.x_spinbox.value(), self.y_spinbox.value())
        self.update_preview()

    def update_logo_scale(self):
        self.logo_scale = self.scale_slider.value() / 100.0
        self.scale_label.setText(f'水印缩放: {self.logo_scale:.2f}')
        self.update_preview()

    def start_processing(self):
        if not self.video_path or not self.logo_path:
            return

        output_path = self.video_path.split('.')[0] + '_watermarked.mp4'

        # Start the worker thread for video processing
        self.worker.set_paths(self.video_path, self.logo_path, output_path, self.logo_position, self.logo_scale)
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
        self.logo_position = (20, 20)
        self.logo_scale = 0.5

    def set_paths(self, video_path, logo_path, output_path, logo_position, logo_scale):
        self.video_path = video_path
        self.logo_path = logo_path
        self.output_path = output_path
        self.logo_position = logo_position
        self.logo_scale = logo_scale

    def run(self):
        cap = cv2.VideoCapture(self.video_path)
        width = int(cap.get(3))
        height = int(cap.get(4))
        fps = cap.get(5)

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(self.output_path, fourcc, fps, (width, height))

        logo = Image.open(self.logo_path)
        logo = logo.convert("RGBA")
        logo = logo.resize((int(logo.width * self.logo_scale), int(logo.height * self.logo_scale)))

        logo_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        logo_layer.paste(logo, (self.logo_position[0], self.logo_position[1]), logo)

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
