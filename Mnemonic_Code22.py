import os
import asyncio
import aiohttp
import logging
import platform
from datetime import datetime
from hdwallet import HDWallet
from hdwallet.symbols import BTC, ETH, TRX
from hdwallet.utils import generate_mnemonic
from rich.logging import RichHandler
from rich import print
import ctypes
import pyfiglet
import time


# Funktion zum langsamen Drucken von Text
def print_slow(text):
    for char in text:
        print(char, end='', flush=True)  # flush=True sorgt dafür, dass der Buchstabe sofort gedruckt wird
        time.sleep(0.01)  # Ändern Sie diesen Wert, um die Geschwindigkeit anzupassen
    print()  # Neue Zeile am Ende


# Funktion zur Anzeige von Systeminformationen
def display_system_info():
    system_info = platform.uname()

    print("[yellow]System Information:[/yellow]")

    print(f"    System: {system_info.system}")
    print(f"    Node Name: {system_info.node}")
    print(f"    Release: {system_info.release}")
    print(f"    Version: {system_info.version}")
    print(f"    Machine: {system_info.machine}")
    print(f"    Processor: {system_info.processor}")
    print(f"    Date and Time: [yellow]{datetime.now()}[/yellow]")
    print(f"    Telegram ID Admin: [cyan]https://t.me/Emanuill1[/cyan]")


# Funktion zum Abrufen des Aktivierungscodes vom Benutzer
def get_activation_code():
    return input("Enter activation code: ")


# Funktion zur Überprüfung des Aktivierungscodes
def validate_activation_code(code):
    # Beispielvalidierungslogik
    valid_activation_code = "0000"
    return code == valid_activation_code


# Funktion zur Validierung des Aktivierungscodes und zum Starten des Hauptprogramms
def validate_activation():
    while True:
        activation_code = get_activation_code()

        if validate_activation_code(activation_code):
            print("Activation code is valid. Proceeding with program execution.")
            return
        else:
            print("Invalid activation code. Please try again.")


# Ihr ASCII-Banner
ascii_banner = """
 _______  _______           _______ _________ _______  _______  _______  _______  _______  _        _______  _______
(  ____ \(  ____ )|\     /|(  ____ )\__   __/(  ___  )(  ____ \(  ____ )(  ___  )(  ____ \| \    /\(  ____ \(  ____ )
| (    \/| (    )|( \   / )| (    )|   ) (   | (   ) || (    \/| (    )|| (   ) || (    \/|  \  / /| (    \/| (    )|
| |      | (____)| \ (_) / | (____)|   | |   | |   | || |      | (____)|| (___) || |      |  (_/ / | (__    | (____)|
| |      |     __)  \   /  |  _____)   | |   | |   | || |      |     __)|  ___  || |      |   _ (  |  __)   |     __)
| |      | (\ (      ) (   | (         | |   | |   | || |      | (\ (   | (   ) || |      |  ( \ \ | (      | (\ (
| (____/\| ) \ \__   | |   | )         | |   | (___) || (____/\| ) \ \__| )   ( || (____/\|  /  \ \| (____/\| ) \ \__
(_______/|/   \__/   \_/   |/          )_(   (_______)(_______/|/   \__/|/     \|(_______/|_/    \/(_______/|/   \__/
                                                                                                                     
"""

# Printbanner langsam ausgeben
print_slow(ascii_banner)


# Anzeige von Systeminformationen
display_system_info()

# Logging-Konfiguration
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler()]
)

# Bitcoin-API-Endpunkte
BTC_API_ENDPOINTS = [
    "https://btc4.trezor.io/api/v2/address/",
    "https://blockstream.info/api/address/",
]

# Ethereum-API-Endpunkte
ETH_API_ENDPOINTS = [
    "https://eth1.trezor.io/api/v2/address/",
    "https://api.etherscan.io/api?module=account&action=balance&tag=latest&address=",
]

# TRON-API-Endpunkte (Verwendung des TRONSCAN-API)
TRX_API_ENDPOINTS = [
    "https://apilist.tronscan.org/api/account?address=",
]


class Settings:
    total_count = 0
    dry_count = 0
    wet_count = 0
    save_empty = "y"  # You need to define this variable according to your logic


async def check_apis(api_endpoints, symbol):
    working_apis = []
    async with aiohttp.ClientSession() as session:
        tasks = [check_api(session, endpoint, symbol) for endpoint in api_endpoints]
        results = await asyncio.gather(*tasks)
        for endpoint, result in zip(api_endpoints, results):
            if result:
                # logging.info(f"[green]API {endpoint} is functioning.[/green]")
                working_apis.append(endpoint)
            else:
                logging.error(f"[red]API {endpoint} is not available.[/red]")
    return working_apis


async def check_api(session, endpoint, symbol):
    try:
        test_address = (
            "1BoatSLRHtKNngkdXEeobR76b53LETtpyT"
            if symbol == BTC
            else "0xde0b295669a9fd93d5f28d9ec85e40f4cb697bae"
        )
        if symbol == TRX:
            test_address = "TBQkUY3dEnkPrZRkADHdmWn2jZktyxoTo1"
        url = f"{endpoint}{test_address}"
        async with session.get(url, timeout=10) as response:
            return response.status == 200
    except Exception as e:
        logging.error(f"[red]Error checking API {endpoint}: {e}[/red]")
        return False


async def get_balance(session, address, apis, symbol):
    tasks = [fetch_balance(session, endpoint, address, symbol) for endpoint in apis]
    results = await asyncio.gather(*tasks)
    return next((result for result in results if result is not None), None)


async def fetch_balance(session, endpoint, address, symbol):
    try:
        url = f"{endpoint}{address}"
        async with session.get(url, timeout=10) as response:
            if response.status == 200:
                data = await response.json()
                if symbol == BTC:
                    balance = int(data.get("balance", 0)) / 100000000
                elif symbol == ETH:
                    balance = int(data.get("balance", 0)) / 1000000000000000000
                elif symbol == TRX:
                    balance = int(data.get("balance", 0)) / 1000000
                return balance
    except Exception as e:
        logging.error(f"[red]Error in API request to {endpoint}: {e}[/red]")


def generate_wallet(symbol):
    mnemonic = generate_mnemonic(language="english", strength=128)
    hd_wallet = HDWallet(symbol=symbol)
    hd_wallet.from_mnemonic(mnemonic=mnemonic)
    address = hd_wallet.p2pkh_address()
    return mnemonic, address


async def check_internet():
    try:
        # Attempt to resolve a well-known host
        host = "www.google.com"
        await asyncio.get_event_loop().getaddrinfo(host, None)
    except Exception as e:
        logging.error("[red]Internet connection not available.[/red]")


async def main():
    # اعتبارسنجی کد فعال‌سازی قبل از شروع برنامه
    validate_activation()

    working_apis_btc = await check_apis(BTC_API_ENDPOINTS, BTC)
    working_apis_eth = await check_apis(ETH_API_ENDPOINTS, ETH)
    working_apis_trx = await check_apis(TRX_API_ENDPOINTS, TRX)

    if not (working_apis_btc or working_apis_eth or working_apis_trx):
        logging.error("[red]No APIs are currently available.[/red]")
        return

    counter = 0  # Counter for generated wallets
    total_balance = 0  # Total balance of checked seeds
    checked_seeds = 0  # Number of checked seeds

    async with aiohttp.ClientSession() as session:
        while True:
            try:
                btc_mnemonic, btc_address = generate_wallet(BTC)
                eth_mnemonic, eth_address = generate_wallet(ETH)
                trx_mnemonic, trx_address = generate_wallet(TRX)

                btc_balance = await get_balance(session, btc_address, working_apis_btc, BTC)
                eth_balance = await get_balance(session, eth_address, working_apis_eth, ETH)
                trx_balance = await get_balance(session, trx_address, working_apis_trx, TRX)

                if btc_balance is not None:
                    total_balance += btc_balance
                    checked_seeds += 1
                    if btc_balance > 0:
                        save_balance_and_seed(btc_mnemonic, btc_address, btc_balance, "BTC")
                if eth_balance is not None:
                    total_balance += eth_balance
                    checked_seeds += 1
                    if eth_balance > 0:
                        save_balance_and_seed(eth_mnemonic, eth_address, eth_balance, "ETH")
                if trx_balance is not None:
                    total_balance += trx_balance
                    checked_seeds += 1
                    if trx_balance > 0:
                        save_balance_and_seed(trx_mnemonic, trx_address, trx_balance, "TRX")

                print(f"[yellow]Mnemonic-Phrase BTC:[/yellow] {btc_mnemonic}")
                print(
                    f"[cyan]Bitcoin Address:[/cyan] {btc_address} -><><><><<><><><><><><>< [blue]Balance:[/blue] {btc_balance if btc_balance is not None else 'Request failed'}"
                )

                print(f"[green]Mnemonic-Phrase ETH:[/green] {eth_mnemonic}")
                print(
                    f"[cyan]Ethereum Address:[/cyan] {eth_address} -><><><><><><>< [blue]Balance:[/blue] {eth_balance if eth_balance is not None else 'Request failed'}"
                )

                print(f"[yellow]Mnemonic-Phrase TRX:[/yellow] {trx_mnemonic}")
                print(
                    f"[cyan]TRON Address:[/cyan] {trx_address} -><><><><><><><><><>><><><> [blue]Balance:[/blue] {trx_balance if trx_balance is not None else 'Request failed'}"
                )

                await check_internet()

                counter += 1
                print(f"[yellow]Number of generated wallets: {counter}[/yellow]")
                print(f"[yellow]Total balance of checked seeds: {total_balance}[/yellow]")
                print(f"[red]Number of checked seeds: {checked_seeds}[/red]")

                print(f"[yellow]{'=' * 21}  [yellow]Amir King[cyan] {'=' * 21} [cyan]https://t.me/Emanuill1[yellow]  {'=' * 25}\n")

                await asyncio.sleep(0.1)

                # Update console title
                Settings.total_count += 3
                if Settings.save_empty == "y":
                    ctypes.windll.kernel32.SetConsoleTitleW(
                        f" Hits $: {Settings.wet_count} - Total checks: {Settings.total_count}"
                    )
                else:
                    ctypes.windll.kernel32.SetConsoleTitleW(
                        f"Hits: {Settings.wet_count} - Total checks: {Settings.total_count}"
                    )

            except KeyboardInterrupt:
                logging.info("[yellow]Program manually terminated.[/yellow]")
                break
            except Exception as e:
                logging.error(f"[red]Unexpected error in main program: {e}[/red]")

    print("Contents of seeds:")
    try:
        for filename in os.listdir("seeds"):
            print(f"\n[bold]Contents of {filename}[/bold]:")
            with open(os.path.join("seeds", filename), "r") as f:
                print(f.read())
    except Exception as e:
        logging.error(f"[red]Error reading seeds directory: {e}[/red]")


def save_balance_and_seed(mnemonic, address, balance, symbol):
    directory = "seeds"
    if not os.path.exists(directory):
        os.makedirs(directory)
    filename = f"{symbol}_seed.txt"
    with open(os.path.join(directory, filename), "a") as f:
        f.write(f"Mnemonic Phrase: {mnemonic}\n")
        f.write(f"Address: {address}\n")
        f.write(f"Balance: {balance}\n\n")


if __name__ == "__main__":
    asyncio.run(main())
