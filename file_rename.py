import configparser
from datetime import datetime
import pathlib

import easygui
import obspython as obs

from utils import DropdownBox, InputBox, SessionSettings


config_path = ""
session_settings = None


def script_description():
    return """Script to ask for recording name immediately after stopping
              recording with options to add on a prefix/suffix that
              automatically increments a persistent value based on a config
              file"""


# initialise with config file or there will be a race condition
def script_defaults(settings):
    config = configparser.ConfigParser(interpolation=None)
    config.read(config_path)
    global session_settings
    session_settings = SessionSettings(config['DEFAULT']
                                       ['is_series'] == 'True',
                                       config['DEFAULT']['series_path'],
                                       config['DEFAULT']['datetime_format'],
                                       config['DEFAULT']
                                       ['datetime_first'] == 'True',
                                       config['DEFAULT']
                                       ['sort_latest'] == 'True')
    obs.obs_data_set_default_bool(settings, "is_series",
                                  session_settings.is_series)
    obs.obs_data_set_default_string(settings, "series_path",
                                    session_settings.series_path)
    obs.obs_data_set_default_string(settings, "datetime_format",
                                    session_settings.datetime_format)
    obs.obs_data_set_default_bool(settings, "datetime_first",
                                  session_settings.datetime_first)
    obs.obs_data_set_default_bool(settings, "sort_latest",
                                  session_settings.sort_latest)


def script_load(settings):
    obs.obs_frontend_add_event_callback(on_event)


def script_update(settings):
    global session_settings
    session_settings.is_series = obs.obs_data_get_bool(settings,
                                                       "is_series")
    session_settings.series_path = obs.obs_data_get_string(settings,
                                                           "series_path")
    session_settings.datetime_format = (obs
                                        .obs_data_get_string(settings,
                                                             "datetime_format"
                                                             ))
    session_settings.datetime_first = obs.obs_data_get_bool(settings,
                                                            "datetime_first")
    session_settings.sort_latest = obs.obs_data_get_bool(settings,
                                                         "sort_latest")
    session_settings.save_config(config_path)


def on_event(event):
    global session_settings
    if event == obs.OBS_FRONTEND_EVENT_RECORDING_STOPPED:
        # get Path object pointing to stopped recording
        file = get_recording()

        # load series data
        series_data = session_settings.get_series()
        if session_settings.sort_latest:  # sort keys by timestamp
            series_data.sort(key=lambda x: x[1]['timestamp'], reverse=True)
        else:  # sort keys in alphabetical order
            series_data.sort(key=lambda x: x[0])

        # get name for recording
        recording_name_UI = DropdownBox([series[0] for series in series_data])
        recording_name = (recording_name_UI.get_value().lower()
                          .replace(" ", "_"))
        if recording_name == "":  # If nothing was entered
            recording_name = "untitled"

        # get part number from user with default obtained from series file
        recording_num_UI = InputBox(session_settings
                                    .get_latest(recording_name) + 1)
        recording_num = int(recording_num_UI.get_value())

        # get datetime string
        dt = datetime.now().strftime(session_settings.datetime_format)

        # create new name
        if session_settings.datetime_first:
            new_recording_name = f"{dt}_{recording_name}_{recording_num:>03}"
        else:
            new_recording_name = f"{recording_name}_{recording_num:>03}_{dt}"

        # update part number
        session_settings.set_latest(recording_name, recording_num,
                                    datetime.now().timestamp())

        # rename recording
        while True:  # keep trying while file is being accessed
            try:
                file.rename(pathlib.Path(file.parent,
                                         f"{new_recording_name}{file.suffix}"))
                break
            except PermissionError:
                continue


def get_recording():
    # set variables to release later
    output = obs.obs_frontend_get_recording_output()
    output_data = obs.obs_output_get_settings(output)
    filepath = pathlib.Path(obs.obs_data_get_string(output_data, "path"))
    # release references to avoid memory leak
    obs.obs_data_release(output_data)
    obs.obs_output_release(output)
    return filepath
