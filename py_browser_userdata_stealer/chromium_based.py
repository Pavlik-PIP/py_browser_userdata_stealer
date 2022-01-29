import base64
import json
import os
import shutil
import sqlite3
from tempfile import NamedTemporaryFile

import win32crypt
from Crypto.Cipher import AES

from . import indent_text

class ChromiumBased:

    def __init__(self, name, user_data_path):
        self.name = name
        self.user_data_path = user_data_path
        self.local_state_path = os.path.join(user_data_path, "Local State")
        self.database_paths = self._get_database_paths()

        self.is_yandex = "Yandex" in name

        self.key = self._get_key()

    def _get_database_paths(self):
        databases = set()

        # Empty string means current dir, without a profile
        profiles = {"Default", ""}

        for f in os.listdir(self.user_data_path):
            f_path = os.path.join(self.user_data_path, f)
            if os.path.isdir(f_path) and "profile" in f.lower():
                profiles.add(f)

        # Add profiles from Local State
        with open(self.local_state_path, "r", encoding="utf-8") as f:
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

    def get_credentials(self):
        credentials = []

        for db in self.database_paths:
            temp_db = NamedTemporaryFile(delete=False)
            shutil.copyfile(db, temp_db.name)

            try:
                conn = sqlite3.connect(temp_db.name)
                curs = conn.cursor()
                db_query = "SELECT origin_url, username_value, password_value FROM logins"
                curs.execute(db_query)
                logins_data = curs.fetchall()
            except sqlite3.DatabaseError as e:
                print(indent_text("Error with {}: {}".format(db, e)))
                continue
            finally:
                conn.close()
                del temp_db

            if not logins_data:
                continue

            for row in logins_data:
                url = row[0]
                username = row[1]
                encrypted_password = row[2]

                password = self._decrypt_password(encrypted_password, self.key)

                row = (url, username, password)
                credentials.append(row)

        return credentials

    def _get_key(self):
        with open(self.local_state_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            encrypted_key = data["os_crypt"]["encrypted_key"]

        encrypted_key = base64.b64decode(encrypted_key)

        DPAPI_prefix = "DPAPI"
        encrypted_key = encrypted_key[len(DPAPI_prefix):]

        key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]

        return key

    def _decrypt_password(self, encrypted_password, key):
        DPAPI_version_prefix = "v10"

        nonce_length = 12 # 96 / 8
        auth_tag_length = 16 # 128 / 8

        if not self.is_yandex:
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
