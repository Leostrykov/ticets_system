import sys
from PyQt5.QtWidgets import QMainWindow, QWidget, QPushButton
from PyQt5.QtGui import QPainter, QColor, QFont
from PyQt5.QtCore import Qt
import sqlite3
import json
import jinja2
import qrcode
from PyQt5.QtGui import QTextDocument
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog

db = sqlite3.connect('ticets_db.sqlite3')
cur = db.cursor()


class SeatWidget(QWidget):
    def __init__(self, row, seat_number, status, window):
        super().__init__()
        self.row = row
        self.seat_number = seat_number
        self.status = status
        self.clicked = False
        self.parent = window

    def paintEvent(self, event):
        painter = QPainter(self)

        color = (250, 5, 15)
        if self.status == 'F':
            color = (27, 161, 169)
        elif self.status == 'S':
            color = (250, 150, 14)
        painter.setBrush(QColor(*color))
        painter.drawRect(5, 5, self.width(), self.height())

        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Arial", 12))
        painter.drawText(5, 20, str(self.seat_number + 1))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked = not self.clicked
            if self.status != 'E':
                if self.clicked:
                    self.status = "S"
                    self.parent.select_seats.append((self.row, self.seat_number))
                    self.parent.order_button.setEnabled(True)
                else:
                    self.status = 'F'
                    del self.parent.select_seats[self.parent.select_seats.index((self.row, self.seat_number))]
                    if len(self.parent.select_seats) == 0:
                        self.parent.order_button.setEnabled(False)
                self.update()


class CinemaLayout(QMainWindow):
    def __init__(self, session_id):
        super().__init__()
        self.session = cur.execute('SELECT * FROM sessions_in_cinema WHERE id = %s' % session_id).fetchone()
        self.film_name = cur.execute('SELECT name FROM sessions WHERE id = %s' % self.session[1]).fetchone()[0].title()
        self.seats = json.loads(self.session[6])
        self.order_button = QPushButton("Заказать", self)
        self.select_seats = []
        self.order_button.setEnabled(False)
        self.order_button.clicked.connect(self.order)
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.film_name)

        seats_layout = self.createSeatsLayout()
        self.order_button.setStyleSheet('QPushButton {background-color: #ff3118; border-radius: 10px; '
                                        'color: white; padding: 5px; font: 9pt "Arial";}')
        self.setCentralWidget(seats_layout)

    def createSeatsLayout(self):
        rows = len(self.seats)
        cols = len(self.seats[0])
        seat_width = 40
        seat_height = 40

        self.setGeometry(100, 100, 41 * cols, 45 * rows)

        seats_layout = QWidget()
        seats_layout.setGeometry(10, 10, (cols + 1) * seat_width, rows * seat_height)

        for row in range(len(self.seats)):
            for col in range(len(self.seats[row])):
                seat = SeatWidget(row, col, self.seats[row][col], self)
                seat.setGeometry(col * seat_width, row * seat_height, seat_width, seat_height)
                seat.setParent(seats_layout)
                seat.show()

        self.order_button.setGeometry(0, rows * seat_height + 5, cols * seat_width, 30)
        self.order_button.setParent(seats_layout)

        return seats_layout

    def order(self):
        for seat in self.select_seats:
            self.seats[seat[0]][seat[1]] = 'E'
            cur.execute('''INSERT INTO tickets (session) VALUES (%s);''' % self.session[0])
            id_ticket = cur.lastrowid
            self.print_ticket(id_ticket, seat)
        cur.execute('''UPDATE sessions_in_cinema SET seats = '%s' WHERE id = %s;''' % (json.dumps(self.seats),
                                                                                       self.session[0]))
        db.commit()
        self.close()

    def print_ticket(self, ticket_id, seat):
        qr = qrcode.QRCode(
            version=5,
            box_size=128,
            border=3
        )

        qr.add_data(f'ticket_id: {ticket_id}')
        image = qr.make_image()
        image.save('qr_code.png')

        hall = cur.execute('SELECT name FROM halls WHERE id = %s' % self.session[3]).fetchone()[0]

        content = {
            'cinema_name': 'Сияние',
            'film_name': self.film_name,
            'datetime_start': self.session[2],
            'datetime_end': self.session[5],
            'hall': hall,
            'row_number': seat[0] + 1,
            'seat_number': seat[1] + 1,
            'ticket_id': ticket_id
        }

        template_loader = jinja2.FileSystemLoader('./')
        template_env = jinja2.Environment(loader=template_loader)
        template = template_env.get_template('ticket.html')
        output_text = template.render(content)

        printer = QPrinter()

        document = QTextDocument()

        document.setHtml(output_text)

        print_dialog = QPrintDialog(printer, self)

        if print_dialog.exec_() == QPrintDialog.Accepted:
            document.print_(printer)


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)
