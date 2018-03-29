import local_config

import http
import json
import time


def create_steamapi_connection():
    return http.client.HTTPConnection(
        "api.steampowered.com",
        timeout=10
    )

