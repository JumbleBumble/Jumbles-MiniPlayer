import sys           # Needed to exit PyQt5
import youtube_dl    # Used to get audio data from youtube
import random        # Used for shuffle and to get a random index for recommendations
import time          # Used for sleeps
import os            # Needed to set better media backend for windows users
import keyboard      # Used for keyboard keybinds
import contextvars   # Used for setting instance context
from PyQt5.QtMultimedia import QMediaPlayer
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QMainWindow,
    QPushButton,
    QGridLayout,
    QLineEdit,
    QSlider,
    QLabel
)
from lib.ui import components
from lib.core import session, playback_core, response_handler

os.environ["QT_MULTIMEDIA_PREFERRED_PLUGINS"] = "windowsmediafoundation" # Only works on windows, remove line if using linux/other

app = QApplication(sys.argv)





# WINDOW SETUP
window = QMainWindow()
window.setWindowTitle("MiniPlayer")
window.setFixedSize(240, 380)
window.setWindowFlags(Qt.FramelessWindowHint)
title_bar = components.CTitleBar()
window.setMenuWidget(title_bar)
central_widget = QWidget()
window.setCentralWidget(central_widget)
window.setStyleSheet(
    """QMainWindow {background-image: url('images/ggglitch.svg');background-repeat: no-repeat;}
    QPushButton {background-color: white;color: black;border: 2px solid #008CBA;
    border-radius: 5px;padding: 5px 10px;}QPushButton:hover {background-color: #ADD8E6;}
    QLabel {color: white;font-weight: bold;background-color: rgba(61, 56, 56, 0.8);
    border-radius: 5px;border: 1px inset rgba(84, 83, 83, 0.9);}
    QLineEdit {border-radius: 2px;}QSlider::groove:horizontal {border: 1px solid #007acc;background: black;height: 8px;border-radius: 4px;} 
    QSlider::handle:horizontal {background: white;border: none;width: 13px;height: 16px;border-radius: 3px;}
    QSlider::sub-page:horizontal {background: #007acc;border-radius: 4px;}
    QSlider::add-page:horizontal {border: none;border-radius: 4px;}"""
)

# WIDGET SETUP
main_components = {
    "media_player": QMediaPlayer(),
    "audio_label": QLabel(""),
    "duration_label": QLabel(""),
    "text_input": QLineEdit()
}

main_buttons = {
    "play_button": QPushButton("Play"),
    "pause_button": QPushButton("Pause"),
    "skip_button": QPushButton("►"),
    "previous_button": QPushButton("◄"),
    "stop_button": QPushButton("Stop"),
    "settings_button": QPushButton("Settings"),
    "multi_button": QPushButton("Multi Search"),

}
volume_label, volume_slider = QLabel("Volume"), QSlider(Qt.Horizontal)
volume_label.setAlignment(Qt.AlignCenter)
[widget.setAlignment(Qt.AlignCenter) 
 for name, widget in main_components.items() 
 if name != "media_player"]

main_components['audio_label'].setWordWrap(True)
main_components['text_input'].setPlaceholderText("Enter song/audio name here")
volume_slider.setRange(0, 100)  # volume range
volume_slider.setValue(50)  # default volume


# UTILITY CLASSES
saved_context = contextvars.ContextVar('saved')
keys_context = contextvars.ContextVar('keys')
variables_context = contextvars.ContextVar('variables')

saved_instance = session.Session()
keys_instance = saved_instance.Keybindings()
variables_instance = saved_instance.MControl()
saved_context.set(saved_instance),keys_context.set(keys_instance),variables_context.set(variables_instance)

def get_saved():
  try:
    return saved_context.get()
  except LookupError:
    return saved_instance

def get_keys():
  try:
    return keys_context.get()
  except LookupError:
    return keys_instance

def get_variables():
  try:
    return variables_context.get()
  except LookupError:
    return variables_instance


# PLAYBACK
def playback(saved,variables):
     # Checks duration for Duration_Handler
    def inner_duration(song):
        duration = song["duration"] or None
        if not duration:
            return True
        if saved.duration and PlaybackCore.duration_handler(duration):
            print("Audio duration is over the max duration, skipping audio.")
            return True
        return False

    # Checks url for Media_Handler and sets audio_label
    def inner_urlSetup(info):
        url, video_name = info["formats"][0]["url"] or None, info["title"] or ""
        if not url:
            return True
        PlaybackCore.media_handler(url)
        PlaybackCore.set_audio_label(video_name)
        return False
    
    # resume playback if paused
    if variables.paused:
        PlaybackCore.play()
        if PlaybackCore.sleep_check():
            if variables.current and not variables.paused and not variables.stopped: variables.current += 1
            return
        if not variables.stopped and not variables.paused: variables.current += 1
    else:
        PlaybackCore.handle_submit()  # handle input changes

    if saved.names is not None and len(saved.names) > 0:
        PlaybackCore.multi_handler()  # Handles multi search if Saved.names isnt empty

    PlaybackCore.set_audio_label("Loading..")
    if saved.search_type == "search":  # normal search
        if saved.result:
            for index, song in enumerate(saved.result):
                # current index handling
                if PlaybackCore.current_handler(index, "search"):
                    continue

                # duration handling
                if inner_duration(song):
                    continue

                rurl = f'https://www.youtube.com{song["url_suffix"]}'
                with youtube_dl.YoutubeDL(PlaybackCore.ydl_opts) as ydl:
                    try:
                        if not variables.skipped:
                            # retreives audio info then plays it
                            info = ydl.extract_info(rurl, download=False)
                            if inner_urlSetup(info):
                                continue

                        if PlaybackCore.sleep_check():
                            return
                    except youtube_dl.DownloadError:
                        PlaybackCore.set_audio_label("Youtube_dl Download Error. Attempting to skip audio..")
                        print(f"youtube_dl.DownloadError: {e}")
                        time.sleep(2)


    # Playlist search section
    else:
        with youtube_dl.YoutubeDL(PlaybackCore.ydl_opts) as ydl:
            # Check if current playlist has changed, it'll extract the results again if so, needed so that you don't have to wait & redownload the results everytime you stop or go to previous track.
            if (
                not saved.current_playlist
                or saved.saved_input != saved.current_playlist
            ):
                saved.current_playlist = saved.saved_input
                saved.current = None
                PlaybackCore.set_audio_label("Loading Playlist..")
                playlist = ydl.extract_info(saved.saved_input, download=False)
                saved.result = playlist["entries"]
                if saved.auto_shuffle:
                    random.shuffle(saved.result)

            for index, song in enumerate(saved.result):
                # current index handling
                if PlaybackCore.current_handler(index, "playlist"):
                    continue

                # duration handling
                if inner_duration(song):
                    continue

                try:
                    if not variables.skipped:
                        # Url setup
                        if inner_urlSetup(song):
                            continue

                    if PlaybackCore.sleep_check():
                        return
                except youtube_dl.DownloadError as e:
                    PlaybackCore.set_audio_label("Youtube_dl Download Error.  Attempting to skip audio..")
                    print(f"youtube_dl.DownloadError: {e}")
                    time.sleep(2)
                   

PlaybackCore = playback_core.PlaybackCore(get_saved(),get_variables(),main_components,main_buttons,window,playback)
d_manager = components.DialogManager(get_saved(),get_keys(),PlaybackCore,main_components['media_player'],response_handler.ResponseHandler)

def sp_media():
    if PlaybackCore.stopped_state("stopped"):
        PlaybackCore.pause()
    else:
        PlaybackCore.start()


# default hotkeys
[
    keyboard.add_hotkey(kcode, slot)
    for kcode, slot in [
        (-179, sp_media),
        (-178, PlaybackCore.stop),
        (-177, PlaybackCore.previous),
        (-176, PlaybackCore.skip),
    ]
]

# connecting button signals
[
    signal.connect(slot)
    for signal, slot in [
        (volume_slider.valueChanged, main_components['media_player'].setVolume),
        (main_buttons["play_button"].clicked, PlaybackCore.start),
        (main_buttons["pause_button"].clicked, PlaybackCore.pause),
        (main_buttons["skip_button"].clicked, PlaybackCore.skip),
        (main_buttons["previous_button"].clicked, PlaybackCore.previous),
        (main_buttons["stop_button"].clicked, PlaybackCore.stop),
        (main_buttons["settings_button"].clicked, d_manager.open_settings),
        (main_buttons["multi_button"].clicked, d_manager.open_multisearch),
    ]
]

# main window layout setup
layout = QGridLayout()
[
    layout.addWidget(*widget)
    for widget in [
        (main_components['audio_label'], 0, 0, 1, 2),
        (main_components['duration_label'], 1, 0, 1, 2),
        (main_components['text_input'], 2, 0, 1, 2),
        (main_buttons["play_button"], 3, 0, 1, 2),
        (main_buttons["previous_button"], 4, 0),
        (main_buttons["skip_button"], 4, 1),
        (main_buttons["pause_button"], 5, 0),
        (main_buttons["stop_button"], 5, 1),
        (main_buttons["settings_button"], 6, 0, 1, 2),
        (main_buttons["multi_button"], 7, 0, 1, 2),
        (volume_label, 8, 0, 1, 2),
        (volume_slider, 9, 0, 1, 2),
    ]
]
central_widget.setLayout(layout)

window.show()
sys.exit(app.exec_())
