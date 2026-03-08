import sys
import os
import datetime
import requests
import pandas as pd
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QComboBox, QLineEdit, QPushButton, QTableView, QHeaderView,
    QMenuBar, QMenu, QMessageBox, QDialog, QFormLayout, QDialogButtonBox, QLabel, QLayout
)
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QShortcut, QKeySequence, QAction
from PyQt6.QtCore import Qt

# --- НАСТРОЙКИ ПОДКЛЮЧЕНИЯ И СХЕМЫ ---
BASE_URL = "http://127.0.0.1:5000/api"

# Конфигурация таблиц: поля для форм добавления/обновления и Primary Key
TABLES_SCHEMA = {
    "Order": {"pk": "Number",
              "fields": ["Number", "Cost", "Priority", "Status", "Client_passport", "Car_model", "Employee_phone"]},
    "Client": {"pk": "Passport_number", "fields": ["Passport_number", "Name", "Address", "Phone"]},
    "Car": {"pk": "Car_model", "fields": ["Car_model", "Brand", "Year", "Price", "Sup_name"]},
    "Supplier": {"pk": "Sup_name", "fields": ["Sup_name", "Address", "Phone", "Rating"]},
    "Parts": {"pk": "Part_name", "fields": ["Part_name", "Price", "Manufacturer", "Quality", "Sup_name"]},
    "Services": {"pk": "Service_name", "fields": ["Service_name", "Price", "Total_cost", "Duration", "Part_name"]},
    "Room": {"pk": "Address", "fields": ["Address", "Square", "Appointment", "Floor", "Service_name"]},
    "Employee": {"pk": "Phone", "fields": ["Phone", "Name", "Title", "Experience"]}
}

SPECIAL_QUERIES = {
    "Автомобили дороже средней цены": "/queries/expensive_cars",
    "Детализация заказов (с именами)": "/queries/order_details"
}

# --- СОВРЕМЕННЫЙ СТИЛЬ (QSS) ---
MODERN_DARK_THEME = """
    QMainWindow, QDialog { background-color: #1E1E2E; color: #FFFFFF; }
    QWidget { font-family: 'Segoe UI', Roboto, sans-serif; font-size: 14px; color: #CDD6F4; }
    QTableView {
        background-color: #181825; alternate-background-color: #1E1E2E;
        color: #CDD6F4; gridline-color: #313244; border: 1px solid #313244;
        border-radius: 8px; selection-background-color: #89B4FA; selection-color: #11111B;
    }
    QHeaderView::section { background-color: #313244; color: #BAC2DE; padding: 6px; border: none; font-weight: bold; }
    QLineEdit, QComboBox {
        background-color: #11111B; border: 1px solid #45475A;
        padding: 6px 12px; border-radius: 6px; color: #CDD6F4;
    }
    QLineEdit:focus, QComboBox:focus { border: 1px solid #89B4FA; }
    QPushButton {
        background-color: #89B4FA; color: #11111B; font-weight: bold;
        padding: 8px 16px; border-radius: 6px; border: none;
    }
    QPushButton:hover { background-color: #B4BEFE; }
    QPushButton:pressed { background-color: #74C7EC; }
    QMenuBar { background-color: #1E1E2E; color: #CDD6F4; padding: 4px; }
    QMenuBar::item:selected { background-color: #313244; border-radius: 4px; }
    QMenu { background-color: #181825; border: 1px solid #313244; border-radius: 6px; }
    QMenu::item { padding: 6px 24px; }
    QMenu::item:selected { background-color: #89B4FA; color: #11111B; }
"""


# --- ДИАЛОГОВЫЕ ОКНА (Строго по требованиям CUA) ---

class BaseDialog(QDialog):
    """Базовый диалог: фиксированный размер (без скролла), Enter=OK, Esc=Cancel."""

    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.layout = QVBoxLayout(self)
        # Запрет скроллинга: фиксируем размер по содержимому
        self.layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

        self.form_layout = QFormLayout()
        self.layout.addLayout(self.form_layout)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)


class FormDialog(BaseDialog):
    """Универсальный диалог для добавления и обновления."""

    def __init__(self, title, fields, parent=None):
        super().__init__(title, parent)
        self.inputs = {}
        for field in fields:
            line_edit = QLineEdit()
            self.inputs[field] = line_edit
            self.form_layout.addRow(field + ":", line_edit)

    def get_data(self):
        return {field: line_edit.text() for field, line_edit in self.inputs.items()}


class SingleInputDialog(BaseDialog):
    """Диалог для удаления (ввод ID) и бэкапа (ввод пароля)."""

    def __init__(self, title, label_text, is_password=False, parent=None):
        super().__init__(title, parent)
        self.input_field = QLineEdit()
        if is_password:
            self.input_field.setEchoMode(QLineEdit.EchoMode.Password)
        self.form_layout.addRow(label_text, self.input_field)

    def get_value(self):
        return self.input_field.text()


class QueryDialog(BaseDialog):
    """Диалог выбора специального запроса."""

    def __init__(self, parent=None):
        super().__init__("Select Query", parent)
        self.combo = QComboBox()
        self.combo.addItems(list(SPECIAL_QUERIES.keys()))
        self.form_layout.addRow("Выберите запрос:", self.combo)

    def get_query_url(self):
        return SPECIAL_QUERIES[self.combo.currentText()]


# --- ГЛАВНОЕ ОКНО ПРИЛОЖЕНИЯ ---

class AutosalonClient(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_table = "Order"  # Таблица по умолчанию по условию
        self.user_role = "superuser"  # Роль для API
        self.last_query_data = None  # Для сохранения в Excel

        self.init_ui()
        self.setup_menus()
        self.setup_shortcuts()
        self.load_table_data()

    def init_ui(self):
        self.setWindowTitle("Autosalon ERP - Modern Client")
        self.resize(1000, 600)
        self.setStyleSheet(MODERN_DARK_THEME)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Панель фильтрации
        filter_layout = QHBoxLayout()
        self.lbl_table = QLabel(f"Активная таблица: {self.current_table}")
        self.lbl_table.setStyleSheet("font-weight: bold; color: #A6E3A1;")

        self.combo_filter_field = QComboBox()
        self.input_filter_val = QLineEdit()
        self.input_filter_val.setPlaceholderText("Значение фильтра...")
        btn_apply_filter = QPushButton("Apply Filter")
        btn_apply_filter.clicked.connect(self.apply_filter)

        # Выбор роли (чтобы удобно тестировать RBAC)
        self.combo_role = QComboBox()
        self.combo_role.addItems(["superuser", "user"])
        self.combo_role.currentTextChanged.connect(self.change_role)

        filter_layout.addWidget(self.lbl_table)
        filter_layout.addStretch()
        filter_layout.addWidget(QLabel("Role:"))
        filter_layout.addWidget(self.combo_role)
        filter_layout.addWidget(QLabel("Filter by:"))
        filter_layout.addWidget(self.combo_filter_field)
        filter_layout.addWidget(self.input_filter_val)
        filter_layout.addWidget(btn_apply_filter)
        main_layout.addLayout(filter_layout)

        # Таблица данных
        self.table_view = QTableView()
        self.table_view.setAlternatingRowColors(True)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.model = QStandardItemModel()
        self.table_view.setModel(self.model)
        main_layout.addWidget(self.table_view)

    def change_role(self, role):
        self.user_role = role

    # --- МЕНЮ (F10, Alt+буква) ---
    def setup_menus(self):
        menubar = self.menuBar()

        # Первое меню File
        file_menu = menubar.addMenu("&File")
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Меню Tables
        tables_menu = menubar.addMenu("&Tables")
        for t_name in TABLES_SCHEMA.keys():
            action = QAction(t_name, self)
            action.triggered.connect(lambda checked, t=t_name: self.set_active_table(t))
            tables_menu.addAction(action)

        # Меню Operations
        ops_menu = menubar.addMenu("&Operations")

        ops = [
            ("Add", self.cmd_add), ("View", self.cmd_view),
            ("Delete", self.cmd_delete), ("Update", self.cmd_update),
            ("Queries", self.cmd_queries), ("Save Query", self.cmd_save),
            ("Backup", self.cmd_backup)
        ]

        for op_name, callback in ops:
            action = QAction(op_name, self)
            action.triggered.connect(callback)
            ops_menu.addAction(action)

    # --- ГОРЯЧИЕ КЛАВИШИ (CUA Standard) ---
    def setup_shortcuts(self):
        shortcuts = {
            "Ctrl+A": self.cmd_add,
            "Ctrl+V": self.cmd_view,
            "Ctrl+D": self.cmd_delete,
            "Ctrl+U": self.cmd_update,
            "Ctrl+Q": self.cmd_queries,
            "Ctrl+S": self.cmd_save,
            "Ctrl+B": self.cmd_backup,
            "Ctrl+E": self.close
        }
        for seq, callback in shortcuts.items():
            QShortcut(QKeySequence(seq), self).activated.connect(callback)

    # --- ВЗАИМОДЕЙСТВИЕ С API ---
    def get_headers(self):
        return {"X-Role": self.user_role, "Content-Type": "application/json"}

    def set_active_table(self, table_name):
        self.current_table = table_name
        self.lbl_table.setText(f"Активная таблица: {self.current_table}")
        self.load_table_data()

    def load_table_data(self, endpoint=None):
        url = f"{BASE_URL}/{self.current_table.lower()}" if not endpoint else f"{BASE_URL}{endpoint}"
        try:
            response = requests.get(url, headers=self.get_headers())
            if response.status_code == 200:
                data = response.json()
                self.last_query_data = data
                self.populate_table(data)
            else:
                self.show_error("Ошибка сервера", response.json().get('error', 'Unknown error'))
        except Exception as e:
            self.show_error("Ошибка подключения", str(e))

    def populate_table(self, data):
        self.model.clear()
        self.combo_filter_field.clear()

        if not data:
            return

        headers = list(data[0].keys())
        self.model.setHorizontalHeaderLabels(headers)
        self.combo_filter_field.addItems(headers)

        for row_data in data:
            row = [QStandardItem(str(row_data[h]) if row_data[h] is not None else "") for h in headers]
            # Запрещаем редактирование прямо в ячейках (только через диалоги)
            for item in row:
                item.setEditable(False)
            self.model.appendRow(row)

    def apply_filter(self):
        field = self.combo_filter_field.currentText()
        value = self.input_filter_val.text().lower()
        if not self.last_query_data or not field:
            return

        filtered_data = [
            row for row in self.last_query_data
            if value in str(row.get(field, "")).lower()
        ]
        self.populate_table(filtered_data)

    # --- ОБРАБОТЧИКИ ОПЕРАЦИЙ ---

    def cmd_view(self):
        self.load_table_data()

    def cmd_add(self):
        schema = TABLES_SCHEMA[self.current_table]
        dialog = FormDialog(f"Add to {self.current_table}", schema['fields'], self)
        if dialog.exec():
            data = dialog.get_data()
            self.send_request("POST", f"/{self.current_table.lower()}", data)

    def cmd_update(self):
        schema = TABLES_SCHEMA[self.current_table]
        dialog = FormDialog(f"Update {self.current_table}", schema['fields'], self)
        if dialog.exec():
            data = dialog.get_data()
            pk_val = data.pop(schema['pk'], None)
            if not pk_val:
                self.show_error("Validation", f"Primary key '{schema['pk']}' is required.")
                return
            self.send_request("PUT", f"/{self.current_table.lower()}/{pk_val}", data)

    def cmd_delete(self):
        schema = TABLES_SCHEMA[self.current_table]
        dialog = SingleInputDialog("Delete Record", f"Enter {schema['pk']}:", parent=self)
        if dialog.exec():
            pk_val = dialog.get_value()
            self.send_request("DELETE", f"/{self.current_table.lower()}/{pk_val}")

    def cmd_queries(self):
        dialog = QueryDialog(self)
        if dialog.exec():
            endpoint = dialog.get_query_url()
            self.load_table_data(endpoint=endpoint)
            self.lbl_table.setText(f"Результат запроса")

    def cmd_save(self):
        if not self.last_query_data:
            self.show_error("Ошибка", "Нет данных для сохранения.")
            return

        os.makedirs("backups", exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"backups/query_{timestamp}.xlsx"

        try:
            df = pd.DataFrame(self.last_query_data)
            df.to_excel(filename, index=False)
            QMessageBox.information(self, "Success", f"Query result saved to\n{filename}")
        except Exception as e:
            self.show_error("Ошибка сохранения", str(e))

    def cmd_backup(self):
        dialog = SingleInputDialog("Create Backup", "PASSWORD:", is_password=True, parent=self)
        if dialog.exec():
            # Пароль запрашиваем для вида (в реальной системе он бы отправлялся на сервер)
            # В нашей реализации сервер сам берет пароль из .env, так что просто дергаем эндпоинт
            self.send_request("POST", "/admin/backup")

    def send_request(self, method, endpoint, json_data=None):
        url = f"{BASE_URL}{endpoint}"
        try:
            if method == "POST":
                res = requests.post(url, json=json_data, headers=self.get_headers())
            elif method == "PUT":
                res = requests.put(url, json=json_data, headers=self.get_headers())
            elif method == "DELETE":
                res = requests.delete(url, headers=self.get_headers())

            if res.status_code in [200, 201]:
                QMessageBox.information(self, "Success", res.json().get('message', 'Operation successful'))
                self.load_table_data()  # Обновляем таблицу
            else:
                err = res.json().get('error', 'Unknown error')
                self.show_error("Access Denied / Error", f"Status: {res.status_code}\n{err}")
        except Exception as e:
            self.show_error("Connection Error", str(e))

    def show_error(self, title, text):
        QMessageBox.critical(self, title, text)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AutosalonClient()
    window.show()
    sys.exit(app.exec())