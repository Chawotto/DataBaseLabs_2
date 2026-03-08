-- Очистка
DROP TABLE IF EXISTS "Room-Order" CASCADE;
DROP TABLE IF EXISTS "Service_name-Order_number" CASCADE;
DROP TABLE IF EXISTS "Order" CASCADE;
DROP TABLE IF EXISTS "Room" CASCADE;
DROP TABLE IF EXISTS "Services" CASCADE;
DROP TABLE IF EXISTS "Car" CASCADE;
DROP TABLE IF EXISTS "Parts" CASCADE;
DROP TABLE IF EXISTS "Supplier" CASCADE;
DROP TABLE IF EXISTS "Client" CASCADE;
DROP TABLE IF EXISTS "Employee" CASCADE;

-- Таблицы (строго по варианту)
CREATE TABLE "Employee" (
 "Phone" BIGINT PRIMARY KEY,
 "Name" VARCHAR(255) NOT NULL,
 "Title" VARCHAR(255) NOT NULL,
 "Experience" INT
);

CREATE TABLE "Client" (
 "Passport_number" BIGINT PRIMARY KEY,
 "Name" VARCHAR(255) NOT NULL,
 "Address" VARCHAR(255) NOT NULL,
 "Phone" BIGINT
);

CREATE TABLE "Supplier" (
 "Sup_name" VARCHAR(255) PRIMARY KEY,
 "Address" VARCHAR(255) NOT NULL,
 "Phone" BIGINT NOT NULL,
 "Rating" INT
);

CREATE TABLE "Parts" (
 "Part_name" VARCHAR(255) PRIMARY KEY,
 "Price" DECIMAL(10, 2) NOT NULL,
 "Manufacturer" VARCHAR(255) NOT NULL,
 "Quality" VARCHAR(100),
 "Sup_name" VARCHAR(255) NOT NULL REFERENCES "Supplier"("Sup_name")
);

CREATE TABLE "Services" (
 "Service_name" VARCHAR(255) PRIMARY KEY,
 "Price" DECIMAL(10, 2),
 "Total_cost" DECIMAL(10, 2) NOT NULL,
 "Duration" INT NOT NULL,
 "Part_name" VARCHAR(255) NOT NULL REFERENCES "Parts"("Part_name")
);

CREATE TABLE "Car" (
 "Car_model" VARCHAR(255) PRIMARY KEY,
 "Brand" VARCHAR(255) NOT NULL,
 "Year" INT NOT NULL,
 "Price" DECIMAL(10, 2) NOT NULL,
 "Sup_name" VARCHAR(255) NOT NULL REFERENCES "Supplier"("Sup_name")
);

CREATE TABLE "Room" (
 "Address" VARCHAR(255) PRIMARY KEY,
 "Square" DECIMAL(8, 2) NOT NULL,
 "Appointment" VARCHAR(255) NOT NULL,
 "Floor" INT,
 "Service_name" VARCHAR(255) REFERENCES "Services"("Service_name")
);

CREATE TABLE "Order" (
 "Number" BIGINT PRIMARY KEY,
 "Cost" DECIMAL(12, 2) NOT NULL,
 "Priority" INT,
 "Status" VARCHAR(100) NOT NULL,
 "Client_passport" BIGINT NOT NULL REFERENCES "Client"("Passport_number"),
 "Car_model" VARCHAR(255) NOT NULL REFERENCES "Car"("Car_model"),
 "Employee_phone" BIGINT NOT NULL REFERENCES "Employee"("Phone")
);

CREATE TABLE "Service_name-Order_number" (
 "Service_name" VARCHAR(255) NOT NULL REFERENCES "Services"("Service_name"),
 "Order_number" BIGINT NOT NULL REFERENCES "Order"("Number"),
 PRIMARY KEY ("Service_name", "Order_number")
);

CREATE TABLE "Room-Order" (
 "Room_address" VARCHAR(255) NOT NULL REFERENCES "Room"("Address"),
 "Order_number" BIGINT NOT NULL REFERENCES "Order"("Number"),
 PRIMARY KEY ("Room_address", "Order_number")
);