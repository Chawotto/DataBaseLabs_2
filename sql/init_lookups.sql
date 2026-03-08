-- Поставщики
INSERT INTO "Supplier" ("Sup_name", "Address", "Phone", "Rating") VALUES
('ООО АвтоДеталь', 'Минск, ул. Ленина 1', 375291111111, 5),
('ЗАО ЗапчастьТорг', 'Брест, ул. Мира 5', 375292222222, 4);

-- Запчасти
INSERT INTO "Parts" ("Part_name", "Price", "Manufacturer", "Quality", "Sup_name") VALUES
('Масляный фильтр', 25.00, 'Bosch', 'Original', 'ООО АвтоДеталь'),
('Тормозные колодки', 120.00, 'Brembo', 'Original', 'ЗАО ЗапчастьТорг');

-- Услуги
INSERT INTO "Services" ("Service_name", "Price", "Total_cost", "Duration", "Part_name") VALUES
('Замена масла', 30.00, 55.00, 30, 'Масляный фильтр'),
('Замена колодок', 50.00, 170.00, 60, 'Тормозные колодки');

-- Сотрудники (тоже статичные данные для старта)
INSERT INTO "Employee" ("Phone", "Name", "Title", "Experience") VALUES
(375291234567, 'Иванов Иван Иванович', 'Менеджер', 5),
(375299876543, 'Петров Петр Петрович', 'Механик', 10);