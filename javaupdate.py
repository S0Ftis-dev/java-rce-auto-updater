import os
import re
import sys
import json
import shutil
import zipfile
import tempfile
import subprocess
import urllib.request

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm
    from rich.progress import (
        Progress,
        SpinnerColumn,
        BarColumn,
        TextColumn,
        DownloadColumn,
        TransferSpeedColumn,
        TimeRemainingColumn,
    )
    from rich import box
except ImportError:
    print("Библиотека 'rich' не найдена. Установите её командой: pip install -r requirements.txt")
    input("Нажмите Enter для выхода...")
    sys.exit(1)

console = Console()

SEARCH_ROOTS = [
    os.environ.get("ProgramFiles", r"C:\Program Files"),
    os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
    os.environ.get("LOCALAPPDATA", ""),
    os.environ.get("APPDATA", ""),
]

# Исключения: системные установки, IDE и серверные лаунчеры с проверкой целостности файлов
SKIP_KEYWORDS = [
    r"\program files",
    r"\android studio",
    r"\.vimeworld",
    r"\streamcraft",
    r"\hackmine launcher",
    r"\.cristalix",
    r"\mcskill",
    r"\simpleminecraft",
    r"\excalibur-craft",
    r"\kaboom",
    r"\gravitycraft",
    r"\maintenance\trash",
    r".bak",
]

TARGET_MAJORS = {17, 21, 25, 27}


def find_java_executables():
    found = []
    for root_dir in SEARCH_ROOTS:
        if not root_dir or not os.path.exists(root_dir):
            continue
        for current_root, dirs, files in os.walk(root_dir):
            dirs[:] = [
                d for d in dirs
                if d.lower() not in {"cache", "code cache", "gpucache", "node_modules", ".git", "temp"}
                or "minecraft" in current_root.lower()
                or ".dawn" in current_root.lower()
            ]
            if "java.exe" in files:
                found.append(os.path.join(current_root, "java.exe"))
    return found


def parse_java_info(java_exe):
    try:
        res = subprocess.run([java_exe, "-version"], capture_output=True, text=True, timeout=5)
        output = (res.stderr or "") + "\n" + (res.stdout or "")
    except Exception:
        return None

    ver_match = re.search(r'version\s+"(\d+)(?:\.(\d+))?(?:\.(\d+))?(?:\.(\d+))?"', output)
    if not ver_match:
        return None

    major = int(ver_match.group(1))
    ver_tuple = tuple(int(g) if g is not None else 0 for g in ver_match.groups())
    ver_str = ".".join(str(g) for g in ver_match.groups() if g is not None)

    low = output.lower()
    if "temurin" in low:
        vendor = "Temurin"
    elif "zulu" in low:
        vendor = "Zulu"
    elif "microsoft" in low:
        vendor = "Microsoft"
    elif "java(tm)" in low or "hotspot(tm)" in low:
        vendor = "Oracle"
    else:
        vendor = "Temurin"

    bin_dir = os.path.dirname(java_exe)
    pkg_type = "jdk" if os.path.exists(os.path.join(bin_dir, "javac.exe")) else "jre"
    java_home = os.path.dirname(bin_dir)

    return {
        "exe": java_exe,
        "home": java_home,
        "major": major,
        "version_tuple": ver_tuple,
        "version_str": ver_str,
        "vendor": vendor,
        "type": pkg_type,
    }


def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "JavaAutoUpdater/1.2"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_latest_release(vendor, major, pkg_type):
    try:
        if vendor == "Temurin":
            url = f"https://api.adoptium.net/v3/assets/latest/{major}/hotspot?architecture=x64&image_type={pkg_type}&os=windows&vendor=eclipse"
            data = fetch_json(url)
            if not data and pkg_type == "jre":
                data = fetch_json(url.replace("image_type=jre", "image_type=jdk"))
            if data:
                v = data[0]["version"]
                ver_tuple = (v.get("major", 0), v.get("minor", 0), v.get("security", 0), v.get("patch", 0))
                return ver_tuple, v.get("semver", ""), data[0]["binary"]["package"]["link"]

        elif vendor == "Zulu":
            url = (
                f"https://api.azul.com/metadata/v1/zulu/packages/?java_version={major}"
                f"&os=windows&arch=x86&hw_bitness=64&ext=zip&bundle_type={pkg_type}"
                f"&javafx_bundled=false&release_status=ga&availability_types=CA&latest=true"
            )
            data = fetch_json(url)
            if not data and pkg_type == "jre":
                data = fetch_json(url.replace("bundle_type=jre", "bundle_type=jdk"))
            if data:
                jv = data[0]["java_version"]
                ver_tuple = tuple((jv + [0, 0, 0, 0])[:4])
                return ver_tuple, ".".join(map(str, jv)), data[0]["download_url"]

        elif vendor == "Microsoft":
            dl_url = f"https://aka.ms/download-jdk/microsoft-jdk-{major}-windows-x64.zip"
            req = urllib.request.Request(dl_url, method="HEAD", headers={"User-Agent": "JavaAutoUpdater/1.2"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                final_url = resp.geturl()
            m = re.search(r"microsoft-jdk-(\d+)\.(\d+)\.(\d+)(?:\.(\d+))?", final_url)
            if m:
                ver_tuple = tuple(int(g) if g is not None else 0 for g in m.groups())
                ver_str = ".".join(g for g in m.groups() if g is not None)
                return ver_tuple, ver_str, dl_url
    except Exception:
        pass
    return None, None, None


def download_with_progress(dl_url, cache_dir, key, label):
    target_extracted = os.path.join(cache_dir, key)
    if os.path.exists(target_extracted):
        return target_extracted

    zip_path = os.path.join(cache_dir, f"{key}.zip")
    req = urllib.request.Request(dl_url, headers={"User-Agent": "JavaAutoUpdater/1.2"})

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]{task.description}"),
        BarColumn(bar_width=30),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        with urllib.request.urlopen(req, timeout=120) as resp:
            total = int(resp.headers.get("Content-Length", 0))
            task_id = progress.add_task(f"Загрузка {label}", total=total or None)
            with open(zip_path, "wb") as out:
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    out.write(chunk)
                    progress.update(task_id, advance=len(chunk))

    extract_tmp = os.path.join(cache_dir, f"{key}_raw")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_tmp)

    for r, _, files in os.walk(extract_tmp):
        if "java.exe" in files and os.path.basename(r).lower() == "bin":
            shutil.move(os.path.dirname(r), target_extracted)
            return target_extracted

    raise RuntimeError("В архиве не найден bin/java.exe")


def shorten_path(path):
    user_profile = os.environ.get("USERPROFILE", "")
    if user_profile and path.lower().startswith(user_profile.lower()):
        return "~" + path[len(user_profile):]
    return path


def run_audit():
    with console.status("[bold cyan]Сканирование диска и проверка актуальных версий через REST API...[/]", spinner="dots"):
        executables = find_java_executables()
        api_cache = {}
        records = []

        for exe in executables:
            info = parse_java_info(exe)
            if not info:
                continue

            low_path = exe.lower()
            is_skipped = any(skip in low_path for skip in SKIP_KEYWORDS)

            if info["major"] not in TARGET_MAJORS:
                records.append((info, "Вне зоны риска", "-", "safe_legacy", None))
                continue

            if is_skipped:
                records.append((info, "Пропущено (Система/Серверный)", "-", "skipped", None))
                continue

            cache_key = (info["vendor"], info["major"], info["type"])
            if cache_key not in api_cache:
                api_cache[cache_key] = get_latest_release(*cache_key)

            latest_tuple, latest_str, dl_url = api_cache[cache_key]
            if not latest_tuple:
                records.append((info, "Ошибка API", "?", "unknown", None))
            elif info["version_tuple"] >= latest_tuple:
                records.append((info, "Актуальна", latest_str, "ok", None))
            else:
                records.append((info, "УЯЗВИМА / УСТАРЕЛА", latest_str, "vuln", dl_url))

    table = Table(
        title=f"Результаты аудита Java (найдено экземпляров: {len(records)})",
        box=box.ROUNDED,
        header_style="bold magenta",
        show_lines=True,
    )
    table.add_column("Дистрибутив", style="bold white", no_wrap=True)
    table.add_column("Текущая", justify="center")
    table.add_column("Последняя", justify="center", style="cyan")
    table.add_column("Статус", justify="center")
    table.add_column("Путь расположения", style="dim")

    vuln_items = []
    for info, status_text, latest_str, code, dl_url in records:
        vendor_label = f"{info['vendor']} {info['major']} ({info['type'].upper()})"
        if code == "vuln":
            badge = f"[bold red]⚠ {status_text}[/]"
            cur_ver = f"[red]{info['version_str']}[/]"
            vuln_items.append((info, latest_str, dl_url))
        elif code == "ok":
            badge = f"[bold green]✔ {status_text}[/]"
            cur_ver = f"[green]{info['version_str']}[/]"
        elif code == "skipped":
            badge = f"[yellow]• {status_text}[/]"
            cur_ver = info["version_str"]
        else:
            badge = f"[dim]{status_text}[/]"
            cur_ver = info["version_str"]

        table.add_row(vendor_label, cur_ver, str(latest_str), badge, shorten_path(info["home"]))

    console.print()
    console.print(table)
    return vuln_items


def update_vulnerable(vuln_items):
    if not vuln_items:
        console.print(Panel("[bold green]Уязвимых сборок не обнаружено. Обновление не требуется![/]", border_style="green"))
        return

    console.print(
        Panel(
            f"[bold yellow]Найдено уязвимых сборок: {len(vuln_items)}[/]\n"
            "[dim]Убедитесь, что все лаунчеры Minecraft (Prism, FTB, Dawn и др.) сейчас закрыты.[/]",
            border_style="yellow",
        )
    )

    if not Confirm.ask("Начать скачивание и обновление уязвимых сборок?", default=True):
        console.print("[yellow]Обновление отменено пользователем.[/]")
        return

    cache_dir = tempfile.mkdtemp(prefix="java_auto_updater_")
    updated_count = 0

    try:
        for info, latest_str, dl_url in vuln_items:
            label = f"{info['vendor']} {info['major']} ({info['type'].upper()}) -> {latest_str}"
            key = f"{info['vendor']}_{info['major']}_{info['type']}"
            try:
                fresh_home = download_with_progress(dl_url, cache_dir, key, label)
                backup_home = info["home"] + ".bak"
                if os.path.exists(backup_home):
                    shutil.rmtree(backup_home, ignore_errors=True)

                os.rename(info["home"], backup_home)
                shutil.copytree(fresh_home, info["home"])
                updated_count += 1
                console.print(f"  [bold green]✔ Обновлено:[/] {shorten_path(info['home'])} [dim]({info['version_str']} → {latest_str})[/]")
            except Exception as e:
                console.print(f"  [bold red]✘ Ошибка:[/] {shorten_path(info['home'])} — [red]{e}[/]")
    finally:
        shutil.rmtree(cache_dir, ignore_errors=True)

    console.print(
        Panel(
            f"[bold green]Готово![/] Успешно обновлено сборок: [bold]{updated_count} из {len(vuln_items)}[/].",
            border_style="green",
        )
    )


def clean_backups():
    bak_list = []
    with console.status("[bold yellow]Поиск резервных копий (.bak)...[/]"):
        for root_dir in [os.environ.get("LOCALAPPDATA", ""), os.environ.get("APPDATA", "")]:
            if not root_dir or not os.path.exists(root_dir):
                continue
            for current_root, dirs, _ in os.walk(root_dir):
                for d in list(dirs):
                    if d.endswith(".bak"):
                        bak_list.append(os.path.join(current_root, d))
                        dirs.remove(d)

    if not bak_list:
        console.print(Panel("[cyan]Резервных копий (.bak) не найдено.[/]", border_style="cyan"))
        return

    console.print(f"\nНайдено резервных копий: [bold yellow]{len(bak_list)}[/]")
    for b in bak_list:
        console.print(f"  [dim]• {shorten_path(b)}[/]")

    if Confirm.ask("\nУдалить все найденные .bak папки безвозвратно?", default=True):
        for b in bak_list:
            shutil.rmtree(b, ignore_errors=True)
        console.print(Panel(f"[bold green]Очистка завершена.[/] Удалено папок: [bold]{len(bak_list)}[/]", border_style="green"))


def main():
    while True:
        console.clear()
        console.print(
            Panel.fit(
                "[bold white]Java RCE Auto-Updater[/] [dim]v1.2[/]\n"
                "[cyan]Интерактивный аудит и обновление Java-рантаймов в лаунчерах Minecraft[/]",
                border_style="bright_blue",
                box=box.ROUNDED,
            )
        )

        console.print("\n[bold white]Выберите действие:[/]")
        console.print("  [bold cyan][1][/] Проверить систему (только аудит и таблица статусов)")
        console.print("  [bold green][2][/] Проверить и автоматически обновить уязвимые сборки")
        console.print("  [bold yellow][3][/] Удалить старые резервные копии (.bak)")
        console.print("  [bold red][0][/] Выход\n")

        choice = Prompt.ask("Введите номер пункта", choices=["1", "2", "3", "0"], default="2")

        if choice == "1":
            run_audit()
            Prompt.ask("\n[dim]Нажмите Enter, чтобы вернуться в меню[/]", default="")
        elif choice == "2":
            vuln = run_audit()
            update_vulnerable(vuln)
            Prompt.ask("\n[dim]Нажмите Enter, чтобы вернуться в меню[/]", default="")
        elif choice == "3":
            clean_backups()
            Prompt.ask("\n[dim]Нажмите Enter, чтобы вернуться в меню[/]", default="")
        elif choice == "0":
            console.print("[dim]Выход из программы.[/]")
            break


if __name__ == "__main__":
    main()
