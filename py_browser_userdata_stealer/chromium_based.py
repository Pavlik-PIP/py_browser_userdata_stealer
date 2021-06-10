import os
import json
import base64
import uuid
import shutil
import sqlite3
import textwrap

import win32crypt
from Crypto.Cipher import AES

class ChromiumBased:

    def __init__(self, name, user_data_path):
        self.name = name
        self.user_data_path = user_data_path

        self.is_yandex = "Yandex" in name

        self.local_state_path = os.path.join(user_data_path, "Local State")

        if self.is_yandex:
            self.database_path = os.path.join(user_data_path, "Default", "Ya Passman Data")
        else:
            self.database_path = os.path.join(user_data_path, "Default", "Login Data")

        indent = " "*4
        self.wrapper = textwrap.TextWrapper(initial_indent=indent, subsequent_indent=indent)

    def get_credentials(self):
        credentials = []

        temp_db = str(uuid.uuid4())
        shutil.copyfile(self.database_path, temp_db)

        try:
            conn = sqlite3.connect(temp_db)

            curs = conn.cursor()
            db_query = "SELECT origin_url, username_value, password_value FROM logins"
            curs.execute(db_query)

            logins_data = curs.fetchall()
        except sqlite3.DatabaseError as err:
            print(self.wrapper.fill("Error: {}".format(err)))
            return credentials
        finally:
            conn.close()
            os.remove(temp_db)

        if not logins_data:
            print(self.wrapper.fill("No credentials found"))
            return credentials

        key = self._get_key()

        for row in logins_data:
            url = row[0]
            username = row[1]
            encrypted_password = row[2]

            password = self._decrypt_password(encrypted_password, key)

            row = (url, username, password)
            credentials.append(row)

        return credentials

    def _get_key(self):
        with open(self.local_state_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            encrypted_key = data['os_crypt']['encrypted_key']

            encrypted_key = base64.b64decode(encrypted_key)

            DPAPI_prefix = "DPAPI"
            encrypted_key = encrypted_key[len(DPAPI_prefix):]

            key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]

        return key

    def _decrypt_password(self, encrypted_password, key):
        DPAPI_version_prefix = "v10"

        nonce_length = 12; # 96 / 8
        auth_tag_length = 16; # 128 / 8

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
