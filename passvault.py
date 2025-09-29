from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button, Static, Input, DataTable, Label
from textual.containers import Vertical, Horizontal
from cryptography.fernet import Fernet
import os, string, random, json

# ---- Настройки файлов ----
KEY_FILE = "key.key"
VAULT_FILE = "vault.json"

# ---- Ключ шифрования ----
if not os.path.exists(KEY_FILE) or os.path.getsize(KEY_FILE) == 0:
    key = Fernet.generate_key()
    with open(KEY_FILE, "wb") as file:
        file.write(key)
else:
    with open(KEY_FILE, "rb") as file:
        key = file.read()
fernet = Fernet(key)

# ---- База паролей ----
if not os.path.isfile(VAULT_FILE):
    with open(VAULT_FILE, "wb") as vault:
        vault.write(fernet.encrypt(json.dumps({}).encode()))

# ---- Работа с базой ----
def load_vault():
    with open(VAULT_FILE, "rb") as f:
        return json.loads(fernet.decrypt(f.read()))

def save_vault(vault):
    with open(VAULT_FILE, "wb") as f:
        f.write(fernet.encrypt(json.dumps(vault).encode()))

def generate_password(length=10):
    chars = string.ascii_letters + string.digits + "!@#$%^&*-_+="
    return ''.join(random.choice(chars) for _ in range(length))

# ---- Textual App ----
class PassVaultApp(App):
    BINDINGS = [("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical():
            yield Static("🔐 PassVault", id="title")
            with Horizontal():
                yield Button("Add Entry", id="add")
                yield Button("Find Entry", id="find")
                yield Button("Delete Entry", id="delete")
                yield Button("Generate Password", id="gen")
            yield Vertical(id="form_container")
            yield DataTable(id="vault_table")
            yield Label("", id="status")
        yield Footer()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        form_container = self.query_one("#form_container")
        table = self.query_one("#vault_table")
        status = self.query_one("#status")
        vault = load_vault()

        # ---- Главное меню ----
        if event.button.id in ["add", "find", "delete", "gen"]:
            form_container.remove_children()  # очищаем форму перед новым действием

            if event.button.id == "add":
                service_input = Input(placeholder="Service", id="service")
                login_input = Input(placeholder="Login", id="login")
                password_input = Input(placeholder="Password (optional)", id="password")
                save_btn = Button("Save", id="save_add")
                await form_container.mount(service_input, login_input, password_input, save_btn)

            elif event.button.id == "find":
                table.clear(columns=True)
                table.add_columns("Login", "Password")
                service_input = Input(placeholder="Service to find", id="find_service")
                search_btn = Button("Search", id="search")
                await form_container.mount(service_input, search_btn)

            elif event.button.id == "delete":
                service_input = Input(placeholder="Service to delete", id="del_service")
                del_btn = Button("Delete Confirm", id="del_confirm")
                await form_container.mount(service_input, del_btn)

            elif event.button.id == "gen":
                pw = generate_password()
                status.update(f"🔑 Generated password: {pw}")

        # ---- Кнопки внутри форм ----
        elif event.button.id == "save_add":
            service = self.query_one("#service", Input).value
            login = self.query_one("#login", Input).value
            password = self.query_one("#password", Input).value
            if not password.strip():
                password = generate_password()
            if service in vault:
                if isinstance(vault[service], list):
                    vault[service].append({"login": login, "password": password})
                else:
                    vault[service] = [vault[service], {"login": login, "password": password}]
            else:
                vault[service] = {"login": login, "password": password}
            save_vault(vault)
            status.update(f"✅ Added {service} with password {password}")
            form_container.remove_children()

        elif event.button.id == "search":
            service = self.query_one("#find_service", Input).value
            table.clear(columns=True)
            table.add_columns("Login", "Password")
            if service in vault:
                entries = vault[service]
                if isinstance(entries, list):
                    for v in entries:
                        table.add_row(v["login"], v["password"])
                else:
                    table.add_row(entries["login"], entries["password"])
                status.update(f"✅ Found entries for {service}")
            else:
                status.update(f"❌ Service {service} not found")
            form_container.remove_children()

        elif event.button.id == "del_confirm":
            service = self.query_one("#del_service", Input).value
            if service in vault:
                del vault[service]
                save_vault(vault)
                table.clear()
                status.update(f"✅ Deleted all entries for {service}")
            else:
                status.update(f"❌ Service {service} not found")
            form_container.remove_children()


if __name__ == "__main__":
    PassVaultApp().run()
