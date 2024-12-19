import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3  # Модуль для работы с SQLite

def initialize_database():
    conn = sqlite3.connect("autoshop.db")
    cursor = conn.cursor()

    # Создаем таблицу товаров
    cursor.execute('''CREATE TABLE IF NOT EXISTS products (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        category TEXT NOT NULL,
                        price REAL NOT NULL,
                        quantity INTEGER NOT NULL
                      )''')

    # Создаем таблицу пользователей
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL UNIQUE,
                        password TEXT NOT NULL,
                        role TEXT NOT NULL CHECK(role IN ('admin', 'manager'))
                      )''')

    # Создаем таблицу заказов
    cursor.execute('''CREATE TABLE IF NOT EXISTS orders (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        product_id INTEGER NOT NULL,
                        quantity INTEGER NOT NULL,
                        user_id INTEGER NOT NULL,
                        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (product_id) REFERENCES products (id),
                        FOREIGN KEY (user_id) REFERENCES users (id)
                      )''')

    # Добавляем тестового администратора
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                       ('admin', 'admin123', 'admin'))

    conn.commit()
    conn.close()



# Создаем главное окно
root = tk.Tk()
root.title("Система магазина автозапчастей")
root.geometry("800x600")


def view_orders():
    orders_window = tk.Toplevel(root)
    orders_window.title("View Orders")
    orders_window.geometry("800x600")

    tk.Label(orders_window, text="Orders", font=("Arial", 14)).pack(pady=10)

    tree = ttk.Treeview(orders_window, columns=("Order ID", "Product ID", "Quantity", "User ID", "Date"), show="headings")
    tree.heading("Order ID", text="Order ID")
    tree.heading("Product ID", text="Product ID")
    tree.heading("Quantity", text="Quantity")
    tree.heading("User ID", text="User ID")
    tree.heading("Date", text="Date")
    tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Загружаем заказы в таблицу
    conn = sqlite3.connect("autoshop.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders")
    rows = cursor.fetchall()
    conn.close()

    for row in tree.get_children():
        tree.delete(row)
    for row in rows:
        tree.insert("", "end", values=row)


def open_orders_window(user_id):
    orders_window = tk.Toplevel(root)
    orders_window.title("Manage Orders")
    orders_window.geometry("800x600")

    tk.Label(orders_window, text="Manage Orders", font=("Arial", 14)).pack(pady=10)

    # Таблица товаров для выбора
    tree = ttk.Treeview(orders_window, columns=("ID", "Name", "Category", "Price", "Quantity"), show="headings")
    tree.heading("ID", text="ID")
    tree.heading("Name", text="Name")
    tree.heading("Category", text="Category")
    tree.heading("Price", text="Price")
    tree.heading("Quantity", text="Quantity")
    tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def load_products():
        """Загружает товары в таблицу."""
        conn = sqlite3.connect("autoshop.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products")
        rows = cursor.fetchall()
        conn.close()

        for row in tree.get_children():
            tree.delete(row)
        for row in rows:
            tree.insert("", "end", values=row)

    load_products()

    # Поле для указания количества и оформления заказа
    tk.Label(orders_window, text="Quantity:").pack(pady=5)
    quantity_entry = tk.Entry(orders_window)
    quantity_entry.pack(pady=5)

    def place_order():
        """Оформляет заказ."""
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showerror("Ошибка", "Выберите товар для заказа!")
            return

        item = tree.item(selected_item)
        product_id = item["values"][0]
        available_quantity = item["values"][4]

        try:
            quantity = int(quantity_entry.get())
            if quantity <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Ошибка", "Количество должно быть положительным числом!")
            return

        if quantity > available_quantity:
            messagebox.showerror("Ошибка", "Недостаточно товара на складе!")
            return

        # Обновляем количество товара в базе данных
        conn = sqlite3.connect("autoshop.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE products SET quantity = quantity - ? WHERE id = ?", (quantity, product_id))

        # Создаем запись в таблице заказов
        cursor.execute("INSERT INTO orders (product_id, quantity, user_id) VALUES (?, ?, ?)", 
                       (product_id, quantity, user_id))
        conn.commit()
        conn.close()

        load_products()
        messagebox.showinfo("Успех", "Заказ успешно оформлен!")
        quantity_entry.delete(0, tk.END)

    tk.Button(orders_window, text="Place Order", command=place_order).pack(pady=10)


def edit_user(tree):
    """Редактирование данных выбранного пользователя."""
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showerror("Ошибка", "Выберите пользователя для редактирования!")
        return

    # Получаем ID выбранного пользователя
    item = tree.item(selected_item)
    user_id = item["values"][0]

    # Открываем окно для редактирования
    edit_window = tk.Toplevel()
    edit_window.title("Edit User")
    edit_window.geometry("400x300")

    tk.Label(edit_window, text="New Password:").pack(pady=5)
    password_entry = tk.Entry(edit_window, show="*")
    password_entry.pack(pady=5)

    tk.Label(edit_window, text="New Role:").pack(pady=5)
    role_entry = tk.Entry(edit_window)
    role_entry.pack(pady=5)

    def save_changes():
        new_password = password_entry.get()
        new_role = role_entry.get()

        if not (new_password and new_role in ['admin', 'manager']):
            messagebox.showerror("Ошибка", "Некорректные данные!")
            return

        # Обновляем запись в базе данных
        conn = sqlite3.connect("autoshop.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET password = ?, role = ? WHERE id = ?", (new_password, new_role, user_id))
        conn.commit()
        conn.close()

        # Обновляем данные в таблице интерфейса
        tree.item(selected_item, values=(user_id, item["values"][1], new_role))

        messagebox.showinfo("Успех", "Данные пользователя обновлены!")
        edit_window.destroy()

    tk.Button(edit_window, text="Save Changes", command=save_changes).pack(pady=10)


def delete_user(tree):
    """Удаление выбранного пользователя из базы данных."""
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showerror("Ошибка", "Выберите пользователя для удаления!")
        return

    # Получаем ID выбранного пользователя
    item = tree.item(selected_item)
    user_id = item["values"][0]

    # Удаляем запись из базы данных
    conn = sqlite3.connect("autoshop.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

    # Удаляем строку из таблицы интерфейса
    tree.delete(selected_item)

    messagebox.showinfo("Успех", "Пользователь успешно удален!")


def show_login_window():
    login_window = tk.Toplevel(root)
    login_window.title("Login")
    login_window.geometry("400x300")

    tk.Label(login_window, text="Username:").pack(pady=5)
    username_entry = tk.Entry(login_window)
    username_entry.pack(pady=5)

    tk.Label(login_window, text="Password:").pack(pady=5)
    password_entry = tk.Entry(login_window, show="*")
    password_entry.pack(pady=5)

    def login():
        username = username_entry.get()
        password = password_entry.get()

        conn = sqlite3.connect("autoshop.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, role FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            user_id, role = user
            messagebox.showinfo("Success", f"Logged in as {role.capitalize()}")
            login_window.destroy()
            open_dashboard(role, user_id)
        else:
            messagebox.showerror("Error", "Invalid username or password!")

    tk.Button(login_window, text="Login", command=login).pack(pady=10)


def open_dashboard(role, user_id):
    if role == "admin":
        open_admin_dashboard()
    elif role == "manager":
        open_manager_dashboard(user_id)


def open_admin_dashboard():
    admin_window = tk.Toplevel(root)
    admin_window.title("Admin Dashboard")
    admin_window.geometry("600x400")

    tk.Label(admin_window, text="Admin Dashboard", font=("Arial", 16)).pack(pady=20)

    tk.Button(admin_window, text="Manage Products", command=open_products_window).pack(pady=10)
    tk.Button(admin_window, text="Manage Users", command=open_users_window).pack(pady=10)
    tk.Button(admin_window, text="View Orders", command=view_orders).pack(pady=10)



def open_manager_dashboard(user_id):
    manager_window = tk.Toplevel(root)
    manager_window.title("Manager Dashboard")
    manager_window.geometry("600x400")

    tk.Label(manager_window, text="Manager Dashboard", font=("Arial", 16)).pack(pady=20)

    tk.Button(manager_window, text="View Products", command=open_products_window).pack(pady=10)
    tk.Button(manager_window, text="Manage Orders", command=lambda: open_orders_window(user_id)).pack(pady=10)



def open_users_window():
    users_window = tk.Toplevel(root)
    users_window.title("Manage Users")
    users_window.geometry("600x400")

    tk.Label(users_window, text="Manage Users", font=("Arial", 14)).pack(pady=10)

    tree = ttk.Treeview(users_window, columns=("ID", "Username", "Role"), show="headings")
    tree.heading("ID", text="ID")
    tree.heading("Username", text="Username")
    tree.heading("Role", text="Role")
    tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Поля для добавления нового пользователя
    add_frame = tk.Frame(users_window)
    add_frame.pack(pady=10)

    tk.Label(add_frame, text="Username:").grid(row=0, column=0, padx=5)
    entry_username = tk.Entry(add_frame)
    entry_username.grid(row=0, column=1, padx=5)

    tk.Label(add_frame, text="Password:").grid(row=0, column=2, padx=5)
    entry_password = tk.Entry(add_frame)
    entry_password.grid(row=0, column=3, padx=5)

    tk.Label(add_frame, text="Role:").grid(row=1, column=0, padx=5)
    entry_role = tk.Entry(add_frame)
    entry_role.grid(row=1, column=1, padx=5)

    def add_user():
        username = entry_username.get()
        password = entry_password.get()
        role = entry_role.get()

        if not (username and password and role in ['admin', 'manager']):
            messagebox.showerror("Error", "Invalid input!")
            return

        conn = sqlite3.connect("autoshop.db")
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                           (username, password, role))
            conn.commit()
            load_users(tree)
            messagebox.showinfo("Success", "User added successfully!")
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Username already exists!")
        conn.close()

    tk.Button(add_frame, text="Add User", command=add_user).grid(row=2, column=0, columnspan=4, pady=10)

    # Кнопка для удаления пользователя
    btn_delete = tk.Button(users_window, text="Delete User", command=lambda: delete_user(tree))
    btn_delete.pack(pady=10)

    # Кнопка для редактирования пользователя
    btn_edit = tk.Button(users_window, text="Edit User", command=lambda: edit_user(tree))
    btn_edit.pack(pady=10)

    # Функция для загрузки пользователей
    def load_users(tree):
        conn = sqlite3.connect("autoshop.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, role FROM users")
        rows = cursor.fetchall()
        conn.close()

        for row in tree.get_children():
            tree.delete(row)
        for row in rows:
            tree.insert("", "end", values=row)

    load_users(tree)


    # Функция для загрузки пользователей
    def load_users(tree):
        conn = sqlite3.connect("autoshop.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, role FROM users")
        rows = cursor.fetchall()
        conn.close()

        for row in tree.get_children():
            tree.delete(row)
        for row in rows:
            tree.insert("", "end", values=row)

    load_users(tree)



def search_products(tree, name_entry, category_entry, min_price_entry, max_price_entry):
    """Фильтрация товаров на основе заданных критериев."""
    name = name_entry.get()
    category = category_entry.get()
    min_price = min_price_entry.get()
    max_price = max_price_entry.get()

    # Формируем SQL-запрос с фильтрацией
    query = "SELECT * FROM products WHERE 1=1"
    params = []

    if name:
        query += " AND name LIKE ?"
        params.append(f"%{name}%")
    if category:
        query += " AND category LIKE ?"
        params.append(f"%{category}%")
    if min_price:
        try:
            min_price = float(min_price)
            query += " AND price >= ?"
            params.append(min_price)
        except ValueError:
            messagebox.showerror("Ошибка", "Минимальная цена должна быть числом!")
            return
    if max_price:
        try:
            max_price = float(max_price)
            query += " AND price <= ?"
            params.append(max_price)
        except ValueError:
            messagebox.showerror("Ошибка", "Максимальная цена должна быть числом!")
            return

    # Выполняем запрос и обновляем таблицу
    conn = sqlite3.connect("autoshop.db")
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    # Очищаем таблицу
    for row in tree.get_children():
        tree.delete(row)

    # Заполняем таблицу результатами поиска
    for row in rows:
        tree.insert("", "end", values=row)


def delete_product(tree):
    """Удаление выбранного товара из базы данных и таблицы."""
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showerror("Ошибка", "Выберите товар для удаления!")
        return

    # Получаем ID выбранного товара
    item = tree.item(selected_item)
    product_id = item["values"][0]

    # Удаляем запись из базы данных
    conn = sqlite3.connect("autoshop.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()

    # Удаляем строку из таблицы интерфейса
    tree.delete(selected_item)

    messagebox.showinfo("Успех", "Товар успешно удален!")


def edit_product(tree, name_entry, category_entry, price_entry, quantity_entry):
    """Редактирование выбранного товара."""
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showerror("Ошибка", "Выберите товар для редактирования!")
        return

    # Получаем ID выбранного товара
    item = tree.item(selected_item)
    product_id = item["values"][0]

    # Получаем новые значения из полей ввода
    name = name_entry.get()
    category = category_entry.get()
    price = price_entry.get()
    quantity = quantity_entry.get()

    # Проверка на заполненность полей
    if not (name and category and price and quantity):
        messagebox.showerror("Ошибка", "Заполните все поля!")
        return

    try:
        price = float(price)
        quantity = int(quantity)
    except ValueError:
        messagebox.showerror("Ошибка", "Цена должна быть числом, а количество — целым числом!")
        return

    # Обновляем запись в базе данных
    conn = sqlite3.connect("autoshop.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE products SET name = ?, category = ?, price = ?, quantity = ? WHERE id = ?",
                   (name, category, price, quantity, product_id))
    conn.commit()
    conn.close()

    # Обновляем данные в таблице интерфейса
    tree.item(selected_item, values=(product_id, name, category, price, quantity))

    # Очищаем поля ввода
    name_entry.delete(0, tk.END)
    category_entry.delete(0, tk.END)
    price_entry.delete(0, tk.END)
    quantity_entry.delete(0, tk.END)

    messagebox.showinfo("Успех", "Товар успешно обновлен!")


# Функция для выхода
def exit_app():
    root.quit()

# Функция для окна "О программе"
def show_about():
    messagebox.showinfo("О программе", "Система магазина автозапчастей\nВерсия 1.0")


def open_products_window():
    products_window = tk.Toplevel(root)
    products_window.title("Управление товарами")
    products_window.geometry("800x600")

    # Заголовок окна
    label = tk.Label(products_window, text="Управление товарами", font=("Arial", 14))
    label.pack(pady=10)

    # Поля для фильтрации товаров
    filter_frame = tk.Frame(products_window)
    filter_frame.pack(pady=10)

    tk.Label(filter_frame, text="Search by Name:").grid(row=0, column=0, padx=5)
    search_name = tk.Entry(filter_frame)
    search_name.grid(row=0, column=1, padx=5)

    tk.Label(filter_frame, text="Category:").grid(row=0, column=2, padx=5)
    search_category = tk.Entry(filter_frame)
    search_category.grid(row=0, column=3, padx=5)

    tk.Label(filter_frame, text="Min Price:").grid(row=1, column=0, padx=5)
    min_price = tk.Entry(filter_frame)
    min_price.grid(row=1, column=1, padx=5)

    tk.Label(filter_frame, text="Max Price:").grid(row=1, column=2, padx=5)
    max_price = tk.Entry(filter_frame)
    max_price.grid(row=1, column=3, padx=5)

    # Кнопка для выполнения поиска
    btn_search = tk.Button(filter_frame, text="Search",
                           command=lambda: search_products(tree, search_name, search_category, min_price, max_price))
    btn_search.grid(row=2, column=0, columnspan=4, pady=10)

    # Таблица для отображения товаров
    tree = ttk.Treeview(products_window, columns=("ID", "Name", "Category", "Price", "Quantity"), show="headings")
    tree.heading("ID", text="ID")
    tree.heading("Name", text="Name")
    tree.heading("Category", text="Category")
    tree.heading("Price", text="Price")
    tree.heading("Quantity", text="Quantity")
    tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Поля для добавления или редактирования товара
    add_frame = tk.Frame(products_window)
    add_frame.pack(pady=10)

    tk.Label(add_frame, text="Name:").grid(row=0, column=0, padx=5)
    entry_name = tk.Entry(add_frame)
    entry_name.grid(row=0, column=1, padx=5)

    tk.Label(add_frame, text="Category:").grid(row=0, column=2, padx=5)
    entry_category = tk.Entry(add_frame)
    entry_category.grid(row=0, column=3, padx=5)

    tk.Label(add_frame, text="Price:").grid(row=1, column=0, padx=5)
    entry_price = tk.Entry(add_frame)
    entry_price.grid(row=1, column=1, padx=5)

    tk.Label(add_frame, text="Quantity:").grid(row=1, column=2, padx=5)
    entry_quantity = tk.Entry(add_frame)
    entry_quantity.grid(row=1, column=3, padx=5)

    # Кнопка для добавления товара
    btn_add = tk.Button(add_frame, text="Add Product", command=lambda: add_product(entry_name, entry_category, entry_price, entry_quantity, tree))
    btn_add.grid(row=2, column=0, columnspan=4, pady=10)

    # Кнопка для редактирования товара
    btn_edit = tk.Button(add_frame, text="Edit Product",
                         command=lambda: edit_product(tree, entry_name, entry_category, entry_price, entry_quantity))
    btn_edit.grid(row=3, column=0, columnspan=4, pady=10)

    # Кнопка для удаления товара
    btn_delete = tk.Button(add_frame, text="Delete Product", command=lambda: delete_product(tree))
    btn_delete.grid(row=4, column=0, columnspan=4, pady=10)

        # Кнопка для сброса фильтров
    btn_reset = tk.Button(filter_frame, text="Reset Filters", command=lambda: load_products(tree))
    btn_reset.grid(row=2, column=4, padx=10)


    # Загружаем товары в таблицу
    load_products(tree)


def load_products(tree):
    """Загружает товары из базы данных в таблицу."""
    conn = sqlite3.connect("autoshop.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    rows = cursor.fetchall()
    conn.close()

    # Очищаем таблицу
    for row in tree.get_children():
        tree.delete(row)

    # Заполняем таблицу
    for row in rows:
        tree.insert("", "end", values=row)


def add_product(name_entry, category_entry, price_entry, quantity_entry, tree):
    """Добавление товара в базу данных и обновление таблицы."""
    name = name_entry.get()
    category = category_entry.get()
    price = price_entry.get()
    quantity = quantity_entry.get()

    # Проверка на заполненность полей
    if not (name and category and price and quantity):
        messagebox.showerror("Ошибка", "Заполните все поля!")
        return

    try:
        price = float(price)
        quantity = int(quantity)
    except ValueError:
        messagebox.showerror("Ошибка", "Цена должна быть числом, а количество — целым числом!")
        return

    # Добавляем данные в базу данных
    conn = sqlite3.connect("autoshop.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO products (name, category, price, quantity) VALUES (?, ?, ?, ?)",
                   (name, category, price, quantity))
    conn.commit()
    conn.close()

    # Обновляем таблицу интерфейса
    tree.insert("", "end", values=(cursor.lastrowid, name, category, price, quantity))

    # Очищаем поля ввода
    name_entry.delete(0, tk.END)
    category_entry.delete(0, tk.END)
    price_entry.delete(0, tk.END)
    quantity_entry.delete(0, tk.END)

    messagebox.showinfo("Успех", "Товар добавлен!")

# Меню
menu = tk.Menu(root)
root.config(menu=menu)

file_menu = tk.Menu(menu, tearoff=0)
menu.add_cascade(label="Файл", menu=file_menu)
file_menu.add_command(label="Выход", command=exit_app)

manage_menu = tk.Menu(menu, tearoff=0)
menu.add_cascade(label="Управление", menu=manage_menu)
manage_menu.add_command(label="Товары", command=open_products_window)

help_menu = tk.Menu(menu, tearoff=0)
menu.add_cascade(label="Справка", menu=help_menu)
help_menu.add_command(label="О программе", command=show_about)

# Заголовок в главном окне
label = tk.Label(root, text="Добро пожаловать в систему магазина автозапчастей!", font=("Arial", 16))
label.pack(pady=20)

if __name__ == "__main__":
    initialize_database()  # Создаем таблицы в базе данных, если они не существуют

    # Прячем главное окно, пока не произойдет авторизация
    root.withdraw()
    show_login_window()  # Показываем окно авторизации

    # Запускаем главное окно после авторизации
    root.mainloop()
