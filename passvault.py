# Импорт необходимых компонентов из библиотек
from textual.app import App, ComposeResult  # Основной класс приложения и результат компоновки
from textual.widgets import Header, Footer, Button, Static, Input, DataTable, Label  # Виджеты интерфейса
from textual.containers import Vertical, Horizontal  # Контейнеры для группировки элементов
from cryptography.fernet import Fernet  # Для шифрования данных
import os, string, random, json  # Стандартные модули: файлы, генерация паролей, JSON


# ---- Настройки файлов ----
KEY_FILE = "key.key"          # Файл с ключом шифрования
VAULT_FILE = "vault.json"     # Файл с зашифрованным хранилищем паролей


# ---- Ключ шифрования ----
# Если файла с ключом нет или он пуст — генерируем новый ключ
if not os.path.exists(KEY_FILE) or os.path.getsize(KEY_FILE) == 0:
    key = Fernet.generate_key()  # Генерируем криптографический ключ
    with open(KEY_FILE, "wb") as file:
        file.write(key)  # Сохраняем ключ в файл
else:
    with open(KEY_FILE, "rb") as file:
        key = file.read()  # Читаем существующий ключ
fernet = Fernet(key)  # Создаём объект для шифрования/дешифрования


# ---- Хранилище паролей ----
# Если файла с хранилищем нет — создаём пустое зашифрованное хранилище
if not os.path.isfile(VAULT_FILE):
    with open(VAULT_FILE, "wb") as vault:
        # Шифруем пустой словарь {} и записываем в файл
        vault.write(fernet.encrypt(json.dumps({}).encode()))


# ---- Функции для работы с хранилищем ----

def load_vault():
    """Загружает и расшифровывает хранилище паролей из файла."""
    with open(VAULT_FILE, "rb") as f:
        decrypted_data = fernet.decrypt(f.read())  # Расшифровываем данные
        return json.loads(decrypted_data.decode())  # Преобразуем в словарь Python


def save_vault(vault):
    """Сохраняет словарь паролей в зашифрованном виде."""
    encrypted_data = fernet.encrypt(json.dumps(vault).encode())  # Шифруем данные
    with open(VAULT_FILE, "wb") as f:
        f.write(encrypted_data)  # Записываем в файл


def generate_password(length=10):
    """Генерирует случайный пароль заданной длины."""
    chars = string.ascii_letters + string.digits + "!@#$%^&*-_+="  # Допустимые символы
    return ''.join(random.choice(chars) for _ in range(length))  # Собираем пароль


# ---- Приложение Textual ----
class PassVaultApp(App):
    """Основное приложение-менеджер паролей с текстовым интерфейсом."""
    
    # Горячие клавиши
    BINDINGS = [("q", "quit", "Выход")]  # Нажмите 'q' для выхода

    def compose(self) -> ComposeResult:
        """Создаёт пользовательский интерфейс."""
        yield Header(show_clock=True)  # Верхняя строка с заголовком и часами
        with Vertical():  # Основной вертикальный контейнер
            yield Static("🔐 Менеджер Паролей", id="title")  # Заголовок приложения
            with Horizontal():  # Горизонтальная панель кнопок
                yield Button("Добавить запись", id="add")
                yield Button("Найти запись", id="find")
                yield Button("Удалить запись", id="delete")
                yield Button("Сгенерировать пароль", id="gen")
            yield Vertical(id="form_container")  # Контейнер для форм (ввода)
            yield DataTable(id="vault_table")   # Таблица для отображения результатов
            yield Label("", id="status")        # Статусная строка
        yield Footer()  # Нижняя панель

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Обрабатывает нажатия на кнопки."""
        form_container = self.query_one("#form_container")  # Область ввода
        table = self.query_one("#vault_table")             # Таблица
        status = self.query_one("#status")                 # Строка статуса
        vault = load_vault()                               # Загружаем текущее хранилище

        # ---- Главное меню: действия по нажатию основных кнопок ----
        if event.button.id in ["add", "find", "delete", "gen"]:
            form_container.remove_children()  # Очищаем форму перед новым действием

            if event.button.id == "add":
                # Форма добавления новой записи
                service_input = Input(placeholder="Сервис (например: Gmail)", id="service")
                login_input = Input(placeholder="Логин", id="login")
                password_input = Input(placeholder="Пароль (необязательно)", id="password")
                save_btn = Button("Сохранить", id="save_add")
                await form_container.mount(service_input, login_input, password_input, save_btn)

            elif event.button.id == "find":
                # Форма поиска записи
                table.clear(columns=True)
                table.add_columns("Логин", "Пароль")
                service_input = Input(placeholder="Имя сервиса для поиска", id="find_service")
                search_btn = Button("Поиск", id="search")
                await form_container.mount(service_input, search_btn)

            elif event.button.id == "delete":
                # Форма удаления записи
                service_input = Input(placeholder="Сервис для удаления", id="del_service")
                del_btn = Button("Подтвердить удаление", id="del_confirm")
                await form_container.mount(service_input, del_btn)

            elif event.button.id == "gen":
                # Генерация пароля
                pw = generate_password()
                status.update(f"🔑 Сгенерированный пароль: {pw}")

        # ---- Обработка действий внутри форм ----
        elif event.button.id == "save_add":
            # Сохранение новой записи
            service = self.query_one("#service", Input).value.strip()
            login = self.query_one("#login", Input).value.strip()
            password = self.query_one("#password", Input).value.strip()

            # Если пароль не указан — генерируем его
            if not password:
                password = generate_password()

            # Добавляем запись
            if service in vault:
                # Если уже есть записи для этого сервиса
                if isinstance(vault[service], list):
                    vault[service].append({"login": login, "password": password})
                else:
                    # Преобразуем одиночную запись в список
                    vault[service] = [vault[service], {"login": login, "password": password}]
            else:
                # Новая запись
                vault[service] = {"login": login, "password": password}

            save_vault(vault)  # Сохраняем изменения
            status.update(f"✅ Добавлено: {service} с паролем {password}")
            form_container.remove_children()  # Очищаем форму

        elif event.button.id == "search":
            # Поиск по сервису
            service = self.query_one("#find_service", Input).value.strip()
            table.clear(columns=True)
            table.add_columns("Логин", "Пароль")

            if service in vault:
                entries = vault[service]
                if isinstance(entries, list):
                    # Несколько записей
                    for entry in entries:
                        table.add_row(entry["login"], entry["password"])
                else:
                    # Одна запись
                    table.add_row(entries["login"], entries["password"])
                status.update(f"✅ Найдено: записи для {service}")
            else:
                status.update(f"❌ Сервис '{service}' не найден")
            form_container.remove_children()

        elif event.button.id == "del_confirm":
            # Удаление записи
            service = self.query_one("#del_service", Input).value.strip()
            if service in vault:
                del vault[service]
                save_vault(vault)
                table.clear()  # Очищаем таблицу
                status.update(f"✅ Успешно удалено: {service}")
            else:
                status.update(f"❌ Сервис '{service}' не найден")
            form_container.remove_children()


# ---- Запуск приложения ----
if __name__ == "__main__":
    PassVaultApp().run()