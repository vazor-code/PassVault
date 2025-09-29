from cryptography.fernet import Fernet
import os
import string
import random
import json

print("==============================")
print("🔐 PassVault запущен!")
print("==============================")

# ---- Настройки файлов ----
KEY_FILE = "key.key"
VAULT_FILE = "vault.json"

# ---- Ключ шифрования ----
if not os.path.exists(KEY_FILE) or os.path.getsize(KEY_FILE) == 0:
    key = Fernet.generate_key()
    with open(KEY_FILE, "wb") as file:
        file.write(key)
    print("🔑 Ключ создан и сохранён.")
else:
    with open(KEY_FILE, "rb") as file:
        key = file.read()
    print("🔑 Ключ уже существует.")

fernet = Fernet(key)

# ---- База паролей ----
if os.path.isfile(VAULT_FILE):
    print("📂 База паролей найдена.")
else:
    print("📂 База паролей пуста.")
    with open(VAULT_FILE, "wb") as vault:
        vault.write(fernet.encrypt(json.dumps({}).encode()))

# ---- Основной цикл ----
while True:
    print("\nВыберите действие:\n1. Добавить запись\n2. Найти запись\n3. Удалить запись\n4. Сгенерировать пароль\n5. Выйти")
    choice = input("Выбор: ").strip()

    # ---- Загрузка базы ----
    with open(VAULT_FILE, "rb") as f:
        encrypted = f.read()
    vault = json.loads(fernet.decrypt(encrypted))

    # ---- 1. Добавить запись ----
    if choice == "1":
        service = input("Сервис: ")
        login = input("Логин: ")
        password = input("Пароль (оставить пустым для генерации): ")
        if password.strip() == "":
            safe_symbols = "!@#$%^&*-_+="
            chars = string.ascii_letters + string.digits + safe_symbols
            password = ''.join(random.choice(chars) for _ in range(10))

        if service in vault:
            if isinstance(vault[service], list):
                vault[service].append({"login": login, "password": password})
            else:
                vault[service] = [vault[service], {"login": login, "password": password}]
        else:
            vault[service] = {"login": login, "password": password}

        with open(VAULT_FILE, "wb") as f:
            f.write(fernet.encrypt(json.dumps(vault).encode()))
        print(f"\n👉 Пароль: {password}\n✅ Запись для {service} добавлена.")

    # ---- 2. Найти запись ----
    elif choice == "2":
        service = input("Введите сервис: ")
        if service in vault:
            entries = vault[service]
            if isinstance(entries, list):
                for i, v in enumerate(entries, 1):
                    print(f"{i}. Логин: {v['login']} | Пароль: {v['password']}")
            else:
                print(f"Логин: {entries['login']} | Пароль: {entries['password']}")
        else:
            print("❌ Сервис не найден.")

    # ---- 3. Удалить запись ----
    elif choice == "3":
        service = input("Введите сервис для удаления: ")
        if service in vault:
            del vault[service]
            with open(VAULT_FILE, "wb") as f:
                f.write(fernet.encrypt(json.dumps(vault).encode()))
            print(f"✅ Все записи для {service} удалены.")
        else:
            print("❌ Сервис не найден.")

    # ---- 4. Сгенерировать пароль ----
    elif choice == "4":
        length = input("Длина пароля (по умолчанию 10): ")
        length = int(length) if length.isdigit() else 10
        safe_symbols = "!@#$%^&*-_+="
        chars = string.ascii_letters + string.digits + safe_symbols
        password = ''.join(random.choice(chars) for _ in range(length))
        print(f"🔑 Сгенерированный пароль: {password}")

    # ---- 5. Выход ----
    elif choice == "5":
        print("👋 Выход. До встречи!")
        break

    else:
        print("Введите число от 1 до 5.")
