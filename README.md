<div align="center">

<img src="1.ico" alt="ZapretTester" width="80" height="80"/>

# ZapretTester

**GUI-оболочка для Zapret — Discord, YouTube и другие заблокированные сервисы**

[![Windows](https://img.shields.io/badge/Windows-10%20%2F%2011-0078D4?style=for-the-badge&logo=windows&logoColor=white)](https://github.com/bpm500/ZapretTester)
[![Python](https://img.shields.io/badge/Python-3.13%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![PyQt6](https://img.shields.io/badge/PyQt6-GUI-41CD52?style=for-the-badge&logo=qt&logoColor=white)](https://pypi.org/project/PyQt6/)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)
[![Version](https://img.shields.io/badge/Version-2.0-blue?style=for-the-badge)](https://github.com/bpm500/ZapretTester/releases)

<br/>

> Удобный графический интерфейс для запуска и тестирования конфигураций Zapret.  
> Подключение в один клик, автотест всех конфигов, автозапуск с Windows.

</div>

---

## ⚡ Что такое ZapretTester?

**ZapretTester** — это GUI-обёртка для [zapret-discord-youtube](https://github.com/Flowseal/zapret-discord-youtube), которая превращает запуск `.bat` файлов в удобный тёмный интерфейс. Программа автоматически тестирует все конфиги, находит лучший по пингу и доступности сервисов, и позволяет подключаться одним кликом.

**Что умеет:**
- Запуск любого `.bat` конфига zapret одним нажатием
- Автоматический тест всех конфигов с замером пинга и доступности
- Автозапуск при старте Windows (через реестр — надёжно)
- Автоподключение при запуске программы
- Сворачивание в системный трей с управлением через иконку
- Скрытие окна `winws.exe` из панели задач

---

## 🖥️ Системные требования

| Параметр | Требование |
|---|---|
| ОС | Windows 10 (1903+) / Windows 11 |
| Права | **Администратор** (обязательно) |
| Python | 3.13+ (только для запуска из исходников) |
| Зависимости | PyQt6, psutil, requests, ping3 |

---

## 🚀 Быстрый старт

### Шаг 1 — Скачайте ZapretTester

Скачайте `ZapretTester.exe` из раздела **[Releases](https://github.com/bpm500/ZapretTester/releases)**

### Шаг 2 — Скачайте zapret

Скачайте архив из репозитория **[zapret-discord-youtube](https://github.com/Flowseal/zapret-discord-youtube/releases)**

### Шаг 3 — Структура папок

Распакуйте архив zapret и расположите файлы **так:**

```
📁 Любая папка/
├── ZapretTester.exe       ← сама программа
└── 📁 zapret/             ← папка с zapret (создайте вручную)
    └── 📁 zapret-discord-youtube-x.x.x/   ← содержимое архива
        ├── general.bat
        ├── discord.bat
        ├── service.bat
        └── ... (остальные .bat файлы)
```

> ⚠️ Папка называется строго `zapret` — именно так программа её находит.

### Шаг 4 — Запуск

Запустите `ZapretTester.exe` **от имени администратора** (ПКМ → «Запуск от имени администратора»)

---

## 📋 Функционал

### Вкладка Connect

| Элемент | Описание |
|---|---|
| **Кнопка питания** | Клик — подключение / отключение. Зелёная = подключено |
| **Выпадающий список** | Выбор `.bat` конфига из папки zapret |
| **Автозапуск** | Добавляет программу в автозапуск Windows через реестр |
| **Автоподключение** | При запуске программы автоматически подключается к последнему конфигу |

### Вкладка Settings

| Элемент | Описание |
|---|---|
| **Консоль** | Лог всех действий в реальном времени с цветовой индикацией |
| **Run service.bat** | Запускает `service.bat` из папки zapret |
| **Test All Configs** | Автоматически тестирует каждый `.bat` файл: проверяет доступность YouTube / Discord / Roblox и замеряет пинг |
| **Результаты** | Показывает TOP-3 конфига по совокупному результату |

### Системный трей

- **Левый клик** по иконке — открыть окно
- **Правый клик** — меню: Открыть / Подключить / Отключить / Выход
- Иконка меняет цвет: серая = отключено, зелёная = подключено
- Закрытие окна сворачивает в трей (не выходит из программы)

---

## 🔬 Как работает автотест

При нажатии **Test All Configs** программа последовательно:

1. Останавливает предыдущий winws процесс
2. Запускает следующий `.bat` конфиг
3. Проверяет HTTP-доступность: YouTube, Discord, Roblox
4. Замеряет ping до: Yandex, Discord, YouTube, Roblox
5. Сохраняет результат и переходит к следующему конфигу
6. После всех тестов показывает **TOP-3** конфига — отсортированных по среднему пингу и количеству доступных сервисов

Тест можно остановить в любой момент кнопкой **Stop Testing**.

---

## 🔧 Сборка из исходников

### Требования

- Python 3.13+
- Git

### Установка

```bash
git clone https://github.com/bpm500/ZapretTester.git
cd ZapretTester
pip install -r requirements.txt
```

### Запуск без сборки

```bash
python zapret_tester.py
```

### Сборка EXE

```bash
# Установить pyinstaller если нет
pip install pyinstaller

# Запустить build.bat от имени администратора
build.bat
```

Готовый EXE появится в папке `dist/`. Он автономен — Python не требуется.

---

## 📁 Структура репозитория

```
ZapretTester/
├── zapret_tester.py      ← основной файл
├── zapret_tester.spec    ← конфиг сборки PyInstaller
├── build.bat             ← скрипт сборки EXE
├── requirements.txt      ← зависимости Python
├── 1.ico                 ← иконка приложения
├── on.png                ← кнопка питания (вкл)
└── off.png               ← кнопка питания (выкл)
```

---

## ❓ Частые вопросы

<details>
<summary><b>Программа не видит .bat файлы</b></summary>

Убедитесь что структура папок правильная:
- Рядом с `ZapretTester.exe` должна быть папка `zapret`
- Внутри `zapret` — содержимое архива zapret-discord-youtube
- `.bat` файлы должны быть внутри (не обязательно в корне `zapret/`, допускается один подкаталог)

</details>

<details>
<summary><b>Ошибка "требуются права администратора"</b></summary>

Zapret запускает драйвер `winws.exe`, который требует прав администратора. Запускайте `ZapretTester.exe` через ПКМ → «Запуск от имени администратора».

</details>

<details>
<summary><b>Автозапуск добавляется, но не работает</b></summary>

Программа добавляет себя в реестр: `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`. Проверьте что антивирус не блокирует запись в реестр. Также убедитесь что запускаете от администратора при первом включении автозапуска.

</details>

<details>
<summary><b>Окно winws.exe всё равно появляется</b></summary>

Программа скрывает окно с задержкой 2 секунды после запуска. Если окно мелькает — это нормально, оно скроется автоматически.

</details>

<details>
<summary><b>Тест показывает все сервисы недоступными</b></summary>

Zapret требует времени на инициализацию (~3 сек после запуска `.bat`). Если сервисы всё равно недоступны — попробуйте другой конфиг, не все конфиги работают на всех провайдерах.

</details>

---

## 📄 Лицензия

MIT License — см. файл [LICENSE](LICENSE)

---

<div align="center">

Сделано с ❤️ by [bpm500](https://github.com/bpm500)

**[⭐ Поставьте звезду если программа помогла!](https://github.com/bpm500/ZapretTester)**

</div>
