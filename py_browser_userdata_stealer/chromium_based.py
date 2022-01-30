import base64
from collections import namedtuple
import json
import os
import shutil
import sqlite3
from tempfile import NamedTemporaryFile
from typing import Any, List

import win32crypt
from Crypto.Cipher import AES

from . import indent_text

Credentials = namedtuple("Credentials", ["url", "username", "password"])


class ChromiumBased:
    def __init__(self, name: str, user_data_path: str) -> None:
        self.name = name
        self.user_data_path = user_data_path
        self._local_state_path = os.path.join(user_data_path, "Local State")
        self._database_paths = self._get_database_paths()

        self._is_yandex = "Yandex" in name

        self._key = self._get_key()

    def _get_database_paths(self) -> List[str]:
        databases = set()

        # Empty string means current dir, without a profile
        profiles = {"Default", ""}

        for f in os.listdir(self.user_data_path):
            f_path = os.path.join(self.user_data_path, f)
            if os.path.isdir(f_path) and "profile" in f.lower():
                profiles.add(f)

        # Add profiles from Local State
        with open(self._local_state_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                profiles |= set(data["profile"]["info_cache"])
            except:
                pass

        for profile in profiles:
            files = os.listdir(os.path.join(self.user_data_path, profile))
            for db in files:
                if db.lower() in ("login data", "ya passman data"):
                    databases.add(os.path.join(self.user_data_path, profile, db))

        return databases

    def get_credentials(self) -> List[Credentials]:
        credentials = []

        for db in self._database_paths:
            temp_db = NamedTemporaryFile(delete=False)
            shutil.copyfile(db, temp_db.name)

            try:
                with sqlite3.connect(temp_db.name) as conn:
                    db_query = "SELECT origin_url, username_value, " \
                               "password_value FROM logins"
                    logins_data = conn.execute(db_query).fetchall()
            except sqlite3.DatabaseError as e:
                print(indent_text(f"Error with {db}: {e}"))
                continue
            finally:
                del temp_db

            if not logins_data:
                continue

            for row in logins_data:
                url = row[0]
                username = row[1]
                encrypted_password = row[2]

                password = self._decrypt_password(encrypted_password, self._key)

                credentials.append(Credentials(url, username, password))

        return credentials

    def _get_key(self) -> Any:
        with open(self._local_state_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            encrypted_key = data["os_crypt"]["encrypted_key"]

        encrypted_key = base64.b64decode(encrypted_key)

        DPAPI_prefix = "DPAPI"
        encrypted_key = encrypted_key[len(DPAPI_prefix):]

        key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]

        return key

    def _decrypt_password(self, encrypted_password: bytes, key: bytes) -> str:
        DPAPI_version_prefix = "v10"

        nonce_length = 12  # 96 / 8
        auth_tag_length = 16  # 128 / 8

        if not self._is_yandex:
            encrypted_password = encrypted_password[len(DPAPI_version_prefix):]

        nonce = encrypted_password[:nonce_length]
        encrypted_password = encrypted_password[nonce_length:-auth_tag_length]

        cipher = AES.new(key, AES.MODE_GCM, nonce)
        password = cipher.decrypt(encrypted_password)
        try:
            password = password.decode("utf-8")
        except:
            password = "%ERROR%"

        return password
