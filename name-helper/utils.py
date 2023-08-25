import configparser
from dataclasses import dataclass
import os
import pickle
import tkinter as tk
from tkinter import ttk


@dataclass
class SessionSettings:
    is_series: bool
    series_path: str
    datetime_format: str
    datetime_first: bool
    sort_latest: bool

    def get_series(self):
        """
        Get list of series followed by part data associated.
        :return: List of (name, part data).
        """
        with open(self.series_path, 'rb') as file:
            series_dict = pickle.load(file)
        
        return list(series_dict.items())

    def get_latest(self, key):
        """
        Gets part number of latest recording of `key`, else creates key in
        series_path and returns 0.
        """
        with open(self.series_path, 'rb') as file:
            series_dict = pickle.load(file)

        if key in series_dict:
            return series_dict[key]['number']
        else:
            series_dict[key] = 0

            # rename old file in case of crash while saving
            os.rename(self.series_path, self.series_path + "_old")

            # write new dict to file
            with open(self.series_path, 'wb') as file:
                pickle.dump(series_dict, file)

            # delete old file
            os.remove(self.series_path + "_old")
            return 0

    def set_latest(self, key, num, timestamp):
        """
        Sets index of latest recording of `key`.
        """
        with open(self.series_path, 'rb') as file:
            series_dict = pickle.load(file)

        series_dict[key] = {'number': num, 'timestamp': timestamp}

        # rename old file in case of crash while saving
        os.rename(self.series_path, self.series_path + "_old")

        # write new dict to file
        with open(self.series_path, 'wb') as file:
            pickle.dump(series_dict, file)

        # delete old file
        os.remove(self.series_path + "_old")

    def save_config(self, config_filepath):
        """
        Saves current config to config file.
        """
        # rename old file in case of crash while saving
        os.rename(config_filepath, config_filepath + "_old")

        # write current config to file
        config = configparser.ConfigParser(interpolation=None)
        config['DEFAULT'] = self.__dict__  # get instance variables as dict

        with open(config_filepath, 'w') as file:
            config.write(file)

        # delete old file
        os.remove(config_filepath + "_old")


class DropdownBox:
    """
    Dropdown box in tkinter.
    """
    def __init__(self, values, width=400, height=200):
        """
        :param values: List of values to show in dropdown box.
        """
        self.selected = None  # selected value after "confirming"
        self.window = tk.Tk()
        self.window.configure(width=width, height=height)
        self.label = ttk.Label(self.window, text="Series Name:")
        self.label.grid(row=0, column=0)
        self.combobox_frame = ttk.Frame(self.window, width=width,
                                        height=height*0.8)
        self.combobox_frame.grid(row=1, column=0, padx=4, pady=8)
        self.combobox = ttk.Combobox(self.combobox_frame,
                                     values=values,
                                     height=8, width=42 * int(width/400),
                                     font="calibri")
        self.combobox.pack()
        self.button_frame = ttk.Frame(self.window)
        self.button_frame.grid(row=2, column=0, pady=5)
        self.confirm_button = ttk.Button(self.button_frame,
                                         text="Confirm", command=self.quit)
        self.confirm_button.pack()
        self.window.mainloop()

    def quit(self):
        self.selected = self.combobox.get()
        self.window.destroy()

    def get_value(self):
        return self.selected


class InputBox:
    """
    Input box in tkinter.
    """
    def __init__(self, value, width=400, height=200):
        """
        :param value: Value to show in text box.
        """
        self.selected = None  # selected value after "confirming"
        self.window = tk.Tk()
        self.window.configure(width=width, height=height)
        self.label = ttk.Label(self.window, text="Part Number:")
        self.label.grid(row=0, column=0)
        self.input_frame = ttk.Frame(self.window, width=width,
                                     height=height*0.8)
        self.input_frame.grid(row=1, column=0, padx=4, pady=5)
        self.text_box = ttk.Entry(self.input_frame)
        self.text_box.pack()
        self.text_box.insert(tk.END, value)
        self.button_frame = ttk.Frame(self.window)
        self.button_frame.grid(row=2, column=0, pady=5)
        self.confirm_button = ttk.Button(self.button_frame, text="Confirm",
                                         command=self.quit)
        self.confirm_button.pack()
        self.window.mainloop()

    def quit(self):
        self.selected = self.text_box.get()
        self.window.destroy()

    def get_value(self):
        return self.selected
