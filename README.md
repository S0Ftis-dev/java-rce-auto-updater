# 🛡️ Java RCE Auto-Updater

**[🇬🇧 English](#-english) | [🇷🇺 Русский](#-русский)**

---

## 🇬🇧 English

Interactive console utility in **Python** to audit and automatically update vulnerable Java runtimes (**Java 17, 21, 25, 27**) embedded inside standard Minecraft launchers (PrismLauncher, FTB App, Dawn Launcher, CurseForge, MultiMC, etc.).

### ✨ Features
- **Auto-Discovery:** Recursively scans `Program Files`, `AppData\Local`, and `AppData\Roaming` for `java.exe` instances.
- **Vendor-Aware Updates:** Identifies the exact distribution (**Eclipse Temurin**, **Azul Zulu**, **Microsoft Build of OpenJDK**) and downloads the latest secure release directly from official vendor REST APIs.
- **Runtimes Only:** Updates **only** the embedded Java runtime directories (`JRE`/`JDK`) inside standalone launchers — it does **not** update launcher executables or game files.
- **Server Launchers Excluded:** Automatically skips dedicated server-project launchers built for playing on specific servers (such as **VimeWorld**, **StreamCraft**, **HackMine**, **Cristalix**, **McSkill**, etc.), as well as system MSI installations and IDEs. Those server launchers verify file integrity/hashes on startup and update their own Java builds through their built-in updaters.
- **Safe Backups:** Creates `.bak` backups before replacing any directory and includes a built-in cleanup option.

### 🚀 Quick Start
1. **Close all running Minecraft instances and launchers.**
2. Clone the repository and install dependencies:
   ```bash
   git clone https://github.com/S0Ftis-dev/java-rce-auto-updater.git
   cd java-rce-auto-updater
   pip install -r requirements.txt
   ```
3. Run the interactive menu:
   ```bash
   python java_updater.py
   ```

### 📋 Menu Options
- **`[1]` Audit System:** Scans all Java installations and displays a status table (`✔ Up to date` / `⚠ Vulnerable`).
- **`[2]` Audit & Update:** Downloads the latest official builds for outdated launcher runtimes and updates them safely (creating `.bak` backups).
- **`[3]` Clean Backups:** Finds and removes `.bak` folders after you verify that your modpacks launch properly.
- **`[0]` Exit**

### ⚠️ Disclaimer
Use at your own risk. Always make sure your launchers are closed before running option `[2]`. Dedicated server launchers (VimeWorld, StreamCraft, HackMine, etc.) manage their own Java runtimes via official project updaters and must be updated by launching them normally. This project is not affiliated with Mojang Studios, Microsoft, Eclipse Adoptium, or Azul Systems.

---

## 🇷🇺 Русский

Интерактивная консольная утилита на **Python** для аудита и автоматического обновления уязвимых версий Java (**Java 17, 21, 25, 27**), вшитых в обычные лаунчеры Minecraft (PrismLauncher, FTB App, Dawn Launcher, CurseForge, MultiMC и др.).

### ✨ Возможности
- **Автопоиск:** рекурсивно сканирует `Program Files`, `AppData\Local` и `AppData\Roaming` в поиске всех установленных `java.exe`.
- **Учёт дистрибутива:** определяет точного производителя (**Eclipse Temurin**, **Azul Zulu**, **Microsoft Build of OpenJDK**) и скачивает свежий безопасный релиз напрямую через официальные REST API разработчиков, сохраняя совместимость с модпаками.
- **Только Java-рантаймы:** скрипт обновляет **исключительно** папки с Java (`JRE`/`JDK`) внутри универсальных лаунчеров и не затрагивает файлы самих лаунчеров или клиентов.
- **Серверные лаунчеры не трогаются:** скрипт автоматически пропускает лаунчеры, созданные для игры на серверах конкретных проектов (**VimeWorld**, **StreamCraft**, **HackMine**, **Cristalix**, **McSkill** и др.), а также системные установки и IDE. Серверные лаунчеры при запуске проверяют хеши файлов и обновляют свою Java самостоятельно через встроенный апдейтер проекта.
- **Резервные копии:** перед заменой создаёт папки `.bak`, которые можно удалить одним нажатием после проверки работы сборок.

### 🚀 Быстрый старт
1. **Закройте все запущенные окна Minecraft и лаунчеры.**
2. Склонируйте репозиторий и установите зависимости:
   ```bash
   git clone https://github.com/S0Ftis-dev/java-rce-auto-updater.git
   cd java-rce-auto-updater
   pip install -r requirements.txt
   ```
3. Запустите интерактивное меню:
   ```bash
   python java_updater.py
   ```

### 📋 Пункты меню
- **`[1]` Проверить систему:** строит таблицу всех найденных Java и показывает, какие из них актуальны, а какие устарели.
- **`[2]` Проверить и обновить:** скачивает новейшие официальные сборки для устаревших папок лаунчеров и безопасно обновляет их с созданием `.bak`.
- **`[3]` Удалить резервные копии (.bak):** очищает диск от старых копий после того, как вы проверите запуск своих сборок.
- **`[0]` Выход**

### ⚠️ Дисклеймер
Используйте на свой страх и риск. Перед запуском пункта `[2]` обязательно закройте все лаунчеры. Серверные лаунчеры (VimeWorld, StreamCraft, HackMine и аналогичные) обновляют Java силами разработчиков самого проекта при запуске лаунчера. Проект не связан с Mojang Studios, Microsoft, Eclipse Adoptium или Azul Systems.
## 📄 License / Лицензия

This project is licensed under **CC BY-NC-SA 4.0** (Attribution-NonCommercial-ShareAlike 4.0 International) — free for personal use and modification, commercial use is prohibited, and any modified versions must remain open-source under the same license.

Проект распространяется под лицензией **CC BY-NC-SA 4.0** — разрешено бесплатное использование и модификация, коммерческое использование запрещено, а любые изменённые версии должны распространяться с открытым исходным кодом под той же лицензией.