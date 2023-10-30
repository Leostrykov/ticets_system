import sys
from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QMessageBox
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QDateTime
import sqlite3
import json

db = sqlite3.connect('ticets_db.sqlite3')
cur = db.cursor()


class AddSession(QMainWindow):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.id = None
        self.link_picture = None
        uic.loadUi('interfaces/session_add.ui', self)
        self.searchWordFilm = ''
        self.dateTime_startted.setDateTime(QDateTime.currentDateTime())
        for i in cur.execute('SELECT name FROM halls;').fetchall():
            self.halls.addItem(i[0])
        self.interface()

        self.list_of_films.itemSelectionChanged.connect(self.select_film)
        self.search_line.textChanged.connect(self.search)
        self.load_pic_btn.clicked.connect(self.set_picture)
        self.save_btn.clicked.connect(self.save)
        self.add_film_btn.clicked.connect(self.add_film)
        self.delete_btn.clicked.connect(self.delete_film)
        self.create_session_btn.clicked.connect(self.create_session)

    def interface(self):
        # загружаем фильмы
        try:
            self.list_of_films.clear()
            self.films.clear()
            if len(self.searchWordFilm) == 0:
                films = cur.execute('''SELECT name FROM sessions ORDER BY name;''').fetchall()
            else:
                films = cur.execute(f'''SELECT name FROM sessions 
                WHERE name LIKE '%{self.searchWordFilm.lower()}%';''')
            for i in films:
                self.list_of_films.addItem(i[0].title())
                self.films.addItem(i[0].title())
        except ValueError:
            self.statusBar().showMessage('Не удалось загрузить фильмы')

    def select_film(self):
        # загружаем данные о выбранном фильме
        try:
            selected_items = self.list_of_films.selectedItems()
            if selected_items is not None:
                for item in selected_items:
                    self.link_picture = None
                    text = item.text()
                    film = cur.execute('''SELECT * FROM sessions WHERE name = '%s';''' % text.lower()).fetchone()
                    self.id = film[0]
                    self.film_name.setText(film[1].title())
                    # Звгружаем изображение фильма
                    pixmap = QPixmap()
                    pixmap.loadFromData(film[3])
                    self.picture_film.setPixmap(pixmap)
                    self.about_of_film.setPlainText(film[2])
                    self.load_pic_btn.setEnabled(True)
                    self.save_btn.setEnabled(True)
                    self.delete_btn.setEnabled(True)
        except ValueError:
            self.statusBar().showMessage('Ошибка: не удалось загрузить фильм')

    def search(self):
        self.searchWordFilm = self.search_line.text()
        self.interface()

    def set_picture(self):
        try:
            self.link_picture = QFileDialog.getOpenFileName(self, 'Выбрать картинку: ', 'Документы',
                                                            'Картинка (*.png);;Картинка (*.jpeg);;Картинка ('
                                                            '*.webp);;Картинка(*.jpg);;Все файлы (*)')[0]
            if len(self.link_picture) > 0:
                pixmap = QPixmap(self.link_picture)
                self.picture_film.setPixmap(pixmap)
        except ValueError():
            self.statusBar().showMessage('Не удалось открыть изображение')

    def save(self):
        name = self.film_name.text()
        about = self.about_of_film.toPlainText()
        if self.link_picture is None:
            cur.execute('''UPDATE sessions
                        SET name = '%s', about = '%s'
                        WHERE id = %s; ''' % (name.lower(), about, self.id))
        else:
            with open(self.link_picture, 'rb') as picture:
                picture = picture.read()
                cur.execute('''UPDATE sessions
                            SET name = '%s',
                            about = '%s',
                            picture = ?
                            WHERE id = %s ''' % (name.lower(), about, self.id), (picture,))
        db.commit()
        self.statusBar().showMessage('Изменения сохранены')
        self.interface()

    def add_film(self):
        self.hide()
        add_form = AddFilm(self)
        add_form.show()

    def delete_film(self):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Question)
        msg_box.setWindowTitle("Подтверждение")
        msg_box.setText("Вы уверены, что хотите удалить фильм? Если удалите этот фильм то все сеансы с этим фильмом "
                        "тоже будут удалены.")
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        result = msg_box.exec_()

        if result == QMessageBox.Yes:
            cur.execute('DELETE from sessions WHERE id = %s;' % self.id)
            cur.execute('DELETE from sessions_in_cinema WHERE session_id = %s;' % self.id)
            db.commit()
            self.parent.interface()
            self.interface()

    def create_session(self):
        film = cur.execute('SELECT id FROM sessions WHERE name = "%s"' % self.films.currentText().lower()).fetchone()[0]
        datetime_start = self.dateTime_startted.dateTime().toString("yyyy-MM-dd hh:mm:00")
        hall = cur.execute('SELECT * FROM halls WHERE name = "%s"' % self.halls.currentText()).fetchone()
        duration = self.duration_session.value()
        datetime_end = self.dateTime_startted.dateTime().addSecs(duration * 60).toString("yyyy-MM-dd hh:mm:00")
        if cur.execute('''SELECT id FROM sessions_in_cinema
    WHERE (DATETIME('%s') BETWEEN DATETIME(datetime_start) AND DATETIME(datetime_end)) OR 
    (DATETIME('%s') BETWEEN DATETIME(datetime_start) AND DATETIME(datetime_end)) AND hall_id = %s;''' %
                       (datetime_start, datetime_end, hall[0])).fetchone() is None:
            seats = [['*' for _ in range(hall[3])] for _ in range(hall[2])]
            cur.execute('''INSERT INTO sessions_in_cinema(session_id, datetime_start, datetime_end, duration, 
            hall_id, seats)
            VALUES (%s, '%s', '%s', %s, %s, '%s');''' % (film, datetime_start,
                                                         datetime_end, duration,
                                                         hall[0], json.dumps(seats)))
            db.commit()
            self.parent.interface()
            self.statusBar().showMessage('Успешно создано')
        else:
            self.statusBar().showMessage('В это время назначен другой сеанс')


class AddFilm(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi('interfaces/add_film.ui', self)
        self.centralwidget.setLayout(self.verticalLayout)
        self.link_picture = None
        self.load_pic_btn.clicked.connect(self.select_picture)
        self.add_btn.clicked.connect(self.add)

    def add(self):
        if self.link_picture is not None:
            name = self.film_name.text().lower()
            about = self.about_of_film.toPlainText()
            with open(self.link_picture, 'rb') as picture:
                picture = picture.read()
                cur.execute('''INSERT INTO sessions(name, about, picture) VALUES('%s', '%s', ?);''' % (name, about),
                            [picture])
                db.commit()

            self.close()
            self.parent().show()
            self.parent().interface()
        else:
            self.statusBar().showMessage('Все поля долны быть заполнены')

    def closeEvent(self, event):
        self.parent().show()

    def select_picture(self):
        try:
            self.link_picture = QFileDialog.getOpenFileName(self, 'Выбрать картинку: ', 'Документы',
                                                            'Картинка (*.png);;Картинка (*.jpeg);;Картинка ('
                                                            '*.webp);;Картинка(*.jpg);;Все файлы (*)')[0]
            pixmap = QPixmap(self.link_picture)
            self.picture_film.setPixmap(pixmap)
        except ValueError():
            self.statusBar().showMessage('Не удалось открыть изображение')


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)
