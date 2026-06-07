import sys
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
import pymysql

conn = pymysql.connect(
    host='localhost',
    user='root',
    password='',
    database='attempt7',
    autocommit=True
)

_ITEMS_Q = (
    "SELECT items.id, items.name, items.description, c.name, items.price, items.photo, "
    "items.discount, m.name, s.name, items.unit, items.quantity, "
    "items.category_id, items.manufacturer_id, items.supplier_id "
    "FROM items "
    "LEFT JOIN categories c ON items.category_id = c.id "
    "LEFT JOIN manufacturers m ON items.manufacturer_id = m.id "
    "LEFT JOIN suppliers s ON items.supplier_id = s.id"
)


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.resize(300, 220)
        self.setWindowTitle('Авторизация')
        layout = QVBoxLayout(self)
        self.login_ql = QLineEdit()
        self.login_ql.setPlaceholderText('Логин')
        self.password_ql = QLineEdit()
        self.password_ql.setPlaceholderText('Пароль')
        self.password_ql.setEchoMode(QLineEdit.EchoMode.Password)
        self.login_btn = QPushButton('Войти')
        self.login_btn.clicked.connect(self.log_in)
        self.guest_btn = QPushButton('Войти без регистрации')
        self.guest_btn.clicked.connect(self.guest_login)
        layout.addWidget(self.login_ql)
        layout.addWidget(self.password_ql)
        layout.addWidget(self.login_btn)
        layout.addWidget(self.guest_btn)

    def log_in(self):
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, login, password, role, full_name FROM users "
            "WHERE login=%s AND password=%s",
            (self.login_ql.text(), self.password_ql.text())
        )
        user = cursor.fetchone()
        if not user:
            QMessageBox.warning(self, 'Ошибка', 'Неверный логин или пароль')
            return
        full_name = user[4] or user[1]   # ФИО для заголовка окна
        if user[3] == 'manager':
            self.hide()
            self.manager = ManagerWindow(full_name, self)
            self.manager.show()
        if user[3] == 'user':
            self.hide()
            self.user = UserWindow(full_name, self)
            self.user.show()
        if user[3] == 'admin':
            self.hide()
            self.admin = AdminWindow(full_name, self)
            self.admin.show()

    def guest_login(self):
        self.hide()
        self.guest = GuestWindow(self)
        self.guest.show()

    def show_again(self):
        self.login_ql.clear()
        self.password_ql.clear()
        self.show()


class AdminWindow(QWidget):
    def __init__(self, full_name, login_win):
        super().__init__()
        self.login_win = login_win
        self.resize(950, 680)
        self.setWindowIcon(QIcon('resources/lopushok.ico'))
        self.setWindowTitle(f'Администратор: {full_name}')
        top_layout = QHBoxLayout()
        label_logo = QLabel()
        pixmap = QPixmap('resources/lopushok.png')
        if not pixmap.isNull():
            label_logo.setPixmap(pixmap.scaled(120, 80, Qt.AspectRatioMode.KeepAspectRatio))

        self.search_ql = QLineEdit()
        self.search_ql.setPlaceholderText('Поиск...')
        self.search_ql.textChanged.connect(self.search)
        self.cat_combo = QComboBox()
        self.cat_combo.addItem('Все категории', None)
        cursor = conn.cursor()
        cursor.execute("""SELECT id, name FROM categories ORDER BY name""")
        for row in cursor.fetchall():
            self.cat_combo.addItem(row[1], row[0])
        self.cat_combo.currentIndexChanged.connect(self.search)
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(['Без сортировки', 'Цена ↑', 'Цена ↓', 'Количество ↑', 'Количество ↓'])
        self.sort_combo.currentIndexChanged.connect(self.search)

        self.add_btn = QPushButton('Добавить товар')
        self.add_btn.clicked.connect(self.add_item)

        self.orders_btn = QPushButton('Заказы')
        self.orders_btn.clicked.connect(self.open_orders)

        self.logout_btn = QPushButton('Выйти')
        self.logout_btn.clicked.connect(self.logout)

        top_layout.addWidget(label_logo)
        top_layout.addWidget(self.search_ql)
        top_layout.addWidget(self.cat_combo)
        top_layout.addWidget(self.sort_combo)

        top_layout.addWidget(self.add_btn)

        top_layout.addWidget(self.orders_btn)

        top_layout.addWidget(self.logout_btn)


        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        self.content_layout = QVBoxLayout(content_widget)
        scroll.setWidget(content_widget)
        layout = QVBoxLayout(self)
        layout.addLayout(top_layout)
        layout.addWidget(scroll)
        self.load_data()


    def logout(self):
        self.hide()
        self.login_win.show_again()


    def open_orders(self):
        self.orders_win = OrdersWindow(can_edit=True)
        self.orders_win.show()

    def load_data(self):
        cursor = conn.cursor()
        cursor.execute(_ITEMS_Q)
        for row in cursor.fetchall():
            self.load_card(row)

    def load_card(self, row):
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.Box)
        qty = int(row[10] or 0)
        disc = float(row[6] or 0)
        if qty == 0:
            frame.setStyleSheet("background-color: #ADD8E6;")
        elif disc > 15:
            frame.setStyleSheet("background-color: #2E8B57;")
        label_pic = QLabel()
        if not row[5]:
            pixmap = QPixmap('resources/picture.png')
        else:
            pixmap = QPixmap(f'resources/products/{row[5]}')
        label_pic.setPixmap(pixmap.scaled(100, 100))
        if disc > 0:
            final = float(row[4]) * (1 - disc / 100)
            price_html = (f'<span style="color:red;text-decoration:line-through">{float(row[4]):.2f}</span>'
                          f' <span style="color:black">{final:.2f}</span> руб.')
        else:
            price_html = f'{float(row[4]):.2f} руб.'
        info_lbl = QLabel(
            f'<b>{row[3]} | {row[1]}</b><br>'
            f'Описание: {row[2]}<br>'
            f'Производитель: {row[7] or "—"}<br>'
            f'Поставщик: {row[8] or "—"}<br>'
            f'Цена: {price_html}<br>'
            f'Единица измерения: {row[9] or "шт"}<br>'
            f'Количество на складе: {qty}'
        )
        info_lbl.setTextFormat(Qt.TextFormat.RichText)
        info_lbl.setWordWrap(True)
        disc_lbl = QLabel(f'Скидка\n{disc:.0f}%' if disc > 0 else 'Нет\nскидки')
        disc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        disc_lbl.setFixedWidth(80)
        disc_lbl.setFrameShape(QFrame.Shape.Box)


        edit_btn = QPushButton('Редактировать')
        edit_btn.clicked.connect(lambda checked, r=row: self.edit_item(r))
        del_btn = QPushButton('Удалить')
        del_btn.clicked.connect(lambda checked, r=row: self.delete_item(r))


        layout_card = QHBoxLayout(frame)
        layout_card.addWidget(label_pic)
        layout_card.addWidget(info_lbl, 1)
        layout_card.addWidget(disc_lbl)

        layout_card.addWidget(edit_btn)
        layout_card.addWidget(del_btn)

        self.content_layout.addWidget(frame)


    def search(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        name = self.search_ql.text().strip()
        cat = self.cat_combo.currentData()
        query = _ITEMS_Q + " WHERE items.name LIKE %s"
        params = [f'%{name}%']
        if cat:
            query += " AND items.category_id = %s"
            params.append(cat)
        sort = self.sort_combo.currentText()
        if sort == 'Цена ↑':
            query += " ORDER BY items.price ASC"
        elif sort == 'Цена ↓':
            query += " ORDER BY items.price DESC"
        elif sort == 'Количество ↑':
            query += " ORDER BY items.quantity ASC"
        elif sort == 'Количество ↓':
            query += " ORDER BY items.quantity DESC"
        cursor = conn.cursor()
        cursor.execute(query, params)
        for row in cursor.fetchall():
            self.load_card(row)



    def add_item(self):
        dlg = QDialog(self)
        dlg.setWindowTitle('Добавить товар')
        dlg.setMinimumWidth(350)
        form = QFormLayout(dlg)
        name_e = QLineEdit()
        desc_e = QLineEdit()
        cat_e = QComboBox()
        cur2 = conn.cursor()
        cur2.execute("SELECT id, name FROM categories ORDER BY name")
        for r in cur2.fetchall(): cat_e.addItem(r[1], r[0])
        manuf_e = QComboBox()
        cur2.execute("SELECT id, name FROM manufacturers ORDER BY name")
        for r in cur2.fetchall(): manuf_e.addItem(r[1], r[0])
        suppl_e = QComboBox()
        cur2.execute("SELECT id, name FROM suppliers ORDER BY name")
        for r in cur2.fetchall(): suppl_e.addItem(r[1], r[0])
        price_e = QLineEdit()
        price_e.setPlaceholderText('0.00')
        disc_e = QLineEdit('0')
        unit_e = QLineEdit('шт')
        qty_e = QLineEdit('0')
        photo_e = QLineEdit()
        form.addRow('Название:', name_e)
        form.addRow('Описание:', desc_e)
        form.addRow('Категория:', cat_e)
        form.addRow('Производитель:', manuf_e)
        form.addRow('Поставщик:', suppl_e)
        form.addRow('Цена:', price_e)
        form.addRow('Скидка %:', disc_e)
        form.addRow('Ед. измерения:', unit_e)
        form.addRow('Кол-во на складе:', qty_e)
        form.addRow('Фото:', photo_e)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        form.addRow(bb)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        cursor = conn.cursor()
        cursor.execute("""INSERT INTO items (name, description, category_id, price, photo, discount,
                          manufacturer_id, supplier_id, unit, quantity) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                       (name_e.text(), desc_e.text(), cat_e.currentData(), float(price_e.text() or 0), photo_e.text(),
                        float(disc_e.text() or 0), manuf_e.currentData(), suppl_e.currentData(), unit_e.text(), int(qty_e.text() or 0)))
        self.search()

    def edit_item(self, row):

        dlg = QDialog(self)
        dlg.setWindowTitle('Редактировать товар')
        dlg.setMinimumWidth(350)
        form = QFormLayout(dlg)
        name_e = QLineEdit(row[1])
        desc_e = QLineEdit(row[2])
        cat_e = QComboBox()
        cur2 = conn.cursor()
        cur2.execute("SELECT id, name FROM categories ORDER BY name")
        for r in cur2.fetchall(): cat_e.addItem(r[1], r[0])
        for i in range(cat_e.count()):
            if cat_e.itemData(i) == row[11]: cat_e.setCurrentIndex(i); break
        manuf_e = QComboBox()
        cur2.execute("SELECT id, name FROM manufacturers ORDER BY name")
        for r in cur2.fetchall(): manuf_e.addItem(r[1], r[0])
        for i in range(manuf_e.count()):
            if manuf_e.itemData(i) == row[12]: manuf_e.setCurrentIndex(i); break
        suppl_e = QComboBox()
        cur2.execute("SELECT id, name FROM suppliers ORDER BY name")
        for r in cur2.fetchall(): suppl_e.addItem(r[1], r[0])
        for i in range(suppl_e.count()):
            if suppl_e.itemData(i) == row[13]: suppl_e.setCurrentIndex(i); break
        price_e = QLineEdit(str(row[4]))
        disc_e = QLineEdit(str(row[6] or 0))
        unit_e = QLineEdit(row[9] or 'шт')
        qty_e = QLineEdit(str(row[10] or 0))
        photo_e = QLineEdit(row[5] or '')
        form.addRow('Название:', name_e)
        form.addRow('Описание:', desc_e)
        form.addRow('Категория:', cat_e)
        form.addRow('Производитель:', manuf_e)
        form.addRow('Поставщик:', suppl_e)
        form.addRow('Цена:', price_e)
        form.addRow('Скидка %:', disc_e)
        form.addRow('Ед. измерения:', unit_e)
        form.addRow('Кол-во на складе:', qty_e)
        form.addRow('Фото:', photo_e)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        form.addRow(bb)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        cursor = conn.cursor()
        cursor.execute("""UPDATE items SET name=%s, description=%s, category_id=%s, price=%s, photo=%s,
                          discount=%s, manufacturer_id=%s, supplier_id=%s, unit=%s, quantity=%s WHERE id=%s""",
                       (name_e.text(), desc_e.text(), cat_e.currentData(), float(price_e.text() or 0), photo_e.text(),
                        float(disc_e.text() or 0), manuf_e.currentData(), suppl_e.currentData(), unit_e.text(), int(qty_e.text() or 0), row[0]))
        self.search()

    def delete_item(self, row):
        reply = QMessageBox.question(self, 'Удалить', f'Удалить "{row[1]}"?',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                cursor = conn.cursor()
                cursor.execute("""delete from items where id=%s""", (row[0],))
                self.search()
            except Exception as e:
                QMessageBox.warning(self, 'Ошибка', f'Нельзя удалить товар: {e}')

class OrdersWindow(QWidget):
    def __init__(self, can_edit=False):
        super().__init__()
        self.can_edit = can_edit
        self.resize(850, 620)
        self.setWindowIcon(QIcon('resources/lopushok.ico'))
        self.setWindowTitle('Заказы')
        top_layout = QHBoxLayout()
        label_logo = QLabel()
        pixmap = QPixmap('resources/lopushok.png')
        if not pixmap.isNull():
            label_logo.setPixmap(pixmap.scaled(120, 80, Qt.AspectRatioMode.KeepAspectRatio))
        top_layout.addWidget(label_logo)

        if can_edit:
            self.add_btn = QPushButton('Добавить заказ')
            self.add_btn.clicked.connect(self.add_order)
            top_layout.addWidget(self.add_btn)

        top_layout.addStretch()
        close_btn = QPushButton('Закрыть')
        close_btn.clicked.connect(self.close)
        top_layout.addWidget(close_btn)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        self.content_layout = QVBoxLayout(content_widget)
        scroll.setWidget(content_widget)
        layout = QVBoxLayout(self)
        layout.addLayout(top_layout)
        layout.addWidget(scroll)
        self.load_data()

    def load_data(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        cursor = conn.cursor()
        cursor.execute("""select id, article, status, pickup_address, order_date, delivery_date
                          from orders""")
        for row in cursor.fetchall():
            self.load_card(row)

    def load_card(self, row):

        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.Box)
        info_lbl = QLabel(
            f'<b>{row[1] or "—"}</b><br>'
            f'{row[2] or "—"}<br>'
            f'{row[3] or "—"}<br>'
            f'{row[4] or "—"}'
        )
        info_lbl.setTextFormat(Qt.TextFormat.RichText)
        info_lbl.setWordWrap(True)
        delivery_lbl = QLabel(f'Дата\nдоставки\n{row[5] or "Не указана"}')
        delivery_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        delivery_lbl.setFixedWidth(110)
        delivery_lbl.setFrameShape(QFrame.Shape.Box)
        layout_card = QHBoxLayout(frame)
        layout_card.addWidget(info_lbl, 1)
        layout_card.addWidget(delivery_lbl)

        if self.can_edit:
            edit_btn = QPushButton('Редактировать')
            edit_btn.clicked.connect(lambda checked, r=row: self.edit_order(r))
            del_btn = QPushButton('Удалить')
            del_btn.clicked.connect(lambda checked, r=row: self.delete_order(r))
            layout_card.addWidget(edit_btn)
            layout_card.addWidget(del_btn)

        self.content_layout.addWidget(frame)


    def add_order(self):
        dlg = QDialog(self)
        dlg.setWindowTitle('Добавить заказ')
        dlg.setMinimumWidth(320)
        form = QFormLayout(dlg)
        article_e = QLineEdit()
        status_e = QComboBox()
        status_e.addItems(['Новый', 'В обработке', 'Доставляется', 'Выполнен', 'Отменён'])
        address_e = QLineEdit()
        order_date_e = QLineEdit(QDate.currentDate().toString('yyyy-MM-dd'))
        order_date_e.setPlaceholderText('yyyy-MM-dd')
        delivery_date_e = QLineEdit(QDate.currentDate().addDays(7).toString('yyyy-MM-dd'))
        delivery_date_e.setPlaceholderText('yyyy-MM-dd')
        form.addRow('Артикул:', article_e)
        form.addRow('Статус:', status_e)
        form.addRow('Адрес выдачи:', address_e)
        form.addRow('Дата заказа:', order_date_e)
        form.addRow('Дата доставки:', delivery_date_e)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        form.addRow(bb)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        order_date = order_date_e.text().strip() or None
        delivery_date = delivery_date_e.text().strip() or None
        try:
            cursor = conn.cursor()
            cursor.execute("""insert into orders (article, status, pickup_address, order_date, delivery_date)
                              values (%s, %s, %s, %s, %s)""",
                           (article_e.text(), status_e.currentText(), address_e.text(),
                            order_date, delivery_date))
        except Exception as e:
            QMessageBox.warning(self, 'Ошибка', f'Не удалось добавить заказ: {e}')
            return
        self.load_data()

    def edit_order(self, row):
        dlg = QDialog(self)
        dlg.setWindowTitle('Редактировать заказ')
        dlg.setMinimumWidth(320)
        form = QFormLayout(dlg)
        article_e = QLineEdit(row[1] or '')
        status_e = QComboBox()
        status_e.addItems(['Новый', 'В обработке', 'Доставляется', 'Выполнен', 'Отменён'])
        if row[2] in ['Новый', 'В обработке', 'Доставляется', 'Выполнен', 'Отменён']:
            status_e.setCurrentText(row[2])
        address_e = QLineEdit(row[3] or '')
        order_date_e = QLineEdit(row[4].isoformat() if row[4] else '')
        order_date_e.setPlaceholderText('yyyy-MM-dd')
        delivery_date_e = QLineEdit(row[5].isoformat() if row[5] else '')
        delivery_date_e.setPlaceholderText('yyyy-MM-dd')
        form.addRow('Артикул:', article_e)
        form.addRow('Статус:', status_e)
        form.addRow('Адрес выдачи:', address_e)
        form.addRow('Дата заказа:', order_date_e)
        form.addRow('Дата доставки:', delivery_date_e)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        form.addRow(bb)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        order_date = order_date_e.text().strip() or None
        delivery_date = delivery_date_e.text().strip() or None
        try:
            cursor = conn.cursor()
            cursor.execute("""update orders set article=%s, status=%s, pickup_address=%s,
                              order_date=%s, delivery_date=%s where id=%s""",
                           (article_e.text(), status_e.currentText(), address_e.text(),
                            order_date, delivery_date, row[0]))
        except Exception as e:
            QMessageBox.warning(self, 'Ошибка', f'Не удалось обновить заказ: {e}')
            return
        self.load_data()

    def delete_order(self, row):
        reply = QMessageBox.question(self, 'Удалить', f'Удалить заказ "{row[1]}"?',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            cursor = conn.cursor()
            cursor.execute("""delete from orders where id=%s""", (row[0],))
            self.load_data()

class ManagerWindow(QWidget):
    def __init__(self, full_name, login_win):
        super().__init__()
        self.login_win = login_win
        self.resize(950, 680)
        self.setWindowIcon(QIcon('resources/lopushok.ico'))
        self.setWindowTitle(f'Менеджер: {full_name}')
        top_layout = QHBoxLayout()
        label_logo = QLabel()
        pixmap = QPixmap('resources/lopushok.png')
        if not pixmap.isNull():
            label_logo.setPixmap(pixmap.scaled(120, 80, Qt.AspectRatioMode.KeepAspectRatio))
        self.search_ql = QLineEdit()
        self.search_ql.setPlaceholderText('Поиск...')
        self.search_ql.textChanged.connect(self.search)
        self.cat_combo = QComboBox()
        self.cat_combo.addItem('Все категории', None)
        cursor = conn.cursor()
        cursor.execute("""SELECT id, name FROM categories ORDER BY name""")
        for row in cursor.fetchall():
            self.cat_combo.addItem(row[1], row[0])
        self.cat_combo.currentIndexChanged.connect(self.search)
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(['Без сортировки', 'Цена ↑', 'Цена ↓', 'Количество ↑', 'Количество ↓'])
        self.sort_combo.currentIndexChanged.connect(self.search)

        self.orders_btn = QPushButton('Заказы')
        self.orders_btn.clicked.connect(self.open_orders)
        self.logout_btn = QPushButton('Выйти')
        self.logout_btn.clicked.connect(self.logout)
        top_layout.addWidget(label_logo)
        top_layout.addWidget(self.search_ql)
        top_layout.addWidget(self.cat_combo)
        top_layout.addWidget(self.sort_combo)

        top_layout.addWidget(self.orders_btn)
        top_layout.addWidget(self.logout_btn)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        self.content_layout = QVBoxLayout(content_widget)
        scroll.setWidget(content_widget)
        layout = QVBoxLayout(self)
        layout.addLayout(top_layout)
        layout.addWidget(scroll)
        self.load_data()

    def logout(self):
        self.hide()
        self.login_win.show_again()

    def open_orders(self):
        self.orders_win = OrdersWindow(can_edit=False)
        self.orders_win.show()

    def load_data(self):
        cursor = conn.cursor()
        cursor.execute(_ITEMS_Q)
        for row in cursor.fetchall():
            self.load_card(row)

    def load_card(self, row):
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.Box)
        qty = int(row[10] or 0)
        disc = float(row[6] or 0)
        if qty == 0:
            frame.setStyleSheet("background-color: #ADD8E6;")
        elif disc > 15:
            frame.setStyleSheet("background-color: #2E8B57;")
        label_pic = QLabel()
        if not row[5]:
            pixmap = QPixmap('resources/picture.png')
        else:
            pixmap = QPixmap(f'resources/products/{row[5]}')
        label_pic.setPixmap(pixmap.scaled(100, 100))
        if disc > 0:
            final = float(row[4]) * (1 - disc / 100)
            price_html = (f'<span style="color:red;text-decoration:line-through">{float(row[4]):.2f}</span>'
                          f' <span style="color:black">{final:.2f}</span> руб.')
        else:
            price_html = f'{float(row[4]):.2f} руб.'
        info_lbl = QLabel(
            f'<b>{row[3]} | {row[1]}</b><br>'
            f'Описание: {row[2]}<br>'
            f'Производитель: {row[7] or "—"}<br>'
            f'Поставщик: {row[8] or "—"}<br>'
            f'Цена: {price_html}<br>'
            f'Единица измерения: {row[9] or "шт"}<br>'
            f'Количество на складе: {qty}'
        )
        info_lbl.setTextFormat(Qt.TextFormat.RichText)
        info_lbl.setWordWrap(True)
        disc_lbl = QLabel(f'Скидка\n{disc:.0f}%' if disc > 0 else 'Нет\nскидки')
        disc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        disc_lbl.setFixedWidth(80)
        disc_lbl.setFrameShape(QFrame.Shape.Box)

        layout_card = QHBoxLayout(frame)
        layout_card.addWidget(label_pic)
        layout_card.addWidget(info_lbl, 1)
        layout_card.addWidget(disc_lbl)

        self.content_layout.addWidget(frame)

    def search(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        name = self.search_ql.text().strip()
        cat = self.cat_combo.currentData()
        query = _ITEMS_Q + " WHERE items.name LIKE %s"
        params = [f'%{name}%']
        if cat:
            query += " AND items.category_id = %s"
            params.append(cat)
        sort = self.sort_combo.currentText()
        if sort == 'Цена ↑':
            query += " ORDER BY items.price ASC"
        elif sort == 'Цена ↓':
            query += " ORDER BY items.price DESC"
        elif sort == 'Количество ↑':
            query += " ORDER BY items.quantity ASC"
        elif sort == 'Количество ↓':
            query += " ORDER BY items.quantity DESC"
        cursor = conn.cursor()
        cursor.execute(query, params)
        for row in cursor.fetchall():
            self.load_card(row)

class UserWindow(QWidget):
    def __init__(self, full_name, login_win):
        super().__init__()
        self.login_win = login_win
        self.resize(950, 680)
        self.setWindowIcon(QIcon('resources/lopushok.ico'))
        self.setWindowTitle(f'Пользователь: {full_name}')
        top_layout = QHBoxLayout()
        label_logo = QLabel()
        pixmap = QPixmap('resources/lopushok.png')
        if not pixmap.isNull():
            label_logo.setPixmap(pixmap.scaled(120, 80, Qt.AspectRatioMode.KeepAspectRatio))

        self.logout_btn = QPushButton('Выйти')
        self.logout_btn.clicked.connect(self.logout)
        top_layout.addWidget(label_logo)
        top_layout.addStretch()

        top_layout.addWidget(self.logout_btn)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        self.content_layout = QVBoxLayout(content_widget)
        scroll.setWidget(content_widget)
        layout = QVBoxLayout(self)
        layout.addLayout(top_layout)
        layout.addWidget(scroll)
        self.load_data()

    def logout(self):
        self.hide()
        self.login_win.show_again()



    def load_data(self):
        cursor = conn.cursor()
        cursor.execute(_ITEMS_Q)
        for row in cursor.fetchall():
            self.load_card(row)

    def load_card(self, row):
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.Box)
        qty = int(row[10] or 0)
        disc = float(row[6] or 0)
        if qty == 0:
            frame.setStyleSheet("background-color: #ADD8E6;")
        elif disc > 15:
            frame.setStyleSheet("background-color: #2E8B57;")
        label_pic = QLabel()
        if not row[5]:
            pixmap = QPixmap('resources/picture.png')
        else:
            pixmap = QPixmap(f'resources/products/{row[5]}')
        label_pic.setPixmap(pixmap.scaled(100, 100))
        if disc > 0:
            final = float(row[4]) * (1 - disc / 100)
            price_html = (f'<span style="color:red;text-decoration:line-through">{float(row[4]):.2f}</span>'
                          f' <span style="color:black">{final:.2f}</span> руб.')
        else:
            price_html = f'{float(row[4]):.2f} руб.'
        info_lbl = QLabel(
            f'<b>{row[3]} | {row[1]}</b><br>'
            f'Описание: {row[2]}<br>'
            f'Производитель: {row[7] or "—"}<br>'
            f'Поставщик: {row[8] or "—"}<br>'
            f'Цена: {price_html}<br>'
            f'Единица измерения: {row[9] or "шт"}<br>'
            f'Количество на складе: {qty}'
        )
        info_lbl.setTextFormat(Qt.TextFormat.RichText)
        info_lbl.setWordWrap(True)
        disc_lbl = QLabel(f'Скидка\n{disc:.0f}%' if disc > 0 else 'Нет\nскидки')
        disc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        disc_lbl.setFixedWidth(80)
        disc_lbl.setFrameShape(QFrame.Shape.Box)

        layout_card = QHBoxLayout(frame)
        layout_card.addWidget(label_pic)
        layout_card.addWidget(info_lbl, 1)
        layout_card.addWidget(disc_lbl)

        self.content_layout.addWidget(frame)


class GuestWindow(QWidget):
    def __init__(self, login_win):
        super().__init__()
        self.login_win = login_win
        self.resize(950, 680)
        self.setWindowIcon(QIcon('resources/lopushok.ico'))
        self.setWindowTitle('Гость')
        top_layout = QHBoxLayout()
        label_logo = QLabel()
        pixmap = QPixmap('resources/lopushok.png')
        if not pixmap.isNull():
            label_logo.setPixmap(pixmap.scaled(120, 80, Qt.AspectRatioMode.KeepAspectRatio))
        self.logout_btn = QPushButton('Выйти')
        self.logout_btn.clicked.connect(self.logout)
        top_layout.addWidget(label_logo)
        top_layout.addStretch()
        top_layout.addWidget(self.logout_btn)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        self.content_layout = QVBoxLayout(content_widget)
        scroll.setWidget(content_widget)
        layout = QVBoxLayout(self)
        layout.addLayout(top_layout)
        layout.addWidget(scroll)
        self.load_data()

    def logout(self):
        self.hide()
        self.login_win.show_again()

    def load_data(self):
        cursor = conn.cursor()
        cursor.execute(_ITEMS_Q)
        for row in cursor.fetchall():
            self.load_card(row)

    def load_card(self, row):
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.Box)
        qty = int(row[10] or 0)
        disc = float(row[6] or 0)
        if qty == 0:
            frame.setStyleSheet("background-color: #ADD8E6;")
        elif disc > 15:
            frame.setStyleSheet("background-color: #2E8B57;")
        label_pic = QLabel()
        if not row[5]:
            pixmap = QPixmap('resources/picture.png')
        else:
            pixmap = QPixmap(f'resources/products/{row[5]}')
        label_pic.setPixmap(pixmap.scaled(100, 100))
        if disc > 0:
            final = float(row[4]) * (1 - disc / 100)
            price_html = (f'<span style="color:red;text-decoration:line-through">{float(row[4]):.2f}</span>'
                          f' <span style="color:black">{final:.2f}</span> руб.')
        else:
            price_html = f'{float(row[4]):.2f} руб.'
        info_lbl = QLabel(
            f'<b>{row[3]} | {row[1]}</b><br>'
            f'Описание: {row[2]}<br>'
            f'Производитель: {row[7] or "—"}<br>'
            f'Поставщик: {row[8] or "—"}<br>'
            f'Цена: {price_html}<br>'
            f'Единица измерения: {row[9] or "шт"}<br>'
            f'Количество на складе: {qty}'
        )
        info_lbl.setTextFormat(Qt.TextFormat.RichText)
        info_lbl.setWordWrap(True)
        disc_lbl = QLabel(f'Скидка\n{disc:.0f}%' if disc > 0 else 'Нет\nскидки')
        disc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        disc_lbl.setFixedWidth(80)
        disc_lbl.setFrameShape(QFrame.Shape.Box)
        layout_card = QHBoxLayout(frame)
        layout_card.addWidget(label_pic)
        layout_card.addWidget(info_lbl, 1)
        layout_card.addWidget(disc_lbl)
        self.content_layout.addWidget(frame)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = LoginWindow()
    win.show()
    sys.exit(app.exec())



# drop DATABASE attempt7;
#
# CREATE DATABASE attempt7;
# USE attempt7;
#
# CREATE TABLE categories (
#   id   INT AUTO_INCREMENT PRIMARY KEY,
#   name VARCHAR(255) NOT NULL
# );
#
# CREATE TABLE manufacturers (
#   id   INT AUTO_INCREMENT PRIMARY KEY,
#   name VARCHAR(255) NOT NULL
# );
#
# CREATE TABLE suppliers (
#   id   INT AUTO_INCREMENT PRIMARY KEY,
#   name VARCHAR(255) NOT NULL
# );
#
# CREATE TABLE users (
#   id        INT AUTO_INCREMENT PRIMARY KEY,
#   login     VARCHAR(255),
#   password  VARCHAR(255),
#   role      VARCHAR(255),
#   full_name VARCHAR(255) NOT NULL DEFAULT ''
# );
#
# CREATE TABLE items (
#   id              INT AUTO_INCREMENT PRIMARY KEY,
#   name            VARCHAR(255),
#   description     VARCHAR(255),
#   category_id     INT,
#   price           DECIMAL(10,2),
#   photo           VARCHAR(255),
#   discount        DECIMAL(5,2)  DEFAULT 0.00,
#   manufacturer_id INT,
#   supplier_id     INT,
#   unit            VARCHAR(50)   DEFAULT 'шт',
#   quantity        INT           DEFAULT 0,
#   FOREIGN KEY (category_id)     REFERENCES categories(id),
#   FOREIGN KEY (manufacturer_id) REFERENCES manufacturers(id),
#   FOREIGN KEY (supplier_id)     REFERENCES suppliers(id)
# );
#
# CREATE TABLE orders (
#   id             INT AUTO_INCREMENT PRIMARY KEY,
#   article        VARCHAR(100)  DEFAULT '',
#   id_user        INT,
#   id_item        INT,
#   price_paid     DECIMAL(10,2),
#   status         VARCHAR(50)   DEFAULT 'Новый',
#   pickup_address VARCHAR(255)  DEFAULT '',
#   order_date     DATE,
#   delivery_date  DATE,
#   ordered_at     DATETIME      DEFAULT CURRENT_TIMESTAMP,
#   FOREIGN KEY (id_user) REFERENCES users(id),
#   FOREIGN KEY (id_item) REFERENCES items(id)
# );
#
# INSERT INTO categories (name) VALUES
#   ('Электроника'),
#   ('Периферия'),
#   ('Аудио'),
#   ('Аксессуары'),
#   ('Комплектующие');
#
# INSERT INTO manufacturers (name) VALUES
#   ('Dell'),
#   ('Logitech'),
#   ('Razer'),
#   ('LG'),
#   ('Sony'),
#   ('Gembird'),
#   ('Samsung'),
#   ('Kingston'),
#   ('SteelSeries');
#
# INSERT INTO suppliers (name) VALUES
#   ('ТехноМаркет'),
#   ('ПериферийОпт'),
#   ('ГеймерСнаб'),
#   ('ДисплейТорг'),
#   ('АудиоСклад'),
#   ('КомпОптТорг'),
#   ('ДисковыйСклад'),
#   ('МемориТрейд');
#
# INSERT INTO users (login, password, role, full_name) VALUES
#   ('admin',   'admin',   'admin',   'Иванов Иван Иванович'),
#   ('manager', 'manager', 'manager', 'Петрова Мария Сергеевна'),
#   ('user1',   'user1',   'user',    'Сидоров Алексей Петрович'),
#   ('user2',   'user2',   'user',    'Козлова Елена Николаевна');
#
# INSERT INTO items
#   (name, description, category_id, price, photo, discount,
#    manufacturer_id, supplier_id, unit, quantity)
# VALUES
#   ('Ноутбук Dell XPS',        'Ультрабук 15", Core i7, 16GB RAM',        1, 85000.00, 'paper_0.jpeg', 10.00, 1, 1, 'шт',  5),
#   ('Мышь Logitech MX',        'Беспроводная эргономичная мышь',          2,  4200.00, 'paper_1.jpeg',  0.00, 2, 2, 'шт',  0),
#   ('Клавиатура Razer',        'Механическая RGB клавиатура',             2,  9500.00, 'paper_2.jpeg',  5.00, 3, 3, 'шт', 12),
#   ('Монитор LG 27"',          'IPS 4K монитор, 60 Гц',                   1, 32000.00, 'paper_3.jpeg', 15.00, 4, 4, 'шт',  3),
#   ('Наушники Sony WH-1000',   'Беспроводные с шумоподавлением',          3, 19900.00, 'paper_4.jpeg', 20.00, 5, 5, 'шт',  8),
#   ('Веб-камера Logitech C920','Full HD 1080p, автофокус',                2,  5800.00, 'paper_5.jpeg',  0.00, 2, 2, 'шт', 15),
#   ('USB-хаб 7 портов',        'USB 3.0, питание от сети',                4,  1900.00, 'paper_6.jpeg',  0.00, 6, 6, 'шт',  0),
#   ('SSD Samsung 1TB',         'NVMe M.2, скорость чтения 3500 МБ/с',    5, 10500.00, 'paper_7.jpeg', 10.00, 7, 7, 'шт', 20),
#   ('ОЗУ Kingston 16GB',       'DDR4 3200MHz, 2x8GB',                     5,  5200.00, '',             18.00, 8, 8, 'шт',  7),
#   ('Коврик SteelSeries',      'Большой игровой, 900x400 мм',             4,  1200.00, '',              0.00, 9, 3, 'шт', 30);
#
# INSERT INTO orders (article, id_user, id_item, price_paid, status,
#                     pickup_address, order_date, delivery_date) VALUES
#   ('ORD-2026-001', 3, 2,  4200.00, 'Выполнен',    'ул. Ленина 1, ПВЗ №3',   '2026-05-10', '2026-05-13'),
#   ('ORD-2026-002', 3, 4, 27200.00, 'В обработке', 'пр. Победы 55, ПВЗ №7',  '2026-05-20', '2026-05-25'),
#   ('ORD-2026-003', 4, 1, 76500.00, 'Доставляется','ул. Садовая 12, ПВЗ №1', '2026-05-22', '2026-05-28'),
#   ('ORD-2026-004', 4, 8,  9450.00, 'Новый',       'ул. Мира 33, ПВЗ №5',    '2026-05-25', '2026-05-30');
