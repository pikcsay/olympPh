import os
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtWidgets import QApplication, QButtonGroup, QDialog, QFileDialog, QInputDialog, \
    QLabel, QMainWindow, QMessageBox, QPushButton, QTableWidgetItem, QVBoxLayout, QWidget
from requests import get
from shutil import copy
import sqlite3
import sys

from design.design import Ui_MainWindow
from design.designDatetime import Ui_Dialog1
from design.designProblems import Ui_Dialog2


class OlympPhysics(QMainWindow, Ui_MainWindow):
    BD = 'bd/bd.sql'

    def __init__(self):
        super(OlympPhysics, self).__init__()
        self.setupUi(self)

        self.con = sqlite3.connect(OlympPhysics.BD)
        self.initUI()

    def initUI(self):
        cur = self.con.cursor()
        self.sites = [*map(lambda x: x[0], cur.execute("""SELECT title FROM Sites""").fetchall())]
        self.createGroupSites()

        self.wid_sites = WidSites(self.buttonGroupSites)
        self.scrollArea.setWidget(self.wid_sites)
        number_tour = cur.execute("SELECT DISTINCT number_tour FROM Tours").fetchall()
        self.comboBox.addItems([str(item[0]) for item in number_tour])

        self.scrollArea.show()
        self.scrollArea.setWidgetResizable(True)

        self.btnAddSite.clicked.connect(self.addSite)
        self.btnDelSite.clicked.connect(self.delSite)
        self.btnAddProblem.clicked.connect(self.addProblem)
        self.btnDelProblem.clicked.connect(self.delProblem)
        self.btnRandProblem.clicked.connect(self.getRandProblem)
        self.btnShowOlymp.clicked.connect(self.filter)
        self.btnSearchOlymp.clicked.connect(self.searchOlymp)
        self.btnMenuProblems.clicked.connect(self.getProblems)
        self.btnSaveNote.clicked.connect(self.saveNotes)
        self.btnShowNote.clicked.connect(self.showNotes)
        self.btnDeleteNote.clicked.connect(self.delNotes)

    def createGroupSites(self):

        cur = self.con.cursor()
        self.buttonGroupSites = QButtonGroup()
        for i in range(len(self.sites)):
            btn = QPushButton(self)
            btn.setText(f'{i + 1}) {self.sites[i]}')
            btn.clicked.connect(self.ViewWebSite)
            k = cur.execute("""SELECT id FROM Sites WHERE title = ?""",
                            (self.sites[i],)).fetchone()[0]
            btn.setObjectName(f'site{k}')
            self.buttonGroupSites.addButton(btn, id=i)

    def filter(self):
        """C его помощью будем настраивать работу кнопки 
        "Показать олимпиады" во вкладке "Олимпиады"""""

        cur = self.con.cursor()
        # Отправляем запрос на получение данных
        result = cur.execute(f"""
                        SELECT Olimp.Олимпиада, Tours.number_tour, 
                        Tours.data_tour, Olimp.sites_tour
                        FROM Olimp, Tours ON Olimp.id = Tours.id_olymp 
                        WHERE Tours.number_tour = {self.comboBox.currentIndex() + 1}""").fetchall()
        # Выводим данные в таблицу
        self.tableWidget.setRowCount(len(result))
        self.tableWidget.setColumnCount(len(result[0]))
        self.tableWidget.setHorizontalHeaderLabels(['Олимпиада', 'Номер тура', 'Дата', 'Сайт'])
        for i, elem in enumerate(result):
            for j, val in enumerate(elem):
                self.tableWidget.setItem(i, j, QTableWidgetItem(str(val)))

    def searchOlymp(self):
        """С помошью этого метода мы будем искать необходимые для нас олимпиады"""

        cur = self.con.cursor()
        # Если вписанный запрос нашёлся в базе данных, выводим надпись в статус баре
        if self.lineEdit.text():
            self.statusBar().showMessage('Нашлись записи по указанному запросу', 3000)
            # Выполняем запрос на добавление данных в таблицу
            result = cur.execute(
                "SELECT DISTINCT Olimp.Олимпиада, Tours.number_tour, "
                "Tours.data_tour, Olimp.sites_tour "
                "FROM Olimp, Tours ON Olimp.id = Tours.id_olymp "
                "WHERE Olimp.Олимпиада = ?", (self.lineEdit.text(),)).fetchall()
        # Если в запросе ничего не указано, выводим соответствующую надпись в статус баре
        else:
            self.statusBar().showMessage('Вы ничего не указали. Вывелся список всех олимпиад и их туров', 3000)
            # Так как ничего не указано, выводим список всех олимпиад и их туров
            result = cur.execute(f"""
                            SELECT DISTINCT Olimp.Олимпиада, Tours.number_tour, 
                            Tours.data_tour, Olimp.sites_tour
                            FROM Olimp, Tours ON Olimp.id = Tours.id_olymp
                            ORDER BY Olimp.Олимпиада""").fetchall()
        self.tableWidget.setRowCount(len(result))
        # Если результат запроса не нашёлся, выводим соответствующую надпись в статус баре
        if not result:
            self.statusBar().showMessage('Ничего не нашлось', 3000)
            return
        # Выводим данные в таблицу
        self.tableWidget.setColumnCount(len(result[0]))
        self.tableWidget.setHorizontalHeaderLabels(['Олимпиада', 'Номер тура', 'Дата', 'Сайт'])
        for i, elem in enumerate(result):
            for j, val in enumerate(elem):
                self.tableWidget.setItem(i, j, QTableWidgetItem(str(val)))

    def saveNotes(self):
        """Метод, который сохраняет новые заметки"""
        # Если текста в поле ввода запроса нет,
        # выводим соответствующую надпись в статус баре
        if self.lineNote.text() == '':
            self.statusBar().showMessage('Пустая заметка', 3000)
            return
        # Получаем текст из заметки
        text_note = self.lineNote.text()
        # Создаём экземпляр класса и выводим окно
        self.dt = WidDateTime(text_note)
        self.dt.exec()
        # Очищаем поле ввода и вызываем метод showNotes
        self.lineNote.clear()
        self.showNotes()

    def showNotes(self):
        """Метод, который будет отображать существующие заметки"""

        cur = self.con.cursor()
        # Удаляем все "просроченные" заметки, дата которых меньше сегодняшней даты
        cur.execute("DELETE FROM Events WHERE dates < date('now')")
        self.con.commit()
        # Выполняем запрос на добавление данных в таблицу
        result = cur.execute("SELECT DISTINCT text, dates, times "
                             "FROM Events ORDER by dates, times").fetchall()
        self.tableWidget_2.setRowCount(len(result))
        # Если заметок нет, выводим соответствующую надпись в статус баре
        if result == []:
            self.statusBar().showMessage('Ничего не нашлось', 3000)
            return
        # Выводим данные в таблицу
        self.tableWidget_2.setColumnCount(len(result[0]))
        self.tableWidget_2.setHorizontalHeaderLabels(['Название', 'Дата', 'Время'])
        for i, elem in enumerate(result):
            for j, val in enumerate(elem):
                self.tableWidget_2.setItem(i, j, QTableWidgetItem(str(val)))

    def delNotes(self):
        """Метод, с помощью которого будем удалять все выделенные пользователем заметки"""

        cur = self.con.cursor()
        # Получаем список элементов без повторов и их id
        rows = list(set([i.row() for i in self.tableWidget_2.selectedItems()]))
        # Если заметки, которые пользователь хочет удалить,
        # не выделены, выводим соответствующую надпись в статус баре
        if not rows:
            valid = QMessageBox.question(
                self, '', 'Вы не выделили заметки, которые хотите удалить.',
                QMessageBox.Yes, QMessageBox.No)
            return

        texts = [self.tableWidget_2.item(i, 0).text() for i in rows]
        ids = []
        # Выполняем запрос
        for text in texts:
            ids.append(str(cur.execute("""SELECT id FROM Events WHERE text = ?""",
                                       (text,)).fetchone()[0]))
        # Выводим окно, в котором задаём пользователю вопрос - удалять выбранные элементы или нет?
        valid = QMessageBox.question(
            self, '', "Вы действительно хотите удалить элементы с названиями "
                      + ", ".join(texts) + '?',
            QMessageBox.Yes, QMessageBox.No)
        # Если пользователь ответил утвердительно, удаляем элементы.
        # Сохраняем изменения
        if valid == QMessageBox.Yes:
            cur.execute("DELETE FROM Events WHERE id IN (" + ", ".join(
                '?' * len(ids)) + ")", ids)
            self.con.commit()
        # Вызываем метод showNotes
        self.showNotes()

    def addSite(self):
        """Метод, который добавляет новый сайт в бд и scrollarea"""

        # Получаем название и адрес сайта
        name, ok_pressed = QInputDialog.getText(self, "Введите название сайта",
                                                "Название сайта")
        if not ok_pressed:
            return

        site, ok_pressed = QInputDialog.getText(self, "Введите ссылку",
                                                'Ссылка')

        if not ok_pressed:
            return

        if not site.startswith('http'):
            site1 = 'http://' + site
            site2 = 'https://' + site
        else:
            site1 = site2 = site

        # Проверяем отвечает сайт или нет
        try:
            response = get(site1).status_code
            site = site1
        except:
            try:
                response = get(site2).status_code
                site = site2
            except:
                self.statusBar().showMessage('Сайт, который вы хотите добавить не отвечает', 3000)
                return

        k = len(self.sites)
        cur = self.con.cursor()
        # Создание и настройка pushbutton
        btn = QPushButton(self)
        btn.setText(f'{k + 1}) {name}')
        btn.clicked.connect(self.ViewWebSite)

        # Добавление сайта в бд, группу сайтов и scrollarea
        self.sites.append(name)
        cur.execute("""INSERT INTO Sites(title, site) VALUES(?, ?)""", (name, site)).fetchall()
        self.con.commit()
        c = cur.execute("""SELECT id FROM Sites WHERE title = ?""", (name,)).fetchone()[0]
        btn.setObjectName(f'site{c}')
        self.buttonGroupSites.addButton(btn, id=k)
        self.wid_sites.addWidget(btn)
        self.scrollArea.show()

    def delSite(self):
        """Метод, удаляющий сайт из бд и scrollarea"""

        # Получаем название сайта, который хотим удалить
        cur = self.con.cursor()
        name, ok_pressed = QInputDialog.getItem(
            self, "Выберите сайт", "Удалить",
            map(lambda x: x[0], cur.execute("""SELECT title FROM Sites""").fetchall()), -1, False)

        if not ok_pressed:
            return

        # Удаляем сайт из бд и группы кнопок
        cur.execute("""DELETE FROM Sites WHERE title = ?""", (name,)).fetchone()
        self.con.commit()
        i = self.sites.index(name)
        del self.sites[i]
        self.createGroupSites()
        # Создаем виджет для заполнения scrollarea
        self.wid_sites = WidSites(self.buttonGroupSites)
        self.scrollArea.setWidget(self.wid_sites)
        self.scrollArea.show()

    def ViewWebSite(self):
        """Метод, который создает окно со страницой сайта"""

        try:
            cur = self.con.cursor()
            name = self.sender().text()[3:]
            # Получаем адрес сайта по имени
            site = cur.execute("""SELECT site FROM Sites WHERE title = ?""", (name,)).fetchone()[0]
            # Делаем запрос к сайту
            response = get(site)
            # Создаем окно со страницой сайта
            self.web = QWebEngineView()
            self.web.setWindowTitle('Супер браузер')
            self.web.setWindowIcon(QIcon('images\icon.ico'))
            self.web.load(QUrl(site))
            self.web.show()
        except:
            self.statusBar().showMessage('Сайт не отвечает', 3000)

    def addProblem(self):
        """Метод, который добавляет изображение задачи в бд"""

        cur = self.con.cursor()

        # Диалог с выбором раздела физики
        section, ok_pressed = QInputDialog.getItem(
            self, "Выберите раздел физики", "Разделы",
            (map(lambda x: x[0],
                 cur.execute("""SELECT title FROM Classes""").fetchall())), -1, False)

        if not (ok_pressed and section):
            return

        key_section = cur.execute("""SELECT key FROM Classes WHERE title = ?""",
                                  (section,)).fetchone()[0]

        # Получаем путь к изображению задания
        fname = QFileDialog.getOpenFileName(
            self, 'Выбрать картинку с заданием', '',
            'Картинка (*.jpg);;Картинка (*.png);;Все файлы (*)')[0]

        if not fname:
            return

        # Добавляем задачу в бд
        cur.execute("""INSERT INTO Problems(adress, class) VALUES(?, ?)""",
                    (copy(fname, 'problems/'), key_section)).fetchall()
        self.con.commit()

        # Отображаем изображение с задачей
        pixmap = QPixmap(fname)
        self.imgProblem.setPixmap(pixmap)

    def delProblem(self):
        """Метод, который удаляет изображение задачи в бд"""

        cur = self.con.cursor()

        # Диалог с выбором раздела физики
        sections = map(lambda x: x[0], cur.execute("""SELECT title FROM Classes""").fetchall())
        section, ok_pressed = QInputDialog.getItem(
            self, "Выберите раздел физики", "Разделы",
            ('Все задачи', *sections), -1, False)

        if not (ok_pressed and section):
            return

        # Создание окна с задачами определенной темы
        self.widProblems = ViewProblems(section, 2)
        self.widProblems.exec()

    def getRandProblem(self):
        """Метод, который выводит случайную задачу"""

        cur = self.con.cursor()

        # Выбираем случайную задачу из бд
        fname = cur.execute("""SELECT adress 
                            FROM Problems
                            ORDER BY RANDOM() LIMIT 1""").fetchone()[0]

        # Отображаем изображение с задачей
        self.pixmap = QPixmap(fname)
        self.imgProblem.setPixmap(self.pixmap)

    def getProblems(self):
        """Метод, для выбора задач из бд по теме"""

        cur = self.con.cursor()

        # Диалог с выбором раздела физики
        sections = map(lambda x: x[0], cur.execute("""SELECT title FROM Classes""").fetchall())
        section, ok_pressed = QInputDialog.getItem(
            self, "Выберите раздел физики", "Разделы",
            ('Все задачи', *sections), -1, False)

        if not (ok_pressed and section):
            return

        # Создание окна с задачами определенной темы
        self.widProblems = ViewProblems(section, 1)
        self.widProblems.exec()


class WidSites(QWidget):
    def __init__(self, btnGroup):
        super(WidSites, self).__init__()
        self.init(btnGroup)

    def addWidget(self, btn):
        """Добавление кнопки в виджет"""
        self.lt.addWidget(btn)

    def init(self, btnGroup):
        """Заполнение виджета кнопками сайта"""
        self.lt = QVBoxLayout(self)
        for btn in btnGroup.buttons():
            self.lt.addWidget(btn)


class WidProblems(QWidget):
    def __init__(self, problems, mode):
        super(WidProblems, self).__init__()
        self.mode = mode
        self.init(problems)

    def init(self, problems):
        """Заполнение виджета изображениями задач"""
        self.lt = QVBoxLayout(self)
        for p in problems:
            if self.mode == 1:
                img = QLabel(self)
            elif self.mode == 2:
                img = Label(self, p[0])
            pixmap = QPixmap(p[0])
            img.setPixmap(pixmap)
            self.lt.addWidget(img)


class ViewProblems(QDialog, Ui_Dialog2):
    def __init__(self, section, mode):
        super(ViewProblems, self).__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon('images\problem.ico'))

        self.con = sqlite3.connect(OlympPhysics.BD)
        self.section = section
        self.mode = mode

        self.initUI()

    def initUI(self):

        cur = self.con.cursor()

        # Получение адресов задач из бд
        if self.section == 'Все задачи':
            problems = cur.execute("""SELECT adress FROM Problems""").fetchall()
        else:
            problems = cur.execute("""SELECT adress FROM Problems 
                WHERE class = (SELECT key FROM Classes WHERE title = ?)""",
                                   (self.section,)).fetchall()

        if self.mode == 1:
            self.setWindowTitle(self.section)
            self.labelSectionName.setText(self.section)
        elif self.mode == 2:
            self.setWindowTitle('Удаление задач')
            self.labelSectionName.setText('Щелкнете по задаче, которую хотите удалить')

        # Создание виджета для заполнения scrollarea
        self.wid_problems = WidProblems(problems, self.mode)

        # Добавление виджета в scrollarea
        self.scrollArea.setWidget(self.wid_problems)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.show()


class WidDateTime(QDialog, Ui_Dialog1):
    def __init__(self, text_note):
        super(WidDateTime, self).__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon(r'images\time.ico'))

        self.text_note = text_note
        self.con = sqlite3.connect(OlympPhysics.BD)

        self.pushButton.clicked.connect(self.getDateTime)

    def getDateTime(self):
        cur = self.con.cursor()
        # Воспроизводим выбор даты
        dataChoice = self.calendarWidget.selectedDate().getDate()
        # Если выбранный месяц меньше или равен 9, добавляем к нему ноль вначале
        if int(dataChoice[1]) <= 9:
            dataChoice = (dataChoice[0], "0" + str(dataChoice[1]), dataChoice[-1])
        # Если выбранный день меньше или равен 9, добавляем к нему ноль вначале
        if int(dataChoice[2]) <= 9:
            dataChoice = (dataChoice[0], str(dataChoice[1]), "0" + str(dataChoice[-1]))
        # Соединяем полученный ввод в одну целую строку
        dataChoice = "-".join(map(str, dataChoice))
        # Воспроизводим выбор времени
        timeChoice = self.timeEdit.time().hour(), self.timeEdit.time().minute()
        # Если выбранные минуты меньше или равны 9, добавляем к ним ноль вначале
        if int(timeChoice[1]) <= 9:
            timeChoice = (timeChoice[0], "0" + str(timeChoice[1]))
        # Соединяем полученный ввод в одну целую строку
        timeChoice = ":".join(map(str, timeChoice))
        # Выполняем запрос на передачу данных в базу данных и сохраняем изменения
        cur.execute("""INSERT INTO Events(text, dates, times) VALUES(?, ?, ?)""",
                    (self.text_note, dataChoice, timeChoice))
        self.con.commit()
        # Закрываем окно
        self.close()


class Label(QLabel):
    """Класс для вставки изображений задач с возможностью удаления по нажатию на картинку"""

    def __init__(self, wid, adress):
        super(Label, self).__init__(wid)
        self.adress = adress

    def mouseDoubleClickEvent(self, event):
        """Метод, выполняющий удаление задачи из бд и хранилища по нажатию"""

        valid = QMessageBox.question(
            self, '',
            "Вы действительно хотите удалить эту задачу ?",
            QMessageBox.Yes, QMessageBox.No)

        if valid == QMessageBox.No:
            return

        con = sqlite3.connect(OlympPhysics.BD)
        cur = con.cursor()

        # Удаление задачи из бд
        cur.execute("""DELETE FROM Problems WHERE adress = ?""", (self.adress,)).fetchone()
        con.commit()

        # Удаление задачи из папки
        path = os.path.join(os.path.abspath(os.path.dirname(__file__)), self.adress)
        os.remove(path)

        wnd.widProblems.close()


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    wnd = OlympPhysics()
    wnd.show()
    sys.excepthook = except_hook
    sys.exit(app.exec())
