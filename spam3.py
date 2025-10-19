#!/usr/bin/env python3

import asyncio, aiohttp, json, sys, hashlib, getpass
from datetime import datetime
from pathlib import Path
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from colorama import Fore, Style, init
import itertools, time, os

init(autoreset=True)

# ===== CONFIG =====
API_ID = 11630722
API_HASH = "17992c34fb75f55adcf886b2892fce60"
TARGET_GROUP = "@khugiaitrisss"
SESSION_NAME = "vip_sender_online"
DELAY_SECONDS = 10 * 60  # 10 phút
PHONE = "+84939642195"
PASSWORD = ""
KEY_URL = "https://raw.githubusercontent.com/QuaTang382/sms/main/key.txt"  # Link Pastebin chứa key
# ===================

DATA_DIR = Path.home() / ".vip_bot_online"
DATA_DIR.mkdir(parents=True, exist_ok=True)
LAST_FILE = DATA_DIR / ".last_send"

def pretty_time(sec: int):
    m, s = divmod(sec, 60)
    return f"{m:02d}:{s:02d}"

def load_last_send():
    if not LAST_FILE.exists():
        return None
    try:
        data = json.loads(LAST_FILE.read_text())
        ts = data.get("time")
        return datetime.fromisoformat(ts) if ts else None
    except Exception:
        return None

def save_last_send(dt: datetime):
    LAST_FILE.write_text(json.dumps({"time": dt.isoformat()}))

async def check_key_online(user_key: str):
    """Kiểm tra key online từ Pastebin"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(KEY_URL) as resp:
                if resp.status != 200:
                    print(Fore.RED + "Không thể tải danh sách key online.")
                    return False, "Server lỗi"
                text = await resp.text()
        lines = text.strip().splitlines()
        for line in lines:
            if "|" in line:
                key, exp_str = line.strip().split("|", 1)
                if user_key.strip() == key.strip():
                    exp = datetime.fromisoformat(exp_str.strip())
                    if datetime.now() > exp:
                        return False, f"Key hết hạn ({exp.date()})"
                    return True, f"Hợp lệ đến {exp.date()}"
        return False, "Key không tồn tại"
    except Exception as e:
        return False, f"Lỗi khi kiểm tra key: {e}"

async def ensure_authorized(client: TelegramClient):
    """Đăng nhập Telegram"""
    if await client.is_user_authorized():
        return True
    try:
        await client.send_code_request(PHONE)
    except Exception as e:
        print(Fore.RED + f" Gửi mã lỗi: {e}")
        return False
    code = input(Fore.CYAN + "Nhập mã code do admin(lần đầu): ").strip()
    try:
        await client.sign_in(PHONE, code)
    except SessionPasswordNeededError:
        if not PASSWORD:
            print(Fore.RED + " Cần mật khẩu 2FA.")
            return False
        await client.sign_in(password=PASSWORD)
    return await client.is_user_authorized()

async def fancy_loading(text="Đang khởi động"):
    for c in itertools.cycle(["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]):
        sys.stdout.write(f"\r{Fore.MAGENTA}{text}... {c}")
        sys.stdout.flush()
        await asyncio.sleep(0.1)

async def countdown(seconds):
    while seconds:
        sys.stdout.write(f"\r{Fore.YELLOW}⏳ Đếm ngược: {pretty_time(seconds)}  ")
        sys.stdout.flush()
        await asyncio.sleep(1)
        seconds -= 1
    print(Fore.GREEN + "\n Hết thời gian chờ, có thể SPAM tiếp!")

async def main():
    print(Fore.MAGENTA + Style.BRIGHT + "\n=== SPAM VIP ===\n")

    user_key = getpass.getpass(Fore.YELLOW + "Nhập KEY của bạn: ").strip()
    ok, msg = await check_key_online(user_key)
    if not ok:
        print(Fore.RED + f"Key không hợp lệ: {msg}")
        return
    print(Fore.GREEN + f" Key hợp lệ ({msg})")

    spinner = asyncio.create_task(fancy_loading())
    await asyncio.sleep(3)
    spinner.cancel()
    print(Fore.CYAN + "\nLoading")

    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    await client.connect()
    if not await ensure_authorized(client):
        print(Fore.RED + "Lỗi")
        await client.disconnect()
        return

    me = await client.get_me()
    print(Fore.GREEN + f"welcome")

    while True:
        last = load_last_send()
        if last:
            elapsed = (datetime.now() - last).total_seconds()
            if elapsed < DELAY_SECONDS:
                remain = int(DELAY_SECONDS - elapsed)
                print(Fore.RED + f" còn {pretty_time(remain)}.")
                await countdown(remain)
            else:
                print(Fore.GREEN + "Đã hết thời gian chờ, có thể gửi.")
        phone_to_send = input(Fore.CYAN + "Nhập số điện thoại cần spam: ").strip()
        if not phone_to_send:
            print(Fore.RED + "sai")
            break

        msg = f"/vip {phone_to_send.lstrip('+')}"
        try:
            await client.send_message(TARGET_GROUP, msg)
            print(Fore.GREEN + f"Đã spam")
            save_last_send(datetime.now())
            print(Fore.YELLOW + " doi 10p...")
            await countdown(DELAY_SECONDS)
        except Exception as e:
            print(Fore.RED + f"Lỗi khi gửi: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:

        print(Fore.YELLOW + "\nĐã hủy bởi người dùng.")
