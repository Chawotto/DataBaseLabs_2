import json
import random

# Конфигурация, аналогичная серверной
TABLES = {
    "Order": {"pk": "Number", "example_pk": 1001,
              "body": {"Number": 7777, "Cost": 2000.00, "Priority": 1, "Status": "New", "Client_passport": 100000000,
                       "Car_model": "BMW X5", "Employee_phone": 375291111111}},
    "Client": {"pk": "Passport_number", "example_pk": 100000000,
               "body": {"Passport_number": 999999, "Name": "Новый Клиент", "Address": "Минск", "Phone": 375290000000}},
    "Car": {"pk": "Car_model", "example_pk": "BMW X5",
            "body": {"Car_model": "New Car Model", "Brand": "Test", "Year": 2025, "Price": 50000,
                     "Sup_name": "ООО ЕвроАвтоДеталь"}},
    "Supplier": {"pk": "Sup_name", "example_pk": "ООО ЕвроАвтоДеталь",
                 "body": {"Sup_name": "New Supplier", "Address": "Test Address", "Phone": 123456789, "Rating": 5}},
    "Parts": {"pk": "Part_name", "example_pk": "Масляный фильтр",
              "body": {"Part_name": "New Part", "Price": 100, "Manufacturer": "Test", "Quality": "High",
                       "Sup_name": "ООО ЕвроАвтоДеталь"}},
    "Services": {"pk": "Service_name", "example_pk": "Замена масла",
                 "body": {"Service_name": "New Service", "Price": 100, "Total_cost": 200, "Duration": 60,
                          "Part_name": "New Part"}},
    "Room": {"pk": "Address", "example_pk": "Бокс №1",
             "body": {"Address": "New Box", "Square": 50, "Appointment": "Repair", "Floor": 1,
                      "Service_name": "Замена масла"}},
    "Employee": {"pk": "Phone", "example_pk": 375291234567,
                 "body": {"Phone": 375299999999, "Name": "Test Employee", "Title": "Mechanic", "Experience": 5}}
}

# Шаблон коллекции Postman v2.1
collection = {
    "info": {
        "name": "Autosalon Lab 1 (Full CRUD)",
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
    },
    "item": [],
    "variable": [
        {"key": "base_url", "value": "http://127.0.0.1:5000/api", "type": "string"},
        {"key": "role", "value": "superuser", "type": "string"}  # По умолчанию админ
    ]
}


def create_request(name, method, url, body=None):
    req = {
        "name": name,
        "request": {
            "method": method,
            "header": [
                {"key": "Content-Type", "value": "application/json"},
                {"key": "X-Role", "value": "{{role}}"}
            ],
            "url": {
                "raw": url,
                "host": ["{{base_url}}"],
                "path": url.replace("{{base_url}}/", "").split("/")
            }
        }
    }
    if body and method in ["POST", "PUT"]:
        req["request"]["body"] = {
            "mode": "raw",
            "raw": json.dumps(body, indent=4, ensure_ascii=False)
        }
    return req


# Генерация папок для каждой таблицы
for table, config in TABLES.items():
    folder_name = table
    url_name = table.replace('"', '').lower().replace(' ', '-')
    pk_val = config['example_pk']

    items = []

    # 1. GET All
    items.append(create_request(f"Get All {table}", "GET", "{{base_url}}/" + url_name))

    # 2. POST
    items.append(create_request(f"Create {table}", "POST", "{{base_url}}/" + url_name, config['body']))

    # 3. PUT
    items.append(create_request(f"Update {table}", "PUT", f"{{{{base_url}}}}/{url_name}/{pk_val}", config['body']))

    # 4. DELETE
    items.append(create_request(f"Delete {table}", "DELETE", f"{{{{base_url}}}}/{url_name}/{pk_val}"))

    collection["item"].append({
        "name": folder_name,
        "item": items
    })

# Добавляем Admin действия
collection["item"].append({
    "name": "Admin Actions",
    "item": [
        create_request("Backup Database", "POST", "{{base_url}}/admin/backup")
    ]
})

# Сохранение файла
with open("Autosalon_Postman_Collection.json", "w", encoding="utf-8") as f:
    json.dump(collection, f, indent=4, ensure_ascii=False)

print("Коллекция успешно создана: Autosalon_Postman_Collection.json")