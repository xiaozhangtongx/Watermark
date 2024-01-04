import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def add_watermark(video_path, output_path, logo_path):
    # Open the video file
    cap = cv2.VideoCapture(video_path)

    # Get video properties
    width = int(cap.get(3))
    height = int(cap.get(4))

    # 测试
    print(width, height)
    fps = cap.get(5)

    # Create a VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    # Open the logo image
    logo = Image.open(logo_path)
    logo = logo.convert("RGBA")

    # Resize the logo to a reasonable size (you may need to adjust this)
    logo = logo.resize((int(width * 0.2), int(height * 0.2)))

    # Create a transparent layer for the logo
    logo_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    logo_layer.paste(logo, (width - logo.width, height - logo.height), logo)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Convert frame to PIL Image
        pil_frame = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        # Paste the logo on the frame
        frame_with_logo = Image.alpha_composite(pil_frame.convert("RGBA"), logo_layer)

        # Convert the result back to OpenCV format
        result_frame = cv2.cvtColor(np.array(frame_with_logo), cv2.COLOR_RGBA2BGR)

        # Write the frame to the output video
        out.write(result_frame)

    cap.release()
    out.release()


if __name__ == "__main__":
    video_path = "./input/test01.mp4"
    output_path = "./output/video.mp4"
    logo_path = "./input/logo.png"

    add_watermark(video_path, output_path, logo_path)
