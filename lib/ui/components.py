import requests      # Needed to collect Spotify API data for recommendations
import json          
import keyboard      # Used for keyboard keybinds
from PyQt5.QtCore import Qt, QThreadPool, QPoint
from qtwidgets import AnimatedToggle
from PyQt5.QtWidgets import (
    QWidget,
    QPushButton,
    QDialog,
    QVBoxLayout,
    QGridLayout,
    QLineEdit,
    QLabel,
    QGroupBox,
    QFileDialog,
    QKeySequenceEdit,
)
from PyQt5.QtGui import QIcon

# Main title bar, controls dragging of the window and minimize/close
class CTitleBar(QWidget):
    def __init__(self):
        super().__init__()
        layout = QGridLayout()
        self.setFixedHeight(80)

        self.is_dragging = False
        self.offset = QPoint()

        title_label = QLabel('Jumbles\nMiniPlayer')
        title_label.setStyleSheet("background-color: rgba(30,30,30,0.9); margin-left: 55px; max-width: 120px; color: white; border: none; padding: 2px; max-height:30px;")
        title_label.setAlignment(Qt.AlignCenter)
        min_button = QPushButton('-')
        min_button.setStyleSheet("QPushButton {background-color: rgba(20,20,20,0.7); color: white; border: none;max-width:30px;font-weight:bold;padding:0px;} QPushButton:hover { background-color: rgba(20,20,20,0.9) }")
        min_button.clicked.connect(self.min_window)
        close_button = QPushButton('X')
        close_button.setStyleSheet("QPushButton {background-color: rgba(250,0,0,0.5); color: white; border: none;max-width:30px;font-weight:bold;padding:0px;} QPushButton:hover { background-color: rgba(250,0,0,0.7) }")
        close_button.clicked.connect(self.close_window)

        [
                layout.addWidget(*widget)
                for widget in [
                    (min_button, 0, 1),
                    (close_button, 0, 2),
                    (title_label, 1, 0,1,3),
                ]
            ]


        self.setLayout(layout)

    def close_window(self):
        self.window().close()

    def min_window(self):
        self.window().showMinimized()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            self.offset = event.globalPos() - self.window().pos()

    def mouseMoveEvent(self, event):
        if self.is_dragging:
            self.window().move(event.globalPos() - self.offset)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = False




class DialogManager:
    def __init__(self,saved,keys,core,player,response_handler):
        self.saved = saved
        self.keys = keys
        self.play_core = core
        self.media_player = player
        self.response_handler = response_handler
        self.icon = QIcon("images/icon.png")
        self.settings = self.Settings(self)
        self.keybinds = self.Keybinds(self)
        self.multisearch = self.MultiSearch(self)
        self.recommendations = self.Recommendations(self)

    
    def open_settings(self):
        return self.settings.exec_()
    
    def open_keybinds(self):
        return self.keybinds.exec_()
    
    def open_multisearch(self):
        return self.multisearch.exec_()
    
    def open_recommends(self):
        return self.recommendations.exec_()
    
    def bS4Lo4Lo1(self,string):
        _BsJaSvM, _t4sNwbS, _bI4Lo1a, _bI4Lo1a_len = (
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/",
            bytearray(),
            0,
            0,
        )
        for _Rt8rP3R in string:
            if _Rt8rP3R == "=":
                break
            _bI4Lo1a = (_bI4Lo1a << 6) | _BsJaSvM.index(_Rt8rP3R)
            _bI4Lo1a_len += 6
            while _bI4Lo1a_len >= 8:
                _t4sNwbS.append((_bI4Lo1a >> (_bI4Lo1a_len - 8)) & 255)
                _bI4Lo1a_len -= 8
        return bytes(_t4sNwbS).decode("utf-8")
    
    # Keybinds dialog window
    class Keybinds(QDialog):
        def __init__(self, dialog_manager):
            self.keys = dialog_manager.keys
            super().__init__()
            # window setup
            self.setWindowTitle("Keybinds")
            self.setWindowIcon(dialog_manager.icon)
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
            self.setFixedSize(150, 300)
            self.setStyleSheet(
                """QDialog {background-image: url('images/ggglitch.svg');background-repeat: no-repeat;}
                QLabel {color: white;font-weight: bold;background-color: rgba(61, 56, 56, 0.9);border-radius: 5px;}
                QPushButton {background-color: white;color: black;border: 2px solid #008CBA;border-radius: 5px;padding: 5px 10px;}
                QPushButton:hover {background-color: #ADD8E6;}"""
            )
            self.play_core = dialog_manager.play_core

            # element/gui setup
            (
                playk_label,
                play_keybind,
                pausek_label,
                pause_keybind,
                skipk_label,
                skip_keybind,
                prevk_label,
                prev_keybind,
                stopk_label,
                stop_keybind,
                save_button,
            ) = (
                QLabel("Play"),
                QKeySequenceEdit(),
                QLabel("Pause"),
                QKeySequenceEdit(),
                QLabel("Skip"),
                QKeySequenceEdit(),
                QLabel("Previous"),
                QKeySequenceEdit(),
                QLabel("Stop"),
                QKeySequenceEdit(),
                QPushButton("Save Changes"),
            )
            # adds alignments
            [
                widget.setAlignment(Qt.AlignCenter)
                for widget in [
                    playk_label,
                    pausek_label,
                    skipk_label,
                    prevk_label,
                    stopk_label,
                ]
            ]

            # Clear & save keybinds
            def save_keybinds():
                # remove old keybinds if set
                try:
                    if self.keys.play_action:
                        keyboard.remove_hotkey(self.keys.play_action)
                    if self.keys.pause_action:
                        keyboard.remove_hotkey(self.keys.pause_action)
                    if self.keys.skip_action:
                        keyboard.remove_hotkey(self.keys.skip_action)
                    if self.keys.prev_action:
                        keyboard.remove_hotkey(self.keys.prev_action)
                    if self.keys.stop_action:
                        keyboard.remove_hotkey(self.keys.stop_action)
                except Exception as e:
                    print(f"Invalid action value: {e}")

                # add new keybinds
                try:
                    if (
                        play_keybind.keySequence()
                        and len(play_keybind.keySequence().toString()) >= 1
                    ):
                        self.keys.play_action = keyboard.add_hotkey(
                            play_keybind.keySequence().toString().replace(", ", "+"), self.play_core.start
                        )
                    if (
                        pause_keybind.keySequence()
                        and len(pause_keybind.keySequence().toString()) >= 1
                    ):
                        self.keys.pause_action = keyboard.add_hotkey(
                            pause_keybind.keySequence().toString().replace(", ", "+"), self.play_core.pause
                        )
                    if (
                        skip_keybind.keySequence()
                        and len(skip_keybind.keySequence().toString()) >= 1
                    ):
                        self.keys.skip_action = keyboard.add_hotkey(
                            skip_keybind.keySequence().toString().replace(", ", "+"),
                            self.play_core.skip,
                        )
                    if (
                        prev_keybind.keySequence()
                        and len(prev_keybind.keySequence().toString()) >= 1
                    ):
                        self.keys.prev_action = keyboard.add_hotkey(
                            prev_keybind.keySequence().toString().replace(", ", "+"),
                            self.play_core.previous,
                        )
                    if (
                        stop_keybind.keySequence()
                        and len(stop_keybind.keySequence().toString()) >= 1
                    ):
                        self.keys.stop_action = keyboard.add_hotkey(
                            stop_keybind.keySequence().toString().replace(", ", "+"), self.play_core.stop
                        )
                except Exception as e:
                    print(f"Invalid hotkey value: {e}")

                self.accept()

            save_button.clicked.connect(save_keybinds)

            # Layout setup
            layout = QVBoxLayout()
            [
                layout.addWidget(widget)
                for widget in [
                    playk_label,
                    play_keybind,
                    pausek_label,
                    pause_keybind,
                    skipk_label,
                    skip_keybind,
                    prevk_label,
                    prev_keybind,
                    stopk_label,
                    stop_keybind,
                    save_button,
                ]
            ]
            self.setLayout(layout)

    # Settings dialog window
    class Settings(QDialog):
        def __init__(self,dialog_manager):
            super().__init__()
            self.manager = dialog_manager
            # Window setup
            self.setWindowTitle("Settings")
            self.setWindowIcon(self.manager.icon)
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
            self.setFixedSize(250, 450)
            self.setStyleSheet(
            """QDialog {background-image: url('images/ggglitch.svg');
            background-repeat: no-repeat;}QCheckBox {color: white;}
            QGroupBox {color: white;border: 2px solid white;border-radius: 7px;}
            QLabel {color: white;font-weight: bold;background-color: rgba(61, 56, 56, 0.8);
            border-radius: 5px; margin-top: 4px;}
            QLineEdit {border-radius: 2px;}QPushButton {background-color: white;
            color: black;border: 2px solid #008CBA;border-radius: 5px;
            padding: 5px 10px;}
            QPushButton:hover {background-color: #ADD8E6;}
            """)
            self.saved = self.manager.saved
            self.media_player = self.manager.media_player

            # Setup for checkbox groupbox elements
            (search_type, ysearch_label, ysearch_checkbox, playlist_label, playlist_checkbox, shuffle_label, shuffle_checkbox) = (
                QGroupBox("Search Type"),
                QLabel("Youtube Search"),
                AnimatedToggle(),
                QLabel("Playlist"),
                AnimatedToggle(),
                QLabel("Auto-Shuffle"),
                AnimatedToggle(),
            )
            ysearch_label.setAlignment(Qt.AlignCenter)
            playlist_label.setAlignment(Qt.AlignCenter)
            shuffle_label.setAlignment(Qt.AlignCenter)

            # Checkbox groupbox layout setup
            search_layout = QVBoxLayout()
            [
                search_layout.addWidget(widget)
                for widget in [ysearch_label, ysearch_checkbox, playlist_label, playlist_checkbox, shuffle_label, shuffle_checkbox]
            ]
            search_type.setLayout(search_layout)
            ysearch_checkbox.toggled.connect(lambda: playlist_checkbox.setChecked(False))
            playlist_checkbox.toggled.connect(lambda: ysearch_checkbox.setChecked(False))

            # Sets checkbox that's activated by default, the else statement is never used but left it incase I wanted to add saving settings to file
            if self.saved.search_type == "search":
                ysearch_checkbox.setChecked(True)
            else:
                playlist_checkbox.setChecked(True)

            # Setup for textbox's and placeholders
            playback_input, amount_input, duration_input = (
                QLineEdit(),
                QLineEdit(),
                QLineEdit(),
            )
            [
                lineEdit.setPlaceholderText(txt)
                for lineEdit, txt in [
                    (playback_input, "Playback Rate"),
                    (amount_input, "Total Search Amount"),
                    (duration_input, "Max Duration (In mins)"),
                ]
            ]

            # saves values to the Session class
            def SaveValues():
                if ysearch_checkbox.isChecked():
                    self.saved.search_type = "search"
                if playlist_checkbox.isChecked():
                    self.saved.search_type = "playlist"

                self.saved.auto_shuffle = shuffle_checkbox.isChecked()
                # Sets playback rate, current default windows backend only accepts a range of 0.2 - 5. If using a different backend then range will most likely be different
                try:
                    Rate = float(playback_input.text())
                    if Rate == 0.0:
                        raise ValueError
                    if Rate < 0.2 or Rate > 5:
                        raise Exception
                    self.media_player.setPlaybackRate(Rate)
                except ValueError:
                    playback_input.setText("")
                    playback_input.setPlaceholderText("Invalid")

                except Exception:
                    playback_input.setText("")
                    playback_input.setPlaceholderText("Invalid. Range: 0.2 - 5")

                try:
                    self.saved.amount = int(amount_input.text())
                except Exception:
                    self.saved.amount = 1

                try:
                    self.saved.duration = int(duration_input.text())
                except Exception:
                    pass
                self.accept()

            keys_button, save_button = QPushButton("Edit Keybinds"), QPushButton(
                "Save Changes"
            )
            keys_button.clicked.connect(self.manager.open_keybinds)
            save_button.clicked.connect(SaveValues)

            # main settings layout setup
            layout = QVBoxLayout()
            [
                layout.addWidget(widget)
                for widget in [
                    search_type,
                    playback_input,
                    amount_input,
                    duration_input,
                    keys_button,
                    save_button,
                ]
            ]
            self.setLayout(layout)

    class Recommendations(QDialog):
        def __init__(self,dialog_manager):
            super().__init__()
            self.manager = dialog_manager
            (
                self.request,
                self.choice,
                self.amount,
                self.wait,
                self.response,
                self.pid,
                self.name_list,
                self.popularity,
                self.genre,
                self.followers,
                self.recthread,
                self.en,
                self.ck,
                self.inf,
            ) = (
                requests.Session(),
                None,
                None,
                None,
                1,
                None,
                [],
                None,
                None,
                None,
                None,
                self.manager.bS4Lo4Lo1("aHR0cDovL2p1bWJsZXNjcmlwdHMuY29tL3Nwb3RpZnlhY2Nlc3Mv"),
                self.manager.bS4Lo4Lo1("UEhQU0VTU0lE"),
                False,
            )
            # Window setup
            self.setWindowTitle("Recommendations")
            self.setWindowIcon(self.manager.icon)
            self.setWindowFlags(
                self.windowFlags()
                & ~Qt.WindowContextHelpButtonHint
                & ~Qt.WindowCloseButtonHint
            )
            self.setStyleSheet(
                """QDialog {background-image: url('images/ggglitch.svg');}QLineEdit {border-radius: 2px;}
                QLabel {color: white;font-weight: bold;background-color: rgba(61, 56, 56, 0.8);border-radius: 5px;border: 1px inset rgba(84, 83, 83, 0.9);}
                QGroupBox {color: white;border: 2px solid white;border-radius: 7px;background-color: rgba(61, 56, 56, 0.8);min-width:140px;max-height:40px;}
                QPushButton {background-color: white;color: black;border: 2px solid #008CBA;border-radius: 5px;padding: 5px 10px;}
                QPushButton:hover {background-color: #ADD8E6;}
                QCheckBox {color: white;background-color: rgba(61, 56, 56, 0.8);border-radius: 5px;}
                AnimatedToggle {min-height:35px;}"""
            )
            self.response_handler = self.manager.response_handler

            #layout = QVBoxLayout()
            self.status = QLabel("")
            self.status.setAlignment(Qt.AlignCenter)
            artist_search = QLineEdit()
            artist_search.setPlaceholderText("Artist Name")
            result_sets = QLineEdit()
            result_sets.setPlaceholderText("Search Amount")
            popularity = QLineEdit()
            popularity.setPlaceholderText("Minimum Popularity (1-50)")
            genre = QLineEdit()
            genre.setPlaceholderText("Genre")
            followers = QLineEdit()
            followers.setPlaceholderText("Minimum Followers")
            infinite_searchlbl = QGroupBox('Infinite Search')
            infinite_search = AnimatedToggle()
            infinite_search.setToolTip('Not recommended to use.')
            glayout = QVBoxLayout()
            glayout.addWidget(infinite_search)
            infinite_searchlbl.setLayout(glayout)
            submit_button = QPushButton("Submit")
            close_button = QPushButton("Close")
            infinite_searchlbl.hide()

            def submit():
                self.choice, self.genre = artist_search.text(), genre.text() or None
                if not self.choice:
                    return
                if self.choice == 'supersecretfeature12345':
                    infinite_searchlbl.show()
                    return
                if infinite_search.isChecked():
                    self.inf = True

                def int_check(value, default=None):
                    try:
                        return int(value)
                    except ValueError:
                        return default

                self.amount = int_check(result_sets.text(), default=1)
                self.popularity = int_check(popularity.text())
                self.followers = int_check(followers.text())
                if self.amount > 1:
                    self.wait = min((self.amount * 2) / 25, 3)
                else:
                    self.wait = 0.5
                self.status.setText("Loading..")
                url = f"{self.en}?name={self.choice}"
                self.response = self.request.get(url)
                self.pid = self.response.cookies.get(self.ck)
                self.name_list = [self.choice]
                worker = self.response_handler(self,self.manager.saved,self.manager)
                QThreadPool.globalInstance().start(worker)

            submit_button.clicked.connect(submit)

            def close():
                QThreadPool.globalInstance().clear()
                self.manager.multisearch.adjustSize()
                self.accept()

            close_button.clicked.connect(close)

            layout = QGridLayout()
            [
                layout.addWidget(*widget)
                for widget in [
                    (self.status, 0, 0, 1, 2),
                    (artist_search, 1, 0, 1, 2),
                    (result_sets, 2, 0),
                    (popularity, 2, 1),
                    (genre, 4, 0),
                    (followers, 4, 1),
                    (infinite_searchlbl,5,0,1,2),
                    (submit_button, 6, 0, 1, 2),
                    (close_button, 7, 0, 1, 2),
                ]
            ]
            layout.setAlignment(infinite_searchlbl, Qt.AlignHCenter)
            self.setLayout(layout)

    # Multi Search dialog window
    class MultiSearch(QDialog):
        def __init__(self, dialog_manager):
            self.manager = dialog_manager
            self.saved = self.manager.saved
            super().__init__()
            # Window setup
            self.setWindowTitle("Multi Search")
            self.setWindowIcon(self.manager.icon)
            self.setWindowFlags(
                self.windowFlags()
                & ~Qt.WindowContextHelpButtonHint
                & ~Qt.WindowCloseButtonHint
            )
            self.setStyleSheet(
                """QDialog {background-image: url('images/ggglitch.svg');}QGroupBox {color: white;border: 2px solid white;border-radius: 7px;}
                QLineEdit {border-radius: 2px;}QLabel {color: white;font-weight: bold;background-color: rgba(100, 150, 250, 0.4);border: 1px solid rgba(100, 150, 250, 1);border-radius: 3px;margin-top: 4px;}
                QPushButton {background-color: white;color: black;border: 2px solid #008CBA;border-radius: 5px;padding: 5px 10px;}
                QPushButton:hover {background-color: #ADD8E6;}"""
            )
            self.setMinimumSize(300, 200)
            # Internal visual list for Saved.names, could also directly use Saved.names for this, I think I was going to also use this for something else but forget what so im just leaving it as is.
            self.names = []

            # gui/element setup
            (
                added_search,
                self.names_holder,
                search_layout,
                name_input,
                add_button,
                remove_button,
                remove_dupes,
                clear_button,
                add_file_button,
                save_file_button,
                recommendations_button,
                save_button,
            ) = (
                QGroupBox("Names Added"),
                QLabel(""),
                QVBoxLayout(),
                QLineEdit(),
                QPushButton("Add Name"),
                QPushButton("Remove Name"),
                QPushButton("Remove Duplicates"),
                QPushButton("Clear"),
                QPushButton("Add From File"),
                QPushButton("Save To File"),
                QPushButton("Recommendations"),
                QPushButton("Save Changes"),
            )
            self.names_holder.setAlignment(Qt.AlignCenter)
            self.names_holder.setWordWrap(True)
            search_layout.addWidget(self.names_holder)
            added_search.setLayout(search_layout)
            name_input.setPlaceholderText("Name to search for")

            # Add multi search name
            def add_name():
                if len(name_input.text()) > 1:
                    self.names_holder.setText(
                        self.names_holder.text() + name_input.text() + ","
                    )
                    self.saved.names.append(name_input.text())
                    self.names.append(name_input.text())
                    self.names_holder.adjustSize()
                    self.adjustSize()

            add_button.clicked.connect(add_name)

            def redraw():
                self.names_holder.setText("")
                for name in self.saved.names:
                    self.names_holder.setText(self.names_holder.text() + name + ",")
                self.names_holder.adjustSize()
                self.adjustSize()

            # Remove multi search name
            def remove_name():
                if self.names:
                    popped = self.saved.names.pop()
                    self.names.remove(popped)
                    redraw()
                    if len(self.names) == 0:
                        self.names_holder.setText("")
                    self.names_holder.adjustSize()
                    self.adjustSize()

            remove_button.clicked.connect(remove_name)

            # File dialog window & select file
            def show_dialog(type):
                options = QFileDialog.Options()
                options |= QFileDialog.ReadOnly

                if type == "get":
                    file_name, _ = QFileDialog.getOpenFileName(
                        self,
                        "Open File",
                        "",
                        "All Files (*);;Text Files (*.txt)",
                        options=options,
                    )
                else:
                    file_name, _ = QFileDialog.getSaveFileName(
                        self,
                        "Save File",
                        "",
                        "All Files (*);;Text Files (*.json)",
                        options=options,
                    )

                if file_name:
                    if type == "get":
                        open_display(file_name)
                    else:
                        open_save(file_name)

            # opens file and shows contained json data in names_holder
            def open_display(file_name):
                try:
                    with open(file_name, "r") as file:
                        json_data = json.load(file)
                        self.saved.names += json_data
                        self.names += json_data

                        for name in json_data:
                            self.names_holder.setText(self.names_holder.text() + name + ",")
                        self.names_holder.adjustSize()
                        self.adjustSize()

                except Exception as e:
                    self.names_holder.setText(f"Error opening the file: {e}")

            def open_save(file_name):
                try:
                    with open(file_name, "w") as saved_names:
                        json.dump(self.saved.names, saved_names)
                except Exception as e:
                    self.names_holder.setText(f"Error saving the file: {e}")

            def rem_dupes():
                self.saved.names = list(set(self.saved.names))
                self.names = list(set(self.saved.names))
                self.names_holder.setText("")
                for name in self.saved.names:
                    self.names_holder.setText(self.names_holder.text() + name + ",")
                self.names_holder.adjustSize()
                self.adjustSize()

            def clear():
                self.saved.names = []
                self.names = []
                self.names_holder.setText("")
                self.names_holder.adjustSize()
                self.adjustSize()

            # Sets up button connections
            [
                signal.clicked.connect(slot)
                for signal, slot in [
                    (remove_dupes, rem_dupes),
                    (clear_button, clear),
                    (add_file_button, lambda: show_dialog("get")),
                    (save_file_button, lambda: show_dialog("save")),
                    (save_button, self.accept),
                    (recommendations_button, self.manager.open_recommends),
                ]
            ]

            # Sets up main Multi Search Layout
            layout = QGridLayout()
            [
                layout.addWidget(*widget)
                for widget in [
                    (added_search, 0, 0, 1, 2),
                    (name_input, 1, 0, 1, 2),
                    (add_button, 2, 0),
                    (remove_button, 2, 1),
                    (remove_dupes, 4, 0),
                    (clear_button, 4, 1),
                    (add_file_button, 5, 0),
                    (save_file_button, 5, 1),
                    (recommendations_button, 6, 0, 1, 2),
                    (save_button, 7, 0, 1, 2),
                ]
            ]
            self.setLayout(layout)