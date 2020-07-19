#!/usr/bin/env python
# -*- coding: utf-8 -*-


import json
from typing import AnyStr, Dict

import ujson as sdt_json


class Web2Docker(object):

    def create_container(self, *args, **kwargs): pass

    def remove_container(self, *args, **kwargs): pass

    def stop_container(self, *args, **kwargs): pass

    def list_container(self, *args, **kwargs): pass

    @staticmethod
    def to_json(data: Dict, *args, **kwargs) -> AnyStr:
        return sdt_json.dumps(data)

    @staticmethod
    def from_json(string: AnyStr, *args, **kwargs) -> Dict:
        return json.loads(string)

    @staticmethod
    def format_data_to_frontend():
        pass
