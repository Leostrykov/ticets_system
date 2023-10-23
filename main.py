import sys
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtGui import QPixmap
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
                    self.second_form = MainWindowCashier(info_user)
                    self.second_form.show()
                else:
                    raise ValueError('Неверный пароль или логин')
            else:
                raise ValueError('Все поля должны быть заполнеными')
        except ValueError as err:
            self.statusBar().showMessage(str(err))


# Главная страница для кассиров
class MainWindowCashier(QMainWindow):
    def __init__(self, info_user):
        super().__init__()
        uic.loadUi('interfaces/main_window_Cashier.ui', self)
        self.setMinimumSize(1081, 643)
        self.centralwidget.setLayout(self.gridLayout)
        self.user_name.setText(info_user[1])
        self.interface()

    def interface(self):
        # загружаем сеансы
        try:
            sessions = cur.execute('''SELECT (SELECT name FROM sessions WHERE sessions.id = 
            sessions_in_cinema.session_id) as name, datetime_start 
            FROM sessions_in_cinema;''').fetchall()
            for i in sessions:
                self.list_of_sessions.addItem(f'{i[0]} | {i[1]}')
            self.list_of_sessions.itemSelectionChanged.connect(self.select_session)
        except ValueError:
            self.statusBar().showMessage('Не удалось загрузить сеансы')

    def select_session(self):
        # загружаем данные о выбранном сеансе
        try:
            selected_items = self.list_of_sessions.selectedItems()
            if selected_items is not None:
                for item in selected_items:
                    text = item.text().split(' | ')
                    session = cur.execute('''SELECT sessions_in_cinema.id, sessions.name, sessions.about, 
                    sessions_in_cinema.datetime_start, sessions.picture FROM sessions_in_cinema
                    INNER JOIN sessions ON '%s' = sessions.name
                    WHERE sessions_in_cinema.datetime_start = '%s';''' % (text[0], text[1])).fetchone()
                    self.session_name.setText(session[1])
                    # Звгружаем изображение сеанса
                    pixmap = QPixmap()
                    pixmap.loadFromData(session[4])
                    self.picture.setPixmap(pixmap)

                    self.time.setText(session[3])
                    self.about.setPlainText(session[2])
        except ValueError:
            self.statusBar().showMessage('Ошибка: не удалось загрузить сеанс')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = LoginPage()
    win.show()
    sys.exit(app.exec())
