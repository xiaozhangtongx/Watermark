import sys
import cv2
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QGraphicsScene, \
    QGraphicsView, QProgressBar, QMessageBox, QFileDialog, QGraphicsRectItem
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QRectF, QPointF, QSizeF


class WatermarkApp(QWidget):
    def __init__(self):
        super().__init__()

        self.video_path = ""
        self.logo_path = ""
        self.output_path = ""

        self.logo_position = QPointF(0, 0)
        self.logo_scale = 0.5

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('视频添加水印')
        self.setGeometry(100, 100, 800, 600)

        # Widgets
        self.video_label = QLabel('选择视频:')
        self.logo_label = QLabel('选择Logo:')
        self.position_label = QLabel('水印位置:')
        self.scale_label = QLabel('水印缩放:')

        self.video_button = QPushButton('选择视频', self)
        self.video_button.clicked.connect(self.load_video)

        self.logo_button = QPushButton('选择Logo', self)
        self.logo_button.clicked.connect(self.load_logo)

        self.position_label = QLabel('水印位置:')
        self.scale_label = QLabel('水印缩放:')

        self.preview_scene = QGraphicsScene()
        self.preview_view = QGraphicsView(self.preview_scene)
        self.preview_view.setSceneRect(0, 0, 400, 300)

        self.process_button = QPushButton('生成水印视频', self)
        self.process_button.clicked.connect(self.process_video)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.video_label)
        layout.addWidget(self.video_button)
        layout.addWidget(self.logo_label)
        layout.addWidget(self.logo_button)
        layout.addWidget(self.position_label)
        layout.addWidget(self.scale_label)
        layout.addWidget(self.preview_view)
        layout.addWidget(self.process_button)
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)

        # Update labels and preview
        self.update_position_label()
        self.update_scale_label()

    def load_video(self):
        self.video_path, _ = QFileDialog.getOpenFileName(self, '选择视频', '', '视频文件 (*.mp4; *.avi)')
        self.update_preview()

    def load_logo(self):
        self.logo_path, _ = QFileDialog.getOpenFileName(self, '选择Logo', '', '图像文件 (*.png; *.jpg; *.jpeg)')
        self.update_preview()

    def update_preview(self):
        if not self.video_path or not self.logo_path:
            return

        video_cap = cv2.VideoCapture(self.video_path)
        _, frame = video_cap.read()

        logo = cv2.imread(self.logo_path, cv2.IMREAD_UNCHANGED)
        logo = cv2.resize(logo, (int(logo.shape[1] * self.logo_scale), int(logo.shape[0] * self.logo_scale)))

        x, y = int(self.logo_position.x()), int(self.logo_position.y())
        frame[y:y + logo.shape[0], x:x + logo.shape[1]] = self.overlay_logo(
            frame[y:y + logo.shape[0], x:x + logo.shape[1]], logo)

        height, width, channel = frame.shape

        bytes_per_line = 3 * width
        q_img = QPixmap.fromImage(QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888))

        new_q_img = q_img.scaledToHeight(400)

        self.preview_scene.clear()
        self.preview_scene.addPixmap(new_q_img)

    def overlay_logo(self, background, logo):
        x, y = int(self.logo_position.x()), int(self.logo_position.y())
        alpha_logo = logo[:, :, 3] / 255.0
        alpha_bg = 1.0 - alpha_logo

        for c in range(0, 3):
            background[y:y + logo.shape[0], x:x + logo.shape[1], c] = (alpha_logo * logo[:, :, c] +
                                                                       alpha_bg * background[y:y + logo.shape[0],
                                                                                  x:x + logo.shape[1], c])

        return background

    def update_position_label(self):
        self.position_label.setText(f'水印位置: ({int(self.logo_position.x())}, {int(self.logo_position.y())})')
        self.update_preview()

    def update_scale_label(self):
        self.scale_label.setText(f'水印缩放: {self.logo_scale:.2f}')
        self.update_preview()

    def process_video(self):
        if not self.video_path or not self.logo_path:
            return

        output_path = self.video_path.split('.')[0] + '_watermarked.mp4'
        self.output_path = output_path

        video_cap = cv2.VideoCapture(self.video_path)
        video_width = int(video_cap.get(3))
        video_height = int(video_cap.get(4))
        fps = video_cap.get(5)
        frame_count = int(video_cap.get(cv2.CAP_PROP_FRAME_COUNT))

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video_out = cv2.VideoWriter(output_path, fourcc, fps, (video_width, video_height))

        logo = cv2.imread(self.logo_path, cv2.IMREAD_UNCHANGED)
        logo = cv2.resize(logo, (int(logo.shape[1] * 0.5), int(logo.shape[0] * 0.5)))

        progress_step = 100 / frame_count
        current_progress = 0

        while video_cap.isOpened():
            ret, frame = video_cap.read()
            if not ret:
                break

            frame = self.overlay_logo(frame, logo)
            video_out.write(frame)

            current_progress += progress_step
            self.progress_bar.setValue(int(current_progress))

            # Uncomment the following line if you want to display each processed frame
            # self.update_preview()

            # Add a small delay to see the progress (optional)
            cv2.waitKey(1)

        video_cap.release()
        video_out.release()

        self.show_message(f'水印添加完成，输出路径：{self.output_path}')

    def show_message(self, message):
        QMessageBox.information(self, '消息', message)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = WatermarkApp()
    window.show()
    sys.exit(app.exec_())
