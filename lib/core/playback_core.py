import threading     # Needed for the playback thread & other things
import types         # Used this for a coroutine
import random        # Used for shuffle and to get a random index for recommendations
import time          # Used for sleeps
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl
from youtube_search import YoutubeSearch  # Used to scrape youtube data



# Class that handles most playback functions
class PlaybackCore:
    def __init__(self, saved, variables, main_components, main_buttons, window, playback):
        # youtube_dl options for retreiving audio
        self.ydl_opts = {
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
        }
        self.saved = saved
        self.variables = variables
        self.main_components = main_components
        self.main_components['media_player'].mediaStatusChanged.connect(self.handle_media_status)
        self.main_buttons = main_buttons
        self.window = window
        self.playback = playback

    # Handle text input changes & saves them into Session, also checks if saved input has changed so it doesn't have to redownload a bunch of the same results if using multi search.
    def handle_submit(self):
        user_input = self.main_components['text_input'].text()
        if user_input != self.saved.saved_input:
            if self.saved.search_type != "search":
                self.saved.saved_input = user_input
                return

            # checks if not using multi search and if not then searches full amount
            if len(self.saved.names) == 0:
                self.saved.result = YoutubeSearch(user_input, max_results=self.saved.amount).to_dict()

                if self.saved.auto_shuffle:
                    random.shuffle(self.saved.result)
            self.saved.current = None
            self.saved.saved_input = user_input


    # Handles setting audio label and adjusting size
    def set_audio_label(self,text):
        self.main_components['audio_label'].setText(text)
        self.window.adjustSize()

    # handle media player status changes
    def handle_media_status(self,status):
        if status == 7:
            self.main_components['audio_label'].setText("")
            self.main_components['duration_label'].setText("")
            self.window.adjustSize()



    # play audio
    def play(self):
        self.main_components['media_player'].play()
        self.main_buttons["play_button"].setText("Play")
        self.variables.stopped, self.variables.paused = False, False


    # pause audio
    def pause(self):
        self.main_components['media_player'].pause()
        self.main_buttons["play_button"].setText("Resume")
        self.variables.paused = True


    # stop audio
    def stop(self):
        self.variables.stopped = True
        self.main_components['media_player'].stop()
        self.main_buttons["play_button"].setText("Play")


    # play previous track
    def previous(self):
        self.main_buttons["play_button"].setText("Play")
        self.variables.paused = False
        if self.variables.current and self.variables.current >= 1:
            self.variables.current -= 1
            self.stop()
            self.start()

    def skip(self):
        self.main_buttons["play_button"].setText("Play")
        self.variables.skipped = True
        if self.variables.stopped and not self.variables.paused:
            if self.variables.current: self.variables.current += 1
            self.stop()
            self.start()
        elif self.variables.paused:
            self.variables.paused = False
            self.stop()
            self.start()

    # helper to check if player is stopped
    def stopped_state(self,type):
        state = self.main_components['media_player'].state()
        if type == "stopped":
            if state == QMediaPlayer.StoppedState or state == QMediaPlayer.PausedState:
                return False
            else:
                return True
        else:
            if state == QMediaPlayer.BufferedMedia or state == QMediaPlayer.StoppedState:
                return True
            else:
                return False
            
    # formats the millisecond duration from info data into mm:ss format then sets the duration label.
    def format_time(self,millis):
        minutes, seconds = millis // (1000 * 60), (millis % (1000 * 60)) // 1000
        self.main_components['duration_label'].setText(f"{minutes:02d}:{seconds:02d}")

    # formats seconds to mm:ss, used for playlists as ydl.extract_info's duration is a int of total seconds while a YoutubeSearch duration is already in a mm:ss string.
    def format_seconds(self,sec):
        minutes, seconds = sec // 60, sec % 60
        return f"{minutes:02d}:{seconds:02d}"
    
    # Coroutine that calls format_time to update the duration label & is also used as a fallback for StoppedState('stopped') by skipping audio if streaming quality isn't good enough
    @types.coroutine
    def check_position(self):
        try:
            while True:
                current_position = self.main_components['media_player'].position()
                self.format_time(current_position)
                time.sleep(1)
                next_position = self.main_components['media_player'].position()

                if current_position == next_position:
                    return
                yield
        except StopIteration:
            return

    # Sleeps while checking for changes in playback
    def sleep_check(self):
        try:
            checker = self.check_position()
            next(checker)
        except StopIteration:
            if self.variables.skipped: self.variables.skipped = False
            return False

        def end_checker():
            try:
                checker.throw(StopIteration)
            except Exception:
                pass

        while self.stopped_state("stopped"):
            if self.variables.skipped:
                self.variables.skipped = False
                end_checker()
                self.main_components['media_player'].stop()
                if (
                    self.variables.current is not None
                    and len(self.saved.result) > self.variables.current
                ):
                    self.set_audio_label("Loading..")
                return False
            if self.variables.stopped or self.variables.paused:
                end_checker()
                return True

            try:
                value = checker.send(None)
                if value is not None:
                    end_checker()
                    return False
            except StopIteration:
                pass
            except Exception as e:
                print(f"stopped_state Exception: {e}")
                return False
        if self.variables.stopped or self.variables.paused:
            end_checker()
            return True
        end_checker()
        return False

    # Handle Multi Search
    def multi_handler(self):
        self.set_audio_label("Loading Multi Search Playlist..")
        if (
            self.saved.multi_playlist is not None
            and self.saved.multi_playlist != self.saved.saved_input + str(len(self.saved.names))
            or not self.saved.multi_playlist
        ):
            self.saved.multi_playlist = self.saved.saved_input + str(len(self.saved.names))

            total, remainder = self.saved.amount % len(self.saved.names), self.saved.amount % len(
                self.saved.names
            )
            for index, name in enumerate(self.saved.names):
                try:
                    if index < total:
                        temp_results = YoutubeSearch(
                            name,
                            max_results=max(
                                round(
                                    self.saved.amount / len(self.saved.names)
                                    + round(max(len(self.saved.names) / remainder, 0))
                                ),
                                1,
                            ),
                        ).to_dict()
                        remainder -= round(len(self.saved.names) / remainder)
                    elif index != (len(self.saved.names) - 1):
                        temp_results = YoutubeSearch(
                            name,
                            max_results=round(max(self.saved.amount / len(self.saved.names), 1)),
                        ).to_dict()
                    else:
                        temp_results = YoutubeSearch(
                            name,
                            max_results=round(
                                max(
                                    self.saved.amount / len(self.saved.names) + max(remainder, 0),
                                    1,
                                )
                            ),
                        ).to_dict()

                    self.saved.result += temp_results
                except Exception:
                    print(f"Error loading results for: {name} ({index})")
                    pass

                self.set_audio_label(
                    f"Loading Multi Search Playlist..\nLoaded {index} out of {str(len(self.saved.names))}.."
                )

            if self.saved.auto_shuffle:
                random.shuffle(self.saved.result)

    # Sets media and plays it
    def media_handler(self,url):
        try:
            self.main_components['media_player'].setMedia(QMediaContent(QUrl(url)))
            self.play()
        except Exception as e:
            print(f"Error setting URL / Playing Audio: {e}")
            raise e
        self.set_audio_label("Loading..")
        self.main_components['duration_label'].setText("")

        current_position = self.main_components['media_player'].position()
        time.sleep(0.1)
        next_position = self.main_components['media_player'].position()

        while current_position == next_position:
            time.sleep(0.1)
            next_position = self.main_components['media_player'].position()

    # Check if duration is over max
    def duration_handler(self,duration):
        if type(duration) == int:
            duration = self.format_seconds(duration)
        if self.saved.duration:
            dur_split = duration.split(":")
            if int(dur_split[0]) > self.saved.duration or len(dur_split) == 3:
                return True
        return False

    # Handles the current audio index
    def current_handler(self, index, typ):
        if typ == "playlist":
            if index == len(self.saved.result) - 1:
                self.variables.skipped = True

        # Check if playback was paused and adjust current if so
        if self.variables.paused and self.variables.current is not None:
            self.variables.current += 1
            self.variables.paused = False

        # Makes sure current loop is at the same index as the current audio, if it's on a track that has already been played itll skip to the next one
        if self.variables.current is not None and self.variables.current > index:
            return True
        elif (
            self.variables.current is not None
            and self.variables.current != index
            and self.variables.current + 1 != index
        ):
            return True
        self.variables.current = index
        return False
    

    
    def start(self):
        if self.variables.play_thread and self.variables.play_thread.is_alive():
            self.variables.play_thread.join()
        self.variables.play_thread = threading.Thread(target=self.playback, args=(self.saved,self.variables))
        self.variables.stopped = False
        try:
            self.variables.play_thread.start()
        except RuntimeError as e:
            print(f"Thread RuntimeError Error (Duplicate thread attempt?): {e}")
            pass