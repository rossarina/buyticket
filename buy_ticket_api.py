from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import mysql.connector
import uvicorn
from typing import List, Optional

app = FastAPI(title="BuyTicket Pro (Full CRUD + Mobile Features)")

# ฟังก์ชันเชื่อมต่อ Database
def get_db_conn():
    return mysql.connector.connect(
        host="192.168.1.136",
        user="buyticket",
        password="P@ssw0rd",
        database="buyticket_db"
    )

# --- Pydantic Models ---
class BusCreate(BaseModel):
    bus_number: str
    route: str
    price: float
    image_url: str

class BookingRequest(BaseModel):
    customer_name: str
    bus_id: int
    seat_id: int

# --- [1] CRUD สำหรับเที่ยวรถ (Admin Section) ---

# CREATE - เพิ่มเที่ยวรถ
@app.post("/admin/buses")
def add_bus(bus: BusCreate):
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO buses (bus_number, route, price, image_url) VALUES (%s, %s, %s, %s)",
        (bus.bus_number, bus.route, bus.price, bus.image_url)
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return {"message": "เพิ่มเที่ยวรถสำเร็จ", "id": new_id}

# READ - ดูเที่ยวรถทั้งหมด (มีอยู่แล้ว)
@app.get("/buses")
def get_buses():
    conn = get_db_conn()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM buses")
    rows = cursor.fetchall()
    conn.close()
    return rows

# UPDATE - แก้ไขข้อมูลรถ
@app.put("/admin/buses/{bus_id}")
def update_bus(bus_id: int, bus: BusCreate):
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE buses SET bus_number=%s, route=%s, price=%s, image_url=%s WHERE id=%s",
        (bus.bus_number, bus.route, bus.price, bus.image_url, bus_id)
    )
    conn.commit()
    conn.close()
    return {"message": "อัปเดตข้อมูลรถสำเร็จ"}

# DELETE - ลบเที่ยวรถ
@app.delete("/admin/buses/{bus_id}")
def delete_bus(bus_id: int):
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM buses WHERE id = %s", (bus_id,))
    conn.commit()
    conn.close()
    return {"message": "ลบเที่ยวรถเรียบร้อย"}

# --- [2] Mobile Features (Seat, Payment, Ticket) ---

@app.get("/buses/{bus_id}/seats")
def get_seats(bus_id: int):
    conn = get_db_conn()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM seats WHERE bus_id = %s", (bus_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

@app.post("/bookings")
def create_booking(req: BookingRequest):
    conn = get_db_conn()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT is_booked FROM seats WHERE id = %s", (req.seat_id,))
        seat = cursor.fetchone()
        if not seat or seat[0]:
            raise HTTPException(status_code=400, detail="ที่นั่งนี้ไม่ว่าง")

        cursor.execute(
            "INSERT INTO bookings (customer_name, bus_id, seat_id, payment_status) VALUES (%s, %s, %s, 'pending')",
            (req.customer_name, req.bus_id, req.seat_id)
        )
        booking_id = cursor.lastrowid
        cursor.execute("UPDATE seats SET is_booked = True WHERE id = %s", (req.seat_id,))
        conn.commit()
        return {"message": "จองสำเร็จ", "booking_id": booking_id}
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

@app.get("/payment/promptpay/{booking_id}")
def get_payment_qr(booking_id: int):
    conn = get_db_conn()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT b.price FROM bookings bk JOIN buses b ON bk.bus_id = b.id WHERE bk.id = %s", (booking_id,))
    data = cursor.fetchone()
    conn.close()
    if not data: raise HTTPException(status_code=404)
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=PROMPTPAY_{data['price']}"
    return {"qr_url": qr_url, "amount": data['price']}

@app.post("/payment/confirm/{booking_id}")
def confirm_payment(booking_id: int):
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute("UPDATE bookings SET payment_status = 'paid' WHERE id = %s", (booking_id,))
    conn.commit()
    conn.close()
    return {"message": "ชำระเงินเรียบร้อย"}

@app.get("/tickets/{booking_id}")
def get_eticket(booking_id: int):
    conn = get_db_conn()
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT bk.id, bk.customer_name, b.bus_number, b.route, s.seat_label, bk.payment_status
        FROM bookings bk
        JOIN buses b ON bk.bus_id = b.id
        JOIN seats s ON bk.seat_id = s.id
        WHERE bk.id = %s
    """
    cursor.execute(query, (booking_id,))
    ticket = cursor.fetchone()
    conn.close()
    return ticket

if __name__ == "__main__":
    uvicorn.run("buy_ticket_api:app", host="0.0.0.0", port=8000, reload=True)