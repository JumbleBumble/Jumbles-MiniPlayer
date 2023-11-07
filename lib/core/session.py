

# Used to automatically get and set attributes
class PropertyMeta(type):
    def __new__(cls, name, bases, dct):
        for attr_name in dct.get("_properties", []):
            dct[attr_name] = property(fget=lambda self, attr_name=attr_name: getattr(self, f"_{attr_name}"),
                                     fset=lambda self, value, attr_name=attr_name: setattr(self, f"_{attr_name}", value))

        return super().__new__(cls, name, bases, dct)
    


# Used to store settings & other shit
class Session(metaclass=PropertyMeta):
    _properties = {
        "search_type": "search", "amount": 1, "saved_input": None, "result": [],
        "auto_shuffle": False, "names": [], "current_playlist": None,
        "multi_playlist": None, "duration": None
    }

    def __init__(self):
        for attr_name, default_value in self._properties.items():
            setattr(self, f"_{attr_name}", default_value)

    class Keybindings(metaclass=PropertyMeta):
        _properties = ["play_action", "pause_action", "skip_action", "prev_action", "stop_action"]

        def __init__(self):
            for attr_name in self._properties:
                setattr(self, f"_{attr_name}", None)

    class MControl(metaclass=PropertyMeta):
        _properties = ["stopped", "paused", "skipped", "play_thread", "current", "song_end"]

        def __init__(self):
            for attr_name in self._properties:
                setattr(self, f"_{attr_name}", False)
                if attr_name == 'current': setattr(self, f"_{attr_name}", 0)

