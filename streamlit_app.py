import os
import av
import threading
import streamlit as st
import streamlit_nested_layout
from streamlit_webrtc import VideoHTMLAttributes, webrtc_streamer

from audio_handling import AudioFrameHandler
from drowsy_detection import VideoFrameHandler


# tentukan audio file yang akan digunakan
alarm_file_path = os.path.join("audio", "wake_up.wav")

# komponen streamlit
st.set_page_config(
    page_title="DeeVi",
    page_icon="mbkm image.png",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "DeeVi",
    },
)


col1, col2 = st.columns(spec=[6, 2], gap="medium")

with col1:
    st.title("DeeVi")
    with st.container():
        c1, c2 = st.columns(spec=[1, 1])
        with c1:
            # jumlah waktu (dalam detik) untuk menunggu sebelum membunyikan alarm
            WAIT_TIME = st.slider(
                "Seconds to wait before sounding alarm:", 0.0, 5.0, 1.0, 0.25)

        with c2:
            # nilai terendah Eye Aspect Ratio. nilai ideal [0,15, 0,2].
            EAR_THRESH = st.slider(
                "Eye Aspect Ratio threshold:", 0.0, 0.4, 0.18, 0.01)

thresholds = {
    "EAR_THRESH": EAR_THRESH,
    "WAIT_TIME": WAIT_TIME,
}

# untuk streamlit-webrtc
video_handler = VideoFrameHandler()
audio_handler = AudioFrameHandler(sound_file_path=alarm_file_path)

lock = threading.Lock()  # untuk akses thread-safe & untuk mencegah race-condition
shared_state = {"play_alarm": False}


def video_frame_callback(frame: av.VideoFrame):
    frame = frame.to_ndarray(format="bgr24")  # convert frame ke RGB

    frame, play_alarm = video_handler.process(
        frame, thresholds)  # frame diproses
    with lock:
        shared_state["play_alarm"] = play_alarm  # update status dibagikan

    return av.VideoFrame.from_ndarray(frame, format="bgr24")


def audio_frame_callback(frame: av.AudioFrame):
    with lock:  # untuk mengakses alarm
        play_alarm = shared_state["play_alarm"]

    new_frame: av.AudioFrame = audio_handler.process(
        frame, play_sound=play_alarm)
    return new_frame


with col1:
    ctx = webrtc_streamer(
        key="drowsiness-detection",
        video_frame_callback=video_frame_callback,
        audio_frame_callback=audio_frame_callback,
        rtc_configuration={"iceServers": [
            {"urls": ["stun:stun.l.google.com:19302"]}]},  # tambahkan ke konfigurasi untuk penerapan cloud
        media_stream_constraints={
            "video": {"height": {"ideal": 480}}, "audio": True},
        video_html_attrs=VideoHTMLAttributes(
            autoPlay=True, controls=False, muted=False),
    )
