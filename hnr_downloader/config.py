"""Config File for Hengrui Downloader
Currently, only three items can be configed:
    always_delete_downloaded_file (default: False): when deleting a download task,
    whether delete the downloaded file.

    default_save_to (default: None): default path for downloaded file. Every download task may set
    its own save_to attribute.

    auto_change_default_save_to (default: True): change default_save_to to the last
    added download's save_to

    max_retry (default 50): max try numbers, used in fetching info and downloading

    debug(default: False): when True, will print out excetion track
"""

import os
import json
import traceback


class HnrConfig():
    def __init__(self, config_file, **arg):
        self.config_file = config_file
        self.always_delete_downloaded_file = False
        self.default_save_to = None
        self.auto_change_default_save_to = True
        self.max_retry = 50
        self.debug = False
        self.last_used_http_proxy = None
        self.last_used_https_proxy = None
        self.auto_start = True
        self.read_config()

    def read_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                try:
                    d = json.load(f)
                except Exception:
                    pass
                else:
                    for key, value in d.items():
                        if hasattr(self, key):
                            setattr(self, key, value)

    def write_config(self):
        data = {}
        for key, value in self.__dict__.items():
            if value is None or isinstance(value, (str, int, float, bool)):
                data.update({key: value})
        with open(self.config_file, 'w', encoding='utf-8') as f:
            try:
                json.dump(data, f, ensure_ascii=False, indent=4)
            except Exception as e:
                if self.debug:
                    traceback.print_exc()
                pass
