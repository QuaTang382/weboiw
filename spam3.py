#!/usr/bin/env python3

import asyncio, aiohttp, json, sys, getpass, os
from datetime import datetime
from pathlib import Path
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from colorama import Fore, Style, init
import itertools

init(autoreset=True)

# ===== CONFIG =====
API_ID = 23541688
API_HASH = "c8c5b0b2a0e15badc4133e0d27c7f017"
TARGET_GROUP = "@khugiaitrisss"
SESSION_NAME = "vip_sender_online"
DELAY_SECONDS = 10 * 60  # 10 phút
PHONE = "+84862367753"
PASSWORD = "Demo@123"
KEY_URL = "https://raw.githubusercontent.com/QuaTang382/sms/main/key.txt"
MAINTENANCE_URL = "https://raw.githubusercontent.com/QuaTang382/sms/main/baotri.txt"
# ===================

DATA_DIR = Path.home() / ".vip_bot_online"
DATA_DIR.mkdir(parents=True, exist_ok=True)
LAST_FILE = DATA_DIR / ".last_send.json"


def pretty_time(sec: int):
    m, s = divmod(sec, 60)
    return f"{m:02d}:{s:02d}"


def load_last_send():
    if not LAST_FILE.exists():
        return {}
    try:
        data = json.loads(LAST_FILE.read_text())
        return {k: datetime.fromisoformat(v) for k, v in data.items()}
    except Exception:
        return {}


def save_last_send(data: dict):
    serializable = {k: v.isoformat() for k, v in data.items()}
    LAST_FILE.write_text(json.dumps(serializable, indent=2))


async def check_key_online(user_key: str):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(KEY_URL) as resp:
                if resp.status != 200:
                    print(Fore.RED + "Không thể tải danh sách key online.")
                    return False, "Server lỗi"
                text = await resp.text()
        for line in text.strip().splitlines():
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
    if await client.is_user_authorized():
        return True
    try:
        await client.send_code_request(PHONE)
    except Exception as e:
        print(Fore.RED + f"Gửi mã lỗi: {e}")
        return False
    code = input(Fore.CYAN + "Nhập mã(chỉ 1 lần): ").strip()
    try:
        await client.sign_in(PHONE, code)
    except SessionPasswordNeededError:
        if not PASSWORD:
            print(Fore.RED + "Cần mật khẩu 2FA.")
            return False
        await client.sign_in(password=PASSWORD)
    return await client.is_user_authorized()


async def fancy_loading(text="Đang khởi động"):
    for c in itertools.cycle(["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]):
        sys.stdout.write(f"\r{Fore.MAGENTA}{text}... {c}")
        sys.stdout.flush()
        await asyncio.sleep(0.1)


async def countdown(seconds, prefix="Đếm ngược"):
    while seconds > 0:
        sys.stdout.write(f"\r{Fore.YELLOW}⏳ {prefix}: {pretty_time(seconds)}  ")
        sys.stdout.flush()
        await asyncio.sleep(1)
        seconds -= 1
    print(Fore.GREEN + "\nHết thời gian chờ!")


async def safe_connect():
    """Kết nối Telegram, tự xử lý lỗi database is locked"""
    while True:
        try:
            client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
            await client.connect()
            return client
        except Exception as e:
            if "database is locked" in str(e).lower():
                print(Fore.RED + "⚠️ Lỗi database is locked → đang xoá session cũ...")
                try:
                    os.remove(f"{SESSION_NAME}.session")
                    await asyncio.sleep(1)
                except FileNotFoundError:
                    pass
                continue
            else:
                raise

async def check_maintenance():
    """Kiểm tra trạng thái bảo trì online"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(MAINTENANCE_URL) as resp:
                if resp.status == 200:
                    text = (await resp.text()).strip().lower()
                    if "on" in text:
                        print(Fore.RED + "\n🚧 Tool đang bảo trì. Vui lòng quay lại sau.")
                        return True
    except Exception as e:
        print(Fore.YELLOW + f"Lỗi khi kiểm tra bảo trì: {e}")
    return False
async def main():
    print(Fore.MAGENTA + Style.BRIGHT + "\n=== SPAM VIP ===\n")
    # Kiểm tra bảo trì
    if await check_maintenance():
        return

    user_key = getpass.getpass(Fore.YELLOW + "Nhập KEY của bạn: ").strip()
    ok, msg = await check_key_online(user_key)
    if not ok:
        print(Fore.RED + f"Key không hợp lệ: {msg}")
        return
    print(Fore.GREEN + f" Key hợp lệ ({msg})")

    spinner = asyncio.create_task(fancy_loading())
    await asyncio.sleep(2)
    spinner.cancel()
    print(Fore.CYAN + "\nĐang khởi tạo...")

    client = await safe_connect()
    if not await ensure_authorized(client):
        print(Fore.RED + "Lỗi đăng nhập Telegram.")
        await client.disconnect()
        return

    me = await client.get_me()
    print(Fore.GREEN + f"Xin chào!\n")

    last_send = load_last_send()

    phone_to_send = input(Fore.CYAN + "Nhập số điện thoại cần spam: ").strip()
    if not phone_to_send:
        print(Fore.RED + "Không được để trống!")
        await client.disconnect()
        return

    phone_to_send = phone_to_send.lstrip('+')
    msg = f"/vip {phone_to_send}"

    now = datetime.now()
    if phone_to_send in last_send:
        elapsed = (now - last_send[phone_to_send]).total_seconds()
        if elapsed < DELAY_SECONDS:
            remain = int(DELAY_SECONDS - elapsed)
            print(Fore.RED + f"Số {phone_to_send} đang delay ({pretty_time(remain)} còn lại).")
            await countdown(remain, prefix=f"Số {phone_to_send}")
        else:
            print(Fore.GREEN + f"Số {phone_to_send} đã hết delay, có thể gửi.")
    else:
        print(Fore.GREEN + f"Số {phone_to_send} là số khác, đã spam.")

    try:
        await client.send_message(TARGET_GROUP, msg)
        print(Fore.GREEN + f"Đã gửi spam {phone_to_send}")
        last_send[phone_to_send] = datetime.now()
        save_last_send(last_send)
        print(Fore.YELLOW + f"⏳ Đã lưu delay 10 phút cho {phone_to_send}")
    except Exception as e:
        print(Fore.RED + f"Lỗi khi gửi: {e}")

    # 🔒 Đóng client + thoát để tránh bị database locked
    await client.disconnect()
    print(Fore.CYAN + "\ntool tự thoát để tránh database locked.")
    sys.exit(0)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\nĐã hủy bởi người dùng.")

