import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# --- КОНФИГУРАЦИЯ ТАБЛИЦ ---
TABLES_CONFIG = {
    # --- ОСНОВНЫЕ ДАННЫЕ ---
    "Order": {"pk": "Number", "type": "data"},
    "Client": {"pk": "Passport_number", "type": "data"},
    "Car": {"pk": "Car_model", "type": "data"},

    # --- СПРАВОЧНИКИ ---
    "Supplier": {"pk": "Sup_name", "type": "lookup"},
    "Parts": {"pk": "Part_name", "type": "lookup"},
    "Services": {"pk": "Service_name", "type": "lookup"},
    "Room": {"pk": "Address", "type": "lookup"},
    "Employee": {"pk": "Phone", "type": "lookup"},

    # --- СВЯЗУЮЩИЕ ТАБЛИЦЫ ---
    "Room-Order": {"pk": ["Room_address", "Order_number"], "type": "data"},
    "Service_name-Order_number": {"pk": ["Service_name", "Order_number"], "type": "data"}
}


def get_db_connection():
    return psycopg2.connect(
        host=os.getenv('DB_HOST'), database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'), password=os.getenv('DB_PASSWORD')
    )


def execute_query(query, params=(), fetch=False):
    conn = get_db_connection()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(query, params)
        if fetch:
            return cur.fetchall()
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def check_permission(table_name, method):
    user_role = request.headers.get('X-Role', 'user')  # 'user' или 'superuser'
    table_type = TABLES_CONFIG[table_name]['type']

    if user_role == 'superuser':
        return True

    # Пользователь не может писать в справочники
    if table_type == 'lookup' and method in ['POST', 'PUT', 'DELETE']:
        return False

    return True


# --- УНИВЕРСАЛЬНЫЕ CRUD ФУНКЦИИ ---

def generate_crud():

    for table, config in TABLES_CONFIG.items():
        pk = config['pk']
        url_name = table.replace('"', '').lower().replace(' ', '-')

        # 1. GET ALL
        def get_list(t=table):
            try:
                data = execute_query(f'SELECT * FROM "{t}"', fetch=True)
                return jsonify(data), 200
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        # 2. POST (Create)
        def create_item(t=table):
            if not check_permission(t, 'POST'):
                return jsonify({"error": "Access denied"}), 403
            try:
                data = request.get_json()
                columns = data.keys()
                values = [data[col] for col in columns]
                placeholders = ", ".join(["%s"] * len(values))
                cols_str = ", ".join([f'"{c}"' for c in columns])

                query = f'INSERT INTO "{t}" ({cols_str}) VALUES ({placeholders})'
                execute_query(query, tuple(values))
                return jsonify({"message": f"Record added to {t}"}), 201
            except Exception as e:
                return jsonify({"error": str(e)}), 400

        endpoint_base = f'/api/{url_name}'
        app.add_url_rule(endpoint_base, f'get_{table}', get_list, methods=['GET'])
        app.add_url_rule(endpoint_base, f'create_{table}', create_item, methods=['POST'])

        if isinstance(pk, str):
            # 3. PUT (Update)
            def update_item(id, t=table, pk_col=pk):
                if not check_permission(t, 'PUT'):
                    return jsonify({"error": "Access denied"}), 403
                try:
                    data = request.get_json()
                    set_clause = ", ".join([f'"{col}"=%s' for col in data.keys()])
                    values = list(data.values())
                    values.append(id)

                    query = f'UPDATE "{t}" SET {set_clause} WHERE "{pk_col}"=%s'
                    execute_query(query, tuple(values))
                    return jsonify({"message": f"Record updated in {t}"}), 200
                except Exception as e:
                    return jsonify({"error": str(e)}), 400

            # 4. DELETE
            def delete_item(id, t=table, pk_col=pk):
                if not check_permission(t, 'DELETE'):
                    return jsonify({"error": "Access denied"}), 403
                try:
                    query = f'DELETE FROM "{t}" WHERE "{pk_col}"=%s'
                    execute_query(query, (id,))
                    return jsonify({"message": f"Record deleted from {t}"}), 200
                except Exception as e:
                    return jsonify({"error": str(e)}), 400

            app.add_url_rule(f'{endpoint_base}/<string:id>', f'update_{table}', update_item, methods=['PUT'])
            app.add_url_rule(f'{endpoint_base}/<string:id>', f'delete_{table}', delete_item, methods=['DELETE'])


# Запуск генератора маршрутов
generate_crud()

# --- СПЕЦИАЛЬНЫЕ МАРШРУТЫ (Бэкап) ---

@app.route('/api/admin/backup', methods=['POST'])
def backup_db():
    if request.headers.get('X-Role') != 'superuser':
        return jsonify({"error": "Access denied"}), 403
    try:
        db_pass = os.getenv('DB_PASSWORD')
        db_user = os.getenv('DB_USER')
        db_name = os.getenv('DB_NAME')
        cmd = f"set PGPASSWORD={db_pass}&& pg_dump -U {db_user} -h localhost {db_name} > backup.sql"
        os.system(cmd)
        return jsonify({"message": "Backup created"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- СПЕЦИАЛЬНЫЕ ЗАПРОСЫ (Для ЛР №2) ---
@app.route('/api/queries/expensive_cars', methods=['GET'])
def query_expensive_cars():
    """Специальный запрос 1: Автомобили дороже средней цены по салону"""
    try:
        query = """
            SELECT "Car_model", "Brand", "Year", "Price", "Sup_name"
            FROM "Car"
            WHERE "Price" > (SELECT AVG("Price") FROM "Car")
            ORDER BY "Price" DESC
        """
        data = execute_query(query, fetch=True)
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/queries/order_details', methods=['GET'])
def query_order_details():
    """Специальный запрос 2: Детализация заказов (JOIN Клиент, Авто, Сотрудник)"""
    try:
        query = """
            SELECT 
                o."Number" AS "Номер заказа", o."Status" AS "Статус",
                c."Name" AS "Клиент", car."Brand" AS "Марка", car."Car_model" AS "Модель",
                e."Name" AS "Сотрудник", o."Cost" AS "Сумма"
            FROM "Order" o
            JOIN "Client" c ON o."Client_passport" = c."Passport_number"
            JOIN "Car" car ON o."Car_model" = car."Car_model"
            JOIN "Employee" e ON o."Employee_phone" = e."Phone"
            ORDER BY o."Number" DESC
        """
        data = execute_query(query, fetch=True)
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)