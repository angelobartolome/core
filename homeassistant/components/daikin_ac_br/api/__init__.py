import json
import socket

import requests

from .encryption import ACUnitEncryptionService


class DaikinACBR:
    def __init__(self, host, key):
        self.key = key
        self.host = host
        self.port = 15914

        self.ac_unit_encryption_service = ACUnitEncryptionService(self.key)

    def fetch_data(self):
        status = self.get_status()
        return status

    def get_status(self):
        # Call the API and return the status
        url = f"http://{self.host}:{self.port}/acstatus"

        response = requests.request(
            "GET", url, headers={}, verify=False, allow_redirects=False
        )
        json_data = self.ac_unit_encryption_service.decrypt(response.text)

        # remove last char if it is not }
        if json_data[-1] != "}":
            json_data = json_data[:-1]

        print("Response from get_status: ", json_data)
        # Convert the json_data to a ACUnit object
        data = json.loads(json_data)

        return data

    def _send_with_socket(self, payload):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        host = self.host
        port = self.port
        s.connect((host, port))

        headers = "POST /acstatus HTTP/1.1\r\nContent-Type: {content_type}\r\nContent-Length: {content_length}\r\nHost: {host}\r\nConnection: close\r\n\r\n"

        body = payload
        body_bytes = body.encode("ascii")
        header_bytes = headers.format(
            content_type="application/x-www-form-urlencoded",
            content_length=len(body_bytes),
            host=str(host) + ":" + str(port),
        ).encode("iso-8859-1")

        payload = header_bytes + body_bytes
        print(payload)
        s.sendall(payload)

    # def turn_on(self):
    #     # Call the API to turn on the AC
    #     payload = {"port1": {"power": 1}, "src": 5}

    #     encrypted_payload = self.ac_unit_encryption_service.encrypt(json.dumps(payload))
    #     self._send_with_socket(encrypted_payload)
    #     return "AC turned on successfully!"

    # def turn_off(self):
    #     # Call the API to turn off the AC
    #     url = f"http://{self.host}:{self.port}/acstatus"
    #     payload = {"port1": {"power": 0}, "src": 5}

    #     encrypted_payload = self.ac_unit_encryption_service.encrypt(json.dumps(payload))
    #     self._send_with_socket(encrypted_payload)

    # # def set_fan_speed(self, speed):
    # #     payload = {"port1": {"fan": speed}, "src": 5}

    # #     encrypted_payload = self.ac_unit_encryption_service.encrypt(json.dumps(payload))
    # #     self._send_with_socket(encrypted_payload)

    def send_command(self, command):
        payload = {"port1": command, "src": 5}

        encrypted_payload = self.ac_unit_encryption_service.encrypt(json.dumps(payload))
        self._send_with_socket(encrypted_payload)
