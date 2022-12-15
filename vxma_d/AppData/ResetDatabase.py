# The BEERWARE License (BEERWARE)
#
# Copyright (c) 2022 Author. All rights reserved.
#
# Licensed under the "THE BEER-WARE LICENSE" (Revision 42):
# vazw wrote this file. As long as you retain this notice you
# can do whatever you want with this stuff. If we meet some day, and you think
# this stuff is worth it, you can buy me a beer or coffee in return
import sqlite3

import bcrypt
import pandas as pd

barsC = 1502
pwd = "vxmaBot"
id = "vxma"


dropkey = "DROP TABLE key"

# 5
sql_create_key = """CREATE TABLE IF NOT EXISTS key (
                                    API_KEY TEXT PRIMARY KEY,
                                    API_SEC REAL NOT NULL,
                                    LINE_TK TEXT NOT NULL,
                                    RISK TEXT NOT NULL,
                                    MINBALANCE TEXT NOT NULL
                                )"""


def cKey():
    try:
        with sqlite3.connect(
            "vxma_d/AppData/vxma.db", check_same_thread=False
        ) as con:
            cur = con.cursor()
            cur.execute(sql_create_key)
            con.commit()
        print("success : key")
    except sqlite3.Error as e:
        print(e)
        print("Fail to create table : key")


def newUser(api_key, api_sec, line_token, risk, min_balance):
    data = pd.DataFrame(
        columns=["API_KEY", "API_SEC", "LINE_TK", "RISK", "MINBALANCE"]
    )
    try:
        compo = [api_key, api_sec, line_token, risk, min_balance]
        data.loc[1] = compo
        data = data.set_index("API_KEY")
        with sqlite3.connect(
            "vxma_d/AppData/vxma.db", check_same_thread=False
        ) as con:
            data.to_sql(
                "key",
                con=con,
                if_exists="replace",
                index=True,
                index_label="API_KEY",
            )
            con.commit()
        print("success setting!")
    except sqlite3.Error as e:
        print(e)
        print("fail")


def dropT():
    try:
        with sqlite3.connect(
            "vxma_d/AppData/vxma.db", check_same_thread=False
        ) as con:
            cur = con.cursor()
            cur.execute(dropkey)
            con.commit()
        print("success : Drop")
    except sqlite3.Error as e:
        print(e)
        print("Fail to drop table!")


def resetDatabase(api_key, api_sec, line_token, risk, min_balance):
    dropT()
    cKey()
    newUser(api_key, api_sec, line_token, risk, min_balance)
