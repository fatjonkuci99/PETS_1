"""
Utilities for client communication with the trusted server.
You should not need to change this file.
"""

import json
import time
from typing import Union, Tuple

import requests

from secret_sharing import Share


def sanitize_url_param(url_param: Union[bytes, str]) -> str:
    """
    Sanitize URL parameter to be URL-safe.
    """
    if isinstance(url_param, bytes):
        # Mypy "dislikes" variable redefinition.
        url_param = url_param.decode("ASCII") # type: ignore

    # %2F is indistinguishable from / due to WSGI standard.
    url_param = url_param.replace(r"%2F", "_").replace(r"%2f", "_")

    return url_param.replace("/", "_").replace("+", "-") # type: ignore


class Communication:
    """
    Network communications with the server.

    Attributes:
        server_host: hostname of the server
        server_port: port of the server
        client_id: Identifier of this client
        poll_delay: delay between requests in seconds (default: 0.2 s)
        protocol: network protocol to use (default: "http")
    """

    def __init__(
            self,
            server_host: str,
            server_port: int,
            client_id: str,
            poll_delay: float = 0.2,
            protocol: str = "http"
    ):
        self.base_url = f"{protocol}://{server_host}:{server_port}"
        self.client_id = client_id
        self.poll_delay = poll_delay


    def send_private_message(
            self,
            receiver_id: str,
            label: str,
            message: Union[bytes, str]
        ) -> None:
        """
        Send a private message to the receiver with a given label.
        """

        client_id_san = sanitize_url_param(self.client_id)
        receiver_id_san = sanitize_url_param(receiver_id)
        label_san = sanitize_url_param(label)

        url = f"{self.base_url}/private/{client_id_san}/{receiver_id_san}/{label_san}"
        print(f"POST {url}")
        requests.post(url, message)


    def retrieve_private_message(
            self,
            label: str
        ) -> bytes:
        """
        Retrieve a private message for a given label.
        """

        client_id_san = sanitize_url_param(self.client_id)
        label_san = sanitize_url_param(label)

        url = f"{self.base_url}/private/{client_id_san}/{label_san}"
        # We can either use a websocket, or do some polling, but websockets would require asyncio.
        # So we are doing polling to avoid introducing a new programming paradigm.
        while True:
            print(f"GET  {url}")
            res = requests.get(url)
            if res.status_code == 200:
                return res.content
            time.sleep(self.poll_delay)


    def publish_message(
            self,
            label: str,
            message: Union[bytes, str]
        ) -> None:
        """
        Publish a message on the server with a given label. This acts as a broadcast.
        """

        client_id_san = sanitize_url_param(self.client_id)
        label_san = sanitize_url_param(label)

        url = f"{self.base_url}/public/{client_id_san}/{label_san}"
        print(f"POST {url}")
        requests.post(url, message)


    def retrieve_public_message(
            self,
            sender_id: str,
            label: str
        ) -> bytes:
        """
        Retrieve a public message from the server. This receives a
        broadcast message. You have to supply both the label as well as the
        identity of the sender.
        """

        client_id_san = sanitize_url_param(self.client_id)
        sender_id_san = sanitize_url_param(sender_id)
        label_san = sanitize_url_param(label)

        url = f"{self.base_url}/public/{client_id_san}/{sender_id_san}/{label_san}"

        # We can either use a websocket, or do some polling, but websockets would require asyncio.
        # So we are doing polling to avoid introducing a new programming paradigm.
        while True:
            print(f"GET  {url}")
            res = requests.get(url)
            if res.status_code == 200:
                return res.content
            time.sleep(self.poll_delay)


    def retrieve_beaver_triplet_shares(
            self,
            op_id: str
        ) -> Tuple[Share, Share, Share]:
        """
        Retrieve a triplet of shares generated by the trusted server.

        This method automatically encodes the current client's identifier in
        the request. You will have to implement the trusted parameter generator
        in `ttp.py` to enable the server to handle it.
        """

        client_id_san = sanitize_url_param(self.client_id)
        op_id_san = sanitize_url_param(op_id)

        url = f"{self.base_url}/shares/{client_id_san}/{op_id_san}"
        print(f"GET  {url}")

        res = requests.get(url)
        return tuple([Share.deserialize(s) for s in json.loads(res.text)]) # type: ignore
