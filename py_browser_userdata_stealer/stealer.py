#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import os
import sys

from .chromium_based import ChromiumBased

from . import indent_text


# Chromium based browser"s name, User Data path
chromium_browsers = (
    ("Google Chrome", os.path.normpath(os.getenv("LOCALAPPDATA") +
     "/Google/Chrome/User Data")),
    ("Microsoft Edge", os.path.normpath(os.getenv("LOCALAPPDATA") +
     "/Microsoft/Edge/User Data")),
    ("Opera", os.path.normpath(os.getenv("APPDATA") +
     "/Opera Software/Opera Stable")),
    ("Yandex Browser", os.path.normpath(os.getenv("LOCALAPPDATA") +
     "/Yandex/YandexBrowser/User Data"))
)


def main():
    print("Console app that searches for browser's "
          "credentials and saves it to .csv file\n")

    installed_browsers = [ChromiumBased(name, path) for name, path in
                          chromium_browsers if os.path.exists(path)]

    if not installed_browsers:
        sys.exit("No browsers found")

    out_file = "credentials.csv"
    with open(out_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")

        for browser in installed_browsers:
            print(browser.name + ":")

            credentials = browser.get_credentials()
            if credentials:
                print(indent_text(f"Found {len(credentials)} credentials"))
                error_count = sum(cr.password == "%ERROR%" for cr in credentials)
                if error_count > 0:
                    print(indent_text(f"At least {error_count} passwords failed"
                                      " to decrypt"))

                f.write(browser.name + "\n")
                writer.writerows(credentials)
                f.write("\n")
            else:
                print(indent_text("No credentials found"))

            print()

    if os.stat(out_file).st_size != 0:
        print(f"\nFile \"{out_file}\" has been successfully created")
    else:
        print(f"\nFile \"{out_file}\" wasn't created")
        os.remove(out_file)


if __name__ == "__main__":
    main()
