# The BEERWARE License (BEERWARE)
#
# Copyright (c) 2022 Author. All rights reserved.
#
# Licensed under the "THE BEER-WARE LICENSE" (Revision 42):
# vazw wrote this file. As long as you retain this notice you
# can do whatever you want with this stuff. If we meet some day, and you think
# this stuff is worth it, you can buy me a beer or coffee in return

import asyncio
import os

from vxma_d.AppData import Bot, ResetDatabase


def main():
    if not os.path.exists("vxma.db"):
        api_key = str(input("API_KEY ="))
        print(f"API {api_key}")
        api_sec = str(input("API_SEC ="))
        line_token = str(input("Line Notify Token ="))
        risk = int(input("risk per trade($) ="))
        min_balance = int((input("ยอดเงินขั้นต่ำที่จะให้หยุดบอท =")))
        ResetDatabase.resetDatabase(
            api_key, api_sec, line_token, risk, min_balance
        )

    while True:
        asyncio.run(Bot.run_bot())


if __name__ == "__main__":
    main()
