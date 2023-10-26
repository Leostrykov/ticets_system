from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QApplication
import sqlite3
import sys

keyboard = ['qwertyuiop', 'asdfghjkl', 'zxcvbnm', 'фывапролджэё', 'йцукенгшщзхъ', 'фывапролджэ', 'ячсмитьбю']

db = sqlite3.connect('ticets_db.sqlite3')
cur = db.cursor()


class SetUserInformation(QMainWindow):
    def __init__(self, user):
        super().__init__()
        uic.loadUi('interfaces/user_information.ui', self)
        self.user = user
        self.user_name.setText(user[1])
        self.user_login.setText(user[2])
        self.user_type.setText(cur.execute('SELECT title FROM user_types WHERE id = %s' % user[4]).fetchone()[0])
        self.pushButton.clicked.connect(self.save)

    def save(self):
        a = cur.execute('SELECT id FROM users WHERE login = "%s"' % self.user_login.text()).fetchone()
        print(a)
        if cur.execute('SELECT id FROM users WHERE login = "%s"' % self.user_login.text()).fetchone() is None:
            try:
                if self.user_password.text() > 0:
                    self.check_password(self.user_password.text())
                cur.execute('UPDATE users SET login = "%s", password = "%s" WHERE id = %s' %
                            (self.user_login.text(),
                             self.user_password.text(),
                             self.user[0]))
                db.commit()
                self.statusBar().showMessage('Данные обновлены')
            except ValueError as err:
                self.statusBar().showMessage(str(err))

    def check_password(password):
        if len(password) <= 8:
            raise ValueError('Длина пароля более 8 символов')
        number_in_passsword = False
        big_w = False
        small_w = False
        for i in password:
            if i.isalpha():
                if i.isupper():
                    big_w = True
                elif i.islower():
                    small_w = True
            elif i.isdigit():
                number_in_passsword = True
        if not (big_w and small_w):
            raise ValueError('В пароле должны быть заглавные и строчные буквы')
        elif not number_in_passsword:
            raise ValueError('В пароле должна быть хотя бы одна цифра')

        for i in keyboard:
            for r in range(len(i)):
                if r + 3 <= len(i):
                    if i[r: r + 3] in password.lower():
                        raise ValueError('Пароль слишком простой')
        print('ok')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    s = SetUserInformation((3, 'Струков Леонид', 'admin', 'admin', 2))
    s.show()
    sys.exit(app.exec())