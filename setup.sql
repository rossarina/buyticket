CREATE DATABASE IF NOT EXISTS buyticket_db;
USE buyticket_db;

-- 1. ตารางเที่ยวรถ (Buses)
CREATE TABLE IF NOT EXISTS buses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    bus_number VARCHAR(20) UNIQUE,
    route VARCHAR(100),
    departure_time DATETIME,
    price DECIMAL(10,2),
    image_url VARCHAR(255) -- ลิงก์รูปภาพรถจาก API
);

-- 2. ตารางที่นั่ง (Seats)
CREATE TABLE IF NOT EXISTS seats (
    id INT AUTO_INCREMENT PRIMARY KEY,
    bus_id INT,
    seat_label VARCHAR(5), -- เช่น A1, A2, B1
    is_booked BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (bus_id) REFERENCES buses(id)
);

-- 3. ตารางการจอง (Bookings)
CREATE TABLE IF NOT EXISTS bookings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_name VARCHAR(100),
    bus_id INT,
    seat_id INT,
    payment_status ENUM('pending', 'paid') DEFAULT 'pending',
    qr_code_url VARCHAR(255), -- สำหรับจำลอง PromptPay
    booking_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bus_id) REFERENCES buses(id),
    FOREIGN KEY (seat_id) REFERENCES seats(id)
);

-- เพิ่มข้อมูลตัวอย่าง (ที่นั่งรถเบอร์ B-101)
INSERT INTO buses (bus_number, route, price, image_url) VALUES ('B-101', 'BKK - Nakhon Pathom', 150.00, 'https://example.com/bus1.jpg');
INSERT INTO seats (bus_id, seat_label) VALUES (1, 'A1'), (1, 'A2'), (1, 'B1'), (1, 'B2');