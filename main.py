import sys
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QDate
from add_sesion import AddSession
from hall_sheme import CinemaLayout
import sqlite3

db = sqlite3.connect('ticets_db.sqlite3')
cur = db.cursor()


# страница авторазации
class LoginPage(QMainWindow):
    def __init__(self):
        super().__init__()
        self.second_form = None
        uic.loadUi('interfaces/login_page.ui', self)
        self.setFixedSize(470, 267)
        self.login.returnPressed.connect(self.password.setFocus)
        self.password.returnPressed.connect(self.log_in)
        self.btn.clicked.connect(self.log_in)

    def log_in(self):
        try:
            if len(self.login.text()) != 0 and len(self.password.text()):
                info_user = cur.execute('''SELECT * FROM users
                                            WHERE login = '%s' and password = '%s';''' %
                                        (self.login.text(), self.password.text())).fetchone()
                if info_user is not None:
                    self.close()
                    self.second_form = MainWindow(info_user)
                    self.second_form.show()

                else:
                    raise ValueError('Неверный пароль или логин')
            else:
                raise ValueError('Все поля должны быть заполнеными')
        except ValueError as err:
            self.statusBar().showMessage(str(err))


# Главная страница для кассиров
class MainWindow(QMainWindow):
    def __init__(self, info_user):
        super().__init__()
        self.is_admin = False
        self.session_id = None

        if info_user[4] == 1:
            uic.loadUi('interfaces/main_window_Cashier.ui', self)
        elif info_user[4] == 2:
            uic.loadUi('interfaces/main_window_Admin.ui', self)
            self.is_admin = True
            self.action_add_session.triggered.connect(self.addSession)
            self.action_delete_session.triggered.connect(self.deleteSession)

        self.setMinimumSize(1081, 684)
        self.centralwidget.setLayout(self.gridLayout)
        self.user_name.setText(info_user[1])
        self.searchWord = ''
        self.date = 'now'

        self.dateEdit.setDate(QDate.currentDate())
        self.search_l.textChanged.connect(self.search)
        self.list_of_sessions.itemSelectionChanged.connect(self.select_session)

        self.interface()
        self.dateEdit.dateChanged.connect(self.changetDate)
        self.exit_action.triggered.connect(self.exit_from_account)
        self.order_btn.clicked.connect(self.order)

    def interface(self):
        # загружаем сеансы
        try:
            self.list_of_sessions.clear()
            if len(self.searchWord) == 0:
                sessions = cur.execute('''SELECT (SELECT name FROM sessions 
                WHERE sessions.id = sessions_in_cinema.session_id) as name, datetime_start, 
                (SELECT name FROM halls WHERE id = sessions_in_cinema.hall_id) as hall FROM sessions_in_cinema 
                WHERE DATE(datetime_start) = DATE('%s');''' % self.date).fetchall()
            else:
                sessions = cur.execute(f'''SELECT (SELECT name FROM sessions 
                WHERE sessions.id = sessions_in_cinema.session_id) as name, datetime_start, 
                (SELECT name FROM halls WHERE id = sessions_in_cinema.hall_id) as hall FROM sessions_in_cinema 
                WHERE DATE(datetime_start) = DATE('{self.date}') and session_id = 
                (SELECT id FROM sessions WHERE name LIKE '%{self.searchWord.lower()}%');''')
            for i in sessions:
                self.list_of_sessions.addItem(f'{i[0].title()} | {i[1]} | {i[2]}')
        except ValueError:
            self.statusBar().showMessage('Не удалось загрузить сеансы')

    def select_session(self):
        # загружаем данные о выбранном сеансе
        self.order_btn.setEnabled(True)
        if self.is_admin:
            self.action_delete_session.setEnabled(True)
        try:
            selected_items = self.list_of_sessions.selectedItems()
            if selected_items is not None:
                for item in selected_items:
                    text = item.text().split(' | ')
                    session = cur.execute('''SELECT sessions_in_cinema.id, sessions.name, sessions.about, 
                    sessions_in_cinema.datetime_start, sessions.picture  FROM sessions_in_cinema
                    INNER JOIN sessions ON '%s' = sessions.name
                    WHERE sessions_in_cinema.datetime_start = '%s' and 
                    sessions_in_cinema.hall_id = (SELECT id FROM halls WHERE name = '%s');''' %
                                          (text[0].lower(), text[1], text[2])).fetchone()
                    self.session_id = session[0]
                    self.session_name.setText(session[1].title())
                    # Звгружаем изображение сеанса
                    pixmap = QPixmap()
                    pixmap.loadFromData(session[4])
                    self.picture.setPixmap(pixmap)

                    self.time.setText(session[3])
                    self.hall.setText(text[2])
                    self.about.setPlainText(session[2])
        except ValueError:
            self.statusBar().showMessage('Ошибка: не удалось загрузить сеанс')

    def changetDate(self, new_date):
        self.date = new_date.toString("yyyy-MM-dd")
        self.interface()

    def search(self):
        self.searchWord = self.search_l.text()
        self.interface()

    def exit_from_account(self):
        self.close()
        self.log_window = LoginPage()
        self.log_window.show()

    def addSession(self):
        self.sesion_add_form = AddSession(self)
        self.sesion_add_form.show()

    def deleteSession(self):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Question)
        msg_box.setWindowTitle("Подтверждение")
        msg_box.setText("Вы уверены, что хотите удалить сеанс?.")
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        result = msg_box.exec_()

        if result == QMessageBox.Yes:
            cur.execute('DELETE from sessions_in_cinema WHERE id = %s;' % self.session_id)
            db.commit()
            self.interface()
            self.interface()

    def order(self):
        self.sheme_form = CinemaLayout(self.session_id)
        self.sheme_form.show()


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = LoginPage()
    win.show()
    sys.excepthook = except_hook
    sys.exit(app.exec())
