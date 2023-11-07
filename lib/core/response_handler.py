import random        # Used for shuffle and to get a random index for recommendations
import time          # Used for sleeps
import requests      # Needed to collect Spotify API data for recommendations
import json          
from PyQt5.QtCore import QRunnable, pyqtSignal, QObject




class WorkerSignals(QObject):
    finished = pyqtSignal()



class ResponseHandler(QRunnable):
    def __init__(self, main_instance, saved, d_manager):
        self.saved = saved
        self.d_manager = d_manager
        self.skip_next = False
        super().__init__()
        self.main_instance = main_instance
        self.signals = WorkerSignals()

    # Main function for worker thread
    def run(self):
        # Used to collect a artist based on a random index
        def artist_check(inf=False, data=None):
            if inf and data:
                for index, artist in enumerate(data["artists"]):
                    if index == random_index:
                        return artist["name"]
            else:
                for index, artist in enumerate(next_list):
                    if index == random_index:
                        return artist

        # Checks if it should recursively call run to continue collecting or call handle_finish to insert info.
        def handle_end():
            if main.amount > 0 and next_artist is not None:
                url = f"{main.en}?name={next_artist}"
                time.sleep(main.wait)
                main.response = main.request.get(url)
                self.run()
            else:
                if main.amount > 0 and next_artist is None:
                    return self.handle_finish("artist")
                else:
                    return self.handle_finish()

        # Handles estimated loading duration, could probably tweak this to make it better but it's mostly accurate.
        def handle_duration():
            if not main.inf:
                added = 0
                if main.followers:
                    added += main.followers / (main.followers / 5)
                if main.popularity:
                    added += main.popularity / 15
                time_per_result = (
                    max(responsetime, 0.001) / max(main.amount / 20, 1) + added
                )
                total_time = (
                    (main.amount + time_per_result)
                    + (main.amount * (main.wait / 20))
                    + (responsetime)
                )
                minutes, seconds = round(total_time // 60), round(total_time % 60)
                main.status.setText(
                    f"\n{main.amount} results left to fetch\n\nEstimated Load Duration\n{minutes:02d}:{seconds:02d}\n"
                )
            else:
                main.status.setText(f"\n{main.amount} results left to fetch..\n")

        # Loops through the collected artists from API and checks a bunch of conditionals like followers, popularity etc to see if it should append or not. 
        def loop_append(artist):
            if main.popularity and artist["popularity"] < main.popularity:
                return True
            if main.genre and not next(
                (g for g in artist["genres"] if not main.genre.lower().find(g.lower())),
                False,
            ):
                return True
            if main.followers and artist["followers"]["total"] < main.followers:
                return True
            if not artist["name"].lower() in main.name_list:
                main.amount -= 1
                main.name_list.append(artist["name"].lower())
                next_list.append(artist["name"])
                if main.inf:
                    self.skip_next = artist["name"]
                handle_duration()
                if main.amount <= 0:
                    return False
                time.sleep(0.1)
                return True
            else:
                return True

        main = self.main_instance
        responsetime = 0

        # This block handles calling loop_append, finish, setting next artist and ending thread.
        if main.response.status_code == 200:
            data = self.retry(
                main.response.json, fallback=json.loads, arg=main.response.text
            )
            if not data:
                return
            artists = data.get("artists", {}).get("items", None)

            if artists[0]:
                id = artists[0]["id"]
                url = f"{main.en}?artid={id}&pid={main.pid}"
                start_time = time.time()
                response = main.request.get(url)
                end_time = time.time()
                responsetime += end_time - start_time
                time.sleep(main.wait)

                if response.status_code == 200:
                    data = self.retry(
                        response.json, fallback=json.loads, arg=response.text
                    )
                    if not data:
                        return

                    random_index, next_artist = None, None
                    next_list = []
                    self.skip_next = False
                    for artist in data["artists"]:
                        if loop_append(artist):
                            continue
                        else:
                            return self.handle_finish()

                    if not len(next_list) and not main.inf:
                        return self.handle_finish("artist")

                    if main.inf:
                        random_index = random.randrange(0, len(data["artists"]))
                        if not self.skip_next:
                            next_artist = artist_check(True, data)
                        else:
                            next_artist = self.skip_next
                    else:
                        random_index = random.randrange(0, len(next_list))
                        next_artist = artist_check()

                    handle_end()
                    return
                else:
                    return self.handle_finish("rate")

            else:
                return self.handle_finish("artist")

        else:
            return self.handle_finish("rate")

    # Inserts info into lists and names_holder
    def insert_info(self):
        for name in self.main_instance.name_list:
            self.d_manager.multisearch.names_holder.setText(self.d_manager.multisearch.names_holder.text() + name + ",")
            self.d_manager.multisearch.names.append(name)
            self.saved.names.append(name)
        time.sleep(0.1)
        self.signals.finished.emit()

    # Handles retrying JSONDecoding with a fallback
    def retry(self, func, fallback, arg=None, retries=10, delay=10):
        for _ in range(retries):
            try:
                return func()
            except json.JSONDecodeError or requests.exceptions.JSONDecodeError:
                print("JSON fallback initiated")
                if fallback is not None and arg is not None:
                    try:
                        return self.retry(fallback(arg))
                    except json.JSONDecodeError:
                        pass

                time.sleep(delay)
        self.handle_finish("exception", 521, "Raised in retry (Used all retries)")
        return False

    #Handles setting final label text and inserting info
    def handle_finish(self, ertype=None, exception_num=None, exception=None):
        if not ertype:
            self.main_instance.status.setText(
                f"\nSuccesfully fetched all results. They've been inserted into Multi Search\n"
            )
            self.insert_info()
            return
        if ertype == "rate":
            print(f"Rate limit exceeded. Try again later")
            self.main_instance.status.setText(
                f"\nRate limit exceeded, Try again later\n\nResults that were able to be collected were inserted into Multi Search\n"
            )
            self.insert_info()
            return
        if ertype == "artist":
            print("No related artists found.")
            self.main_instance.status.setText(
                f"\nNo more related artists found.\n\nResults that were able to be collected were inserted into Multi Search\n"
            )
            self.insert_info()
            return
        if ertype == "exception":
            if exception_num and exception:
                print(f"Error {exception_num}: {exception}")
                self.main_instance.status.setText(
                    f"\nA problem occured while trying to collect results. (Error code {exception_num})\n\nResults that were able to be collected were inserted into Multi Search\n"
                )
            elif exception_num:
                print(f"Error {exception_num}: NO EXCEPTION GIVEN!")
                self.main_instance.status.setText(
                    f"\nA problem occured while trying to collect results. (Error code {exception_num})\n\nResults that were able to be collected were inserted into Multi Search\n"
                )
            if not exception_num:
                print(f"GENERIC EXCEPTION!")
                self.main_instance.status.setText(
                    f"\nA problem occured while trying to collect results. (Error code not found)\n\nResults that were able to be collected were inserted into Multi Search\n"
                )
            self.insert_info()
            return