import flet as ft
import requests

# ตรวจสอบ IP ให้ตรงกับ Ubuntu ของพายนะครับ
BASE_URL = "http://192.168.1.136:8000"

def main(page: ft.Page):
    page.title = "BuyTicket Pro"
    page.theme_mode = "dark"
    page.scroll = "adaptive"  # Enable mouse scrolling
    # Remove fixed window size for responsive design
    page.bgcolor = ft.Colors.BLUE_GREY_900

    # State
    current_view = "login"
    selected_bus = None
    selected_seat = None
    booking_id = None
    customer_name = ""
    logged_in = False
    logged_user = ""
    credentials = {"user": "1234", "admin": "admin1234"}

    # UI Components
    bus_list = ft.ListView(expand=1, spacing=15, padding=10)
    seat_list = ft.ListView(expand=1, spacing=10, padding=10)
    qr_image = ft.Image(src="", width=250, height=250)
    ticket_view = ft.Column(scroll="adaptive", spacing=15)

    login_username_field = ft.TextField(
        label="ชื่อผู้ใช้",
        hint_text="เช่น user หรือ admin",
        icon=ft.Icons.PERSON,
        border_radius=15,
        bgcolor=ft.Colors.BLUE_GREY_800,
        filled=True,
        width=280
    )
    login_password_field = ft.TextField(
        label="รหัสผ่าน",
        hint_text="กรุณากรอกรหัสผ่าน",
        icon=ft.Icons.LOCK,
        border_radius=15,
        bgcolor=ft.Colors.BLUE_GREY_800,
        filled=True,
        password=True,
        can_reveal_password=True,
        width=280
    )
    login_error = ft.Text("", color=ft.Colors.RED, size=12)

    name_field = ft.TextField(
        label="ชื่อผู้โดยสาร",
        hint_text="กรุณากรอกชื่อเต็ม",
        icon=ft.Icons.PERSON,
        border_radius=15,
        bgcolor=ft.Colors.BLUE_GREY_800,
        filled=True
    )

    amount_text = ft.Text("", size=18, weight="bold", color=ft.Colors.GREEN_700)

    steps = {
        "bus_selection": ("เลือกเที่ยวรถ", 1),
        "seat_selection": ("เลือกที่นั่ง", 2),
        "booking": ("กรอกข้อมูล", 3),
        "payment": ("ชำระเงิน", 4),
        "ticket": ("ตั๋วของคุณ", 5)
    }

    def get_header(title):
        title_size = 24 if page.width < 600 else 28
        return ft.Container(
            content=ft.Column([
                ft.Text(title, size=title_size, weight="bold", color=ft.Colors.WHITE)
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=5),
            gradient=ft.LinearGradient(colors=[ft.Colors.BLUE_400, ft.Colors.BLUE_600]),
            padding=25,
            border_radius=ft.BorderRadius.only(bottom_left=30, bottom_right=30)
        )

    nav_items = [
        ("bus_selection", "เที่ยวรถ", ft.Icons.DIRECTIONS_BUS),
        ("ticket", "ตั๋ว", ft.Icons.CONFIRMATION_NUMBER),
        ("account", "บัญชี", ft.Icons.PERSON),
    ]

    def get_nav_bar():
        buttons = []
        for view_key, label, icon in nav_items:
            selected = current_view == view_key
            buttons.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(icon, size=18, color=ft.Colors.WHITE if selected else ft.Colors.GREY_400),
                        ft.Text(label, size=12, color=ft.Colors.WHITE if selected else ft.Colors.GREY_400)
                    ], alignment=ft.MainAxisAlignment.CENTER, spacing=4),
                    bgcolor=ft.Colors.BLUE_700 if selected else ft.Colors.BLUE_GREY_800,
                    border_radius=ft.BorderRadius.all(16),
                    padding=ft.Padding.symmetric(vertical=8, horizontal=10),
                    on_click=lambda e, v=view_key: change_view(v)
                )
            )
        return ft.Container(
            content=ft.Row(buttons, alignment=ft.MainAxisAlignment.SPACE_AROUND, expand=1),
            padding=ft.Padding.symmetric(vertical=10, horizontal=12),
            bgcolor=ft.Colors.BLUE_GREY_900,
            border=ft.Border.all(1, ft.Colors.BLUE_GREY_700),
            shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.BLACK38, offset=ft.Offset(0, -2))
        )

    def update_layout():
        # Update components based on orientation
        is_landscape = page.width > page.height
        # Adjust grid max_extent for seats
        seat_list.max_extent = 110 if not is_landscape else 90
        # Adjust image sizes
        qr_image.width = 220 if is_landscape else 250
        qr_image.height = 220 if is_landscape else 250
        page.update()

    page.on_resize = lambda e: update_layout()

    def login(e):
        nonlocal logged_in, logged_user, customer_name
        username = login_username_field.value.strip()
        password = login_password_field.value.strip()
        if not username or not password:
            login_error.value = "กรุณากรอกชื่อผู้ใช้และรหัสผ่าน"
            page.update()
            return
        if credentials.get(username) == password:
            logged_in = True
            logged_user = username
            customer_name = username
            login_error.value = ""
            login_username_field.value = ""
            login_password_field.value = ""
            change_view("bus_selection")
        else:
            login_error.value = "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง"
            page.update()

    def logout(e):
        nonlocal logged_in, logged_user, selected_bus, selected_seat, booking_id, customer_name, current_view
        logged_in = False
        logged_user = ""
        selected_bus = None
        selected_seat = None
        booking_id = None
        customer_name = ""
        current_view = "login"
        change_view("login")

    # Functions
    def load_buses():
        bus_list.controls.clear()
        bus_list.controls.append(ft.Container(content=ft.ProgressRing(), alignment=ft.Alignment.CENTER, height=100))
        page.update()
        try:
            response = requests.get(f"{BASE_URL}/buses")
            bus_list.controls.clear()
            if response.status_code == 200:
                buses = response.json()
                for bus in buses:
                    image_width = min(300, page.width - 40)
                    bus_list.controls.append(
                        ft.Container(
                            content=ft.Column([
                                ft.Container(
                                    content=ft.Image(src=bus['image_url'], width=image_width, height=image_width * 0.6, fit="cover"),
                                    border_radius=15,
                                    clip_behavior=ft.ClipBehavior.ANTI_ALIAS
                                ),
                                ft.Container(height=10),
                                ft.Text(f"{bus['bus_number']}", size=18, weight="bold", color=ft.Colors.BLUE_900),
                                ft.Text(f"{bus['route']}", size=14, color=ft.Colors.GREY_700),
                                ft.Text(f"ราคา: {bus['price']} บาท", size=16, weight="bold", color=ft.Colors.GREEN_700),
                                ft.Container(height=10),
                                ft.ElevatedButton(
                                    "เลือกเที่ยวนี้", 
                                    icon=ft.Icons.ARROW_FORWARD,
                                    on_click=lambda e, b=bus: select_bus(b),
                                    style=ft.ButtonStyle(
                                        bgcolor=ft.Colors.BLUE_600,
                                        color=ft.Colors.WHITE,
                                        shape=ft.RoundedRectangleBorder(radius=10)
                                    ),
                                    height=45
                                )
                            ], spacing=5, alignment=ft.MainAxisAlignment.START),
                            bgcolor=ft.Colors.BLUE_GREY_800,
                            border_radius=20,
                            padding=15,
                            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.BLACK12, offset=ft.Offset(0, 5))
                        )
                    )
            else:
                bus_list.controls.append(ft.Text("ไม่สามารถโหลดเที่ยวรถได้", color="red", text_align="center"))
        except Exception as ex:
            bus_list.controls.clear()
            bus_list.controls.append(ft.Text(f"เชื่อมต่อ Server ไม่ได้: {ex}", color="red", text_align="center"))
        page.update()

    def select_bus(bus):
        nonlocal selected_bus
        selected_bus = bus
        change_view("seat_selection")

    def select_seat(seat):
        nonlocal selected_seat
        selected_seat = seat
        change_view("booking")

    def create_seat_container(seat):
        color = ft.Colors.GREEN_300 if not seat['is_booked'] else ft.Colors.RED_300
        icon = ft.Icons.AIRLINE_SEAT_INDIVIDUAL_SUITE if not seat['is_booked'] else ft.Icons.AIRLINE_SEAT_FLAT
        return ft.Container(
            content=ft.Column([
                ft.Icon(icon, size=35, color=ft.Colors.WHITE),
                ft.Text(seat['seat_label'], size=14, weight="bold", color=ft.Colors.WHITE),
                ft.Text("ว่าง" if not seat['is_booked'] else "ไม่ว่าง", size=10, color=ft.Colors.WHITE70)
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=2),
            bgcolor=color,
            border_radius=12,
            width=70,
            height=80,
            padding=5,
            on_click=lambda e, s=seat: select_seat(s) if not s['is_booked'] else None,
            shadow=ft.BoxShadow(blur_radius=8, color=ft.Colors.BLACK26, offset=ft.Offset(0, 3))
        )

    def load_seats():
        if not selected_bus:
            return
        seat_list.controls.clear()
        seat_list.controls.append(ft.Container(content=ft.ProgressRing(), alignment=ft.Alignment.CENTER, height=100))
        page.update()
        try:
            response = requests.get(f"{BASE_URL}/buses/{selected_bus['id']}/seats")
            seat_list.controls.clear()
            if response.status_code == 200:
                seats = response.json()
                seats = sorted(seats, key=lambda x: x['seat_label'])
                runs_count = max(1, min(6, int(page.width // 90)))
                seat_grid = ft.GridView(
                    controls=[create_seat_container(seat) for seat in seats],
                    runs_count=runs_count,
                    spacing=12,
                    run_spacing=12,
                    max_extent=90,
                    expand=1
                )
                seat_list.controls.append(seat_grid)
            else:
                seat_list.controls.append(ft.Text("ไม่สามารถโหลดที่นั่งได้", color="red", text_align="center"))
        except Exception as ex:
            seat_list.controls.clear()
            seat_list.controls.append(ft.Text(f"เชื่อมต่อ Server ไม่ได้: {ex}", color="red", text_align="center"))
        page.update()

    def book_ticket():
        nonlocal booking_id, customer_name
        customer_name = name_field.value
        if not customer_name:
            show_snack("กรุณากรอกชื่อ", ft.Colors.ORANGE)
            return
        payload = {
            "customer_name": customer_name,
            "bus_id": selected_bus['id'],
            "seat_id": selected_seat['id']
        }
        try:
            response = requests.post(f"{BASE_URL}/bookings", json=payload)
            if response.status_code == 200:
                data = response.json()
                booking_id = data['booking_id']
                change_view("payment")
            else:
                show_snack(f"จองไม่สำเร็จ: {response.text}", ft.Colors.RED)
        except Exception as ex:
            show_snack(f"เชื่อมต่อ Server ไม่ได้: {ex}", ft.Colors.RED)

    def load_payment_qr():
        if not booking_id:
            return
        try:
            response = requests.get(f"{BASE_URL}/payment/promptpay/{booking_id}")
            if response.status_code == 200:
                data = response.json()
                qr_image.src = data['qr_url']
                # Find the amount text in the page
                for control in page.controls[0].content.controls:
                    if hasattr(control, 'value') and 'จำนวนเงิน' in str(control.value):
                        control.value = f"จำนวนเงิน: {data['amount']} บาท"
                        break
                page.update()
            else:
                show_snack(f"ไม่สามารถโหลด QR: {response.text}", ft.Colors.RED)
        except Exception as ex:
            show_snack(f"เชื่อมต่อ Server ไม่ได้: {ex}", ft.Colors.RED)

    def confirm_payment():
        if not booking_id:
            return
        try:
            response = requests.post(f"{BASE_URL}/payment/confirm/{booking_id}")
            if response.status_code == 200:
                change_view("ticket")
            else:
                show_snack(f"ชำระเงินไม่สำเร็จ: {response.text}", ft.Colors.RED)
        except Exception as ex:
            show_snack(f"เชื่อมต่อ Server ไม่ได้: {ex}", ft.Colors.RED)

    def load_ticket():
        if not booking_id:
            return
        try:
            response = requests.get(f"{BASE_URL}/tickets/{booking_id}")
            if response.status_code == 200:
                ticket = response.json()
                ticket_view.controls = [
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.Icons.CONFIRMATION_NUMBER, size=50, color=ft.Colors.BLUE_600),
                            ft.Text("ตั๋วอิเล็กทรอนิกส์", size=24, weight="bold", color=ft.Colors.BLUE_900),
                            ft.Divider(),
                            ft.Row([ft.Text("ชื่อ:", weight="bold", size=16), ft.Text(ticket['customer_name'], size=16)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Row([ft.Text("รถ:", weight="bold", size=16), ft.Text(ticket['bus_number'], size=16)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Row([ft.Text("เส้นทาง:", weight="bold", size=16), ft.Text(ticket['route'], size=16)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Row([ft.Text("ที่นั่ง:", weight="bold", size=16), ft.Text(ticket['seat_label'], size=16)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Row([ft.Text("สถานะ:", weight="bold", size=16), ft.Text(ticket['payment_status'], size=16, color=ft.Colors.GREEN_700 if ticket['payment_status'] == 'paid' else ft.Colors.ORANGE_700)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ], spacing=10),
                        bgcolor=ft.Colors.BLUE_GREY_800,
                        border_radius=20,
                        padding=20,
                        shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.BLACK12, offset=ft.Offset(0, 5))
                    ),
                    ft.ElevatedButton(
                        "กลับหน้าแรก", 
                        icon=ft.Icons.HOME,
                        on_click=lambda e: change_view("bus_selection"),
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.BLUE_600,
                            color=ft.Colors.WHITE,
                            shape=ft.RoundedRectangleBorder(radius=10)
                        ),
                        height=50
                    )
                ]
            else:
                ticket_view.controls = [ft.Text("ไม่สามารถโหลดตั๋วได้", color="red", text_align="center")]
        except Exception as ex:
            ticket_view.controls = [ft.Text(f"เชื่อมต่อ Server ไม่ได้: {ex}", color="red")]
        page.update()

    def change_view(view):
        nonlocal current_view
        if view != "login" and not logged_in:
            view = "login"
        current_view = view
        page.controls.clear()
        title = steps.get(view, (view.replace("_", " ").capitalize(), None))[0]
        header = get_header(title)
        nav_bar = get_nav_bar()
        if view == "login":
            page.add(
                ft.SafeArea(
                    content=ft.Column([
                        ft.Container(
                            content=ft.Column([
                                ft.Text("เข้าสู่ระบบ BuyTicket", size=28, weight="bold", color=ft.Colors.WHITE),
                                ft.Text("กรุณาเข้าสู่ระบบเพื่อใช้งาน", size=14, color=ft.Colors.WHITE70)
                            ], alignment=ft.MainAxisAlignment.CENTER, spacing=6),
                            gradient=ft.LinearGradient(colors=[ft.Colors.BLUE_600, ft.Colors.BLUE_900]),
                            padding=30,
                            border_radius=ft.BorderRadius.only(bottom_left=30, bottom_right=30)
                        ),
                        ft.Container(height=30),
                        ft.Container(
                            content=ft.Column([
                                login_username_field,
                                login_password_field,
                                login_error,
                                ft.ElevatedButton(
                                    "เข้าสู่ระบบ",
                                    icon=ft.Icons.LOGIN,
                                    on_click=login,
                                    style=ft.ButtonStyle(
                                        bgcolor=ft.Colors.BLUE_700,
                                        color=ft.Colors.WHITE,
                                        shape=ft.RoundedRectangleBorder(radius=15)
                                    ),
                                    width=280,
                                    height=50
                                )
                            ], spacing=15),
                            width=min(340, page.width - 40),
                            padding=20,
                            border_radius=20,
                            bgcolor=ft.Colors.BLUE_GREY_800,
                            shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.BLACK38, offset=ft.Offset(0, 5))
                        )
                    ], alignment=ft.CrossAxisAlignment.CENTER, spacing=0, expand=1)
                )
            )
            return
        if view == "bus_selection":
            page.add(
                ft.SafeArea(
                    content=ft.Column([
                        header,
                        ft.Column([bus_list], expand=1),
                        nav_bar
                    ], spacing=0, expand=1)
                )
            )
            load_buses()
            update_layout()
        elif view == "seat_selection":
            page.add(
                ft.SafeArea(
                    content=ft.Column([
                        header,
                        ft.Column([seat_list, ft.ElevatedButton(
                            "กลับ", 
                            icon=ft.Icons.ARROW_BACK,
                            on_click=lambda e: change_view("bus_selection"),
                            style=ft.ButtonStyle(
                                bgcolor=ft.Colors.GREY_600,
                                color=ft.Colors.WHITE,
                                shape=ft.RoundedRectangleBorder(radius=10)
                            ),
                            height=45
                        )], expand=1, spacing=12),
                        nav_bar
                    ], spacing=0, expand=1)
                )
            )
            load_seats()
            update_layout()
        elif view == "booking":
            page.add(
                ft.SafeArea(
                    content=ft.Column([
                        header,
                        ft.Column([
                            ft.Container(height=20),
                            name_field,
                            ft.Container(height=20),
                            ft.ElevatedButton(
                                "จองตั๋ว", 
                                icon=ft.Icons.BOOKMARK_ADD,
                                on_click=lambda e: book_ticket(),
                                style=ft.ButtonStyle(
                                    bgcolor=ft.Colors.GREEN_600,
                                    color=ft.Colors.WHITE,
                                    shape=ft.RoundedRectangleBorder(radius=15)
                                ),
                                height=55,
                                width=min(250, page.width * 0.7)
                            ),
                            ft.ElevatedButton(
                                "กลับ", 
                                icon=ft.Icons.ARROW_BACK,
                                on_click=lambda e: change_view("seat_selection"),
                                style=ft.ButtonStyle(
                                    bgcolor=ft.Colors.GREY_600,
                                    color=ft.Colors.WHITE,
                                    shape=ft.RoundedRectangleBorder(radius=10)
                                ),
                                height=45
                            )
                        ], expand=1, spacing=12, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        nav_bar
                    ], spacing=0, expand=1)
                )
            )
            update_layout()
        elif view == "payment":
            page.add(
                ft.SafeArea(
                    content=ft.Column([
                        header,
                        ft.Column([
                            ft.Container(height=20),
                            ft.Text("สแกน QR เพื่อชำระเงิน", size=18, text_align="center"),
                            amount_text,
                            qr_image,
                            ft.Container(height=20),
                            ft.ElevatedButton(
                                "ชำระเงินเสร็จแล้ว", 
                                icon=ft.Icons.CHECK_CIRCLE,
                                on_click=lambda e: confirm_payment(),
                                style=ft.ButtonStyle(
                                    bgcolor=ft.Colors.GREEN_600,
                                    color=ft.Colors.WHITE,
                                    shape=ft.RoundedRectangleBorder(radius=15)
                                ),
                                height=55,
                                width=min(250, page.width * 0.7)
                            ),
                            ft.ElevatedButton(
                                "กลับ", 
                                icon=ft.Icons.ARROW_BACK,
                                on_click=lambda e: change_view("bus_selection"),
                                style=ft.ButtonStyle(
                                    bgcolor=ft.Colors.GREY_600,
                                    color=ft.Colors.WHITE,
                                    shape=ft.RoundedRectangleBorder(radius=10)
                                ),
                                height=45
                            )
                        ], expand=1, spacing=12, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        nav_bar
                    ], spacing=0, expand=1)
                )
            )
            load_payment_qr()
            update_layout()
        elif view == "ticket":
            page.add(
                ft.SafeArea(
                    content=ft.Column([
                        header,
                        ft.Column([ticket_view], expand=1),
                        nav_bar
                    ], spacing=0, expand=1)
                )
            )
            load_ticket()
            update_layout()
        elif view == "account":
            account_details = [
                ft.Text("บัญชีผู้ใช้", size=20, weight="bold"),
                ft.Text(f"ชื่อ: {customer_name if customer_name else 'ยังไม่ได้กรอก'}", size=16),
                ft.Text(f"เที่ยวรถล่าสุด: {selected_bus['bus_number'] if selected_bus else 'ไม่มีข้อมูล'}", size=16),
                ft.Text(f"ที่นั่งล่าสุด: {selected_seat['seat_label'] if selected_seat else 'ไม่มีข้อมูล'}", size=16),
                ft.Container(height=10),
                ft.ElevatedButton(
                    "รีเฟรชข้อมูล",
                    icon=ft.Icons.REFRESH,
                    on_click=lambda e: change_view("account"),
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.BLUE_600,
                        color=ft.Colors.WHITE,
                        shape=ft.RoundedRectangleBorder(radius=12)
                    ),
                    height=45,
                    width=min(250, page.width * 0.7)
                ),
                ft.ElevatedButton(
                    "ออกจากระบบ",
                    icon=ft.Icons.LOGOUT,
                    on_click=logout,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.RED_600,
                        color=ft.Colors.WHITE,
                        shape=ft.RoundedRectangleBorder(radius=12)
                    ),
                    height=45,
                    width=min(250, page.width * 0.7)
                )
            ]
            page.add(
                ft.SafeArea(
                    content=ft.Column([
                        header,
                        ft.Column([
                            ft.Container(height=20),
                            ft.Container(
                                content=ft.Column(account_details, spacing=12),
                                padding=20,
                                border_radius=20,
                                bgcolor=ft.Colors.BLUE_GREY_800,
                                shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.BLACK12, offset=ft.Offset(0, 5))
                            )
                        ], expand=1, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
                        nav_bar
                    ], spacing=0, expand=1)
                )
            )
            update_layout()

    def show_snack(text, color):
        page.snack_bar = ft.SnackBar(ft.Text(text), bgcolor=color)
        page.snack_bar.open = True
        page.update()

    change_view("login")

ft.run(main)
