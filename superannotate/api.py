import json
import logging

import requests
import requests_toolbelt
import urllib3

from .exceptions import SABaseException
from .version import Version

logger = logging.getLogger("superannotate-python-sdk")


class API:
    __instance = None

    def __init__(self):
        self._api_config = None
        self._token = None
        self._verify = None
        self._session = None
        self._default_headers = None
        self._main_endpoint = None
        self.team_id = None
        if API.__instance is not None:
            raise SABaseException(0, "API class is a singleton!")
        API.__instance = self

    def set_auth(self, config_location):
        self._api_config = json.load(open(config_location))

        self._token = self._api_config["token"]
        self.team_id = int(self._token.split("=")[1])

        self._default_headers = {'Authorization': self._token}
        self._default_headers["authtype"] = "sdk"
        if "authtype" in self._api_config:
            self._default_headers["authtype"] = self._api_config["authtype"]
        self._default_headers['User-Agent'] = requests_toolbelt.user_agent(
            'superannotate', Version
        )

        self._main_endpoint = "https://api.annotate.online"
        if "main_endpoint" in self._api_config:
            self._main_endpoint = self._api_config["main_endpoint"]
        self._verify = True
        self._session = None
        response = self.send_request(
            req_type='GET',
            path='/projects',
            params={
                'team_id': str(self.team_id),
                'offset': 0,
                'limit': 1
            }
        )
        if not response.ok:
            self._session = None
            if "Not authorized" in response.text:
                raise SABaseException(0, "Couldn't authorize")
            raise SABaseException(0, "Couldn't reach superannotate")

    @staticmethod
    def get_instance():
        if API.__instance is None:
            API()
        return API.__instance

    def send_request(self, req_type, path, params=None, json_req=None):
        url = self._main_endpoint + path

        req = requests.Request(
            method=req_type, url=url, json=json_req, params=params
        )
        if self._session is None:
            self._session = self._create_session()
        prepared = self._session.prepare_request(req)
        resp = self._session.send(request=prepared, verify=self._verify)
        return resp

    def _create_session(self):
        session = requests.Session()
        retry = urllib3.Retry(
            total=5,
            read=5,
            connect=5,
            backoff_factor=0.3,
            # use on any request type
            method_whitelist=False,
            # force retry on those status responses
            status_forcelist=(501, 502, 503, 504, 505, 506, 507, 508, 510, 511),
            raise_on_status=False
        )
        adapter = requests.adapters.HTTPAdapter(
            max_retries=retry, pool_maxsize=16, pool_connections=16
        )
        session.mount('https://', adapter)
        session.mount('http://', adapter)
        session.headers = self._default_headers
        return session
