import configparser
from datetime import datetime
from dataclasses import dataclass
import os
import pathlib
import pickle

import easygui
import obspython as obs


config_path = ""
session_settings = None


@dataclass
class SessionSettings:
    is_continuation: bool
    series_path: str
    dt_format: str
    dt_first: bool

    def get_latest(self, key):
        """
        Gets index of latest recording of `key`, else creates key in
        series_path and returns 0.
        """
        with open(self.series_path, 'rb') as file:
            series_dict = pickle.load(file)

        if key in series_dict:
            return series_dict[key]
        else:
            series_dict[key] = 0
            # rename old file in case of crash while saving
            os.rename(self.series_path, self.series_path + "_old")
            with open(self.series_path, 'wb') as file:
                pickle.dump(series_dict, file)
            # delete old file
            os.remove(self.series_path + "_old")
            return 0

    def set_latest(self, key, num):
        """
        Sets index of latest recording of 'key'.
        """
        with open(self.series_path, 'rb') as file:
            series_dict = pickle.load(file)

        series_dict[key] = num
        # rename old file in case of crash while saving
        os.rename(self.series_path, self.series_path + "_old")
        with open(self.series_path, 'wb') as file:
            pickle.dump(series_dict, file)
        # delete old file
        os.remove(self.series_path + "_old")


def script_description():
    return """Script to ask for recording name immediately after stopping
              recording with options to add on a prefix/suffix that
              automatically increments a persistent value based on a config
              file"""


def script_load(settings):
    config = configparser.ConfigParser()
    config.read(config_path)
    global session_settings
    session_settings = SessionSettings(config['DEFAULT']['is_series'],
                                       config['DEFAULT']['series_path'],
                                       config['DEFAULT']['datetime_format'],
                                       config['DEFAULT']['datetime_first'])
    obs.obs_frontend_add_event_callback(on_event)


def script_update(settings):
    global session_settings
    session_settings.is_continuation = obs.obs_data_get_bool(settings,
                                                             "is_continuation")
    session_settings.series_path = obs.obs_data_get_string(settings,
                                                           "series_path")
    session_settings.dt_format = obs.obs_data_get_string(settings,
                                                         "datetime_format")
    session_settings.dt_first = obs.obs_data_get_string(settings,
                                                        "datetime_first")


def on_event(event):
    global session_settings
    if event == obs.OBS_FRONTEND_EVENT_RECORDING_STOPPED:
        # get Path object pointing to stopped recording
        file = get_recording()

        # get name for recording
        recording_name = easygui.enterbox("Enter name:", default="Untitled")

        # get part number from user with default obtained from series file
        recording_num = easygui.integerbox("Enter number:",
                                           default=session_settings
                                           .get_latest(recording_name) + 1)

        # get datetime string
        dt = datetime.now().strftime(session_settings.dt_format)

        # create new name
        if session_settings.dt_first:
            new_recording_name = f"{dt}_{recording_name}_{recording_num:>03}"
        else:
            new_recording_name = f"{recording_name}_{recording_num:>03}_{dt}"

        # rename recording
        file.rename(pathlib.Path(file.parent,
                                 f"{new_recording_name}{file.suffix}"))

        # update part number
        session_settings.set_latest(recording_name, recording_num)


def get_recording():
    # set variables to release later
    output = obs.obs_frontend_get_recording_output()
    output_data = obs.obs_output_get_settings(output)
    filepath = pathlib.Path(obs.obs_data_get_string(output_data, "path"))
    # release references to avoid memory leak
    obs.obs_data_release(output_data)
    obs.obs_output_release(output)
    return filepath
