#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main.py

標準入力で番号を選ばせて、対応する処理を user.py / champion.py に委譲するだけの
“薄い” エントリーポイント。API ロジックや分岐の詳細は各モジュール側で実装する。
"""

import sys

# --- あとで実装する自前モジュール -----------------
import user        # user.user_menu() などを想定
import champion    # champion.champion_menu() などを想定
# ----------------------------------------------------

MENU = """
=== Riot API CLI ===
1) ユーザー（サモナー）関連メニュー
2) チャンピオン関連メニュー
0) 終了
番号を入力 > """

def main() -> None:
    while True:
        choice = input(MENU).strip()

        if choice == "0":
            print("終了します。")
            break

        elif choice == "1":
            # user.py 側でさらに分岐・API 呼び出しを行う
            user.user_menu()

        elif choice == "2":
            # champion.py 側で処理を行う
            champion.champion_menu()

        else:
            print("無効な入力です。0, 1, 2 のいずれかを選択してください。\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCtrl‑C で終了しました。")
        sys.exit(0)
