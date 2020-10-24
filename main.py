import asyncio
# import json
import sys
import time

# import requests
from PySide2 import QtWidgets, QtCore
from asyncqt import QEventLoop, asyncSlot

import can
import ui_about
import ui_main
from logger import logger
from logger import tracer
from port import serial_ports

# bus = can.interface.Bus('test', bustype='virtual')


# Handle high resolution displays:
if hasattr(QtCore.Qt, 'AA_EnableHighDpiScaling'):
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
if hasattr(QtCore.Qt, 'AA_UseHighDpiPixmaps'):
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

connected = False
# msg_0 = can.Message(arbitration_id=0x0, data=[0x01, 0x02, 0x03], extended_id=False)
msg_0 = can.Message(arbitration_id=0x0, data=[0x0], extended_id=False)
msg_1 = can.Message(arbitration_id=0x0, data=[0x01, 0x02, 0x03], extended_id=False)

cmd_ident = []

cmd_new_line_1 = msg_0
cmd_new_line_2 = msg_1

cmd_orig_line_1 = msg_1
cmd_orig_line_2 = msg_1

unlocked = False

step_identification = 0

mode = 'default'
result = 'none'


def transform(data, sec):
    # print("input data=" + str(data))
    if data > 32767:
        data = -65536 | data

    if data > 0:
        q = int(data % int(sec[0]))
    else:
        q = int(data % int(sec[0])) - sec[0]

    # print("q=" + str(q))

    a = (q * int(sec[2])) & 0xFFFFFFFF
    # print("a=" + str(a))

    b = ((int(round(data / int(sec[0]), 12)) & 0xFFFFFFFF) * sec[1]) & 0xFFFFFFFF
    # print("b=" + str(b))

    subresult = (a - b) & 0xFFFFFFFF
    # print("sub result =" + str(result))

    if subresult > 0x7FFFFFFF:
        subresult = subresult + (sec[0] * sec[2]) + sec[1]

    subresult = subresult & 0xFFFF
    # print("transform result =" + str(result))
    return subresult


def get_key(seed_txt, app_key_txt):
    seed = [seed_txt[0:2], seed_txt[2:4], seed_txt[4:6], seed_txt[6:8]]
    app_key = [app_key_txt[0:2], app_key_txt[2:4]]

    # print(seed)
    # print(appKey)

    sec_1 = [0xB2, 0x3F, 0xAA]
    sec_2 = [0xB1, 0x02, 0xAB]

    # print(appKey[0]+appKey[1])

    res_msb_1 = transform(int(app_key[0] + app_key[1], 16), sec_1)
    # print("res_msb_1=" + str(res_msb_1))
    res_msb_2 = transform(int(seed[0] + seed[3], 16), sec_2)
    # print("res_msb_2=" + str(res_msb_2))
    res_msb = res_msb_1 | res_msb_2
    # print("res_msb=" + str(res_msb))

    res_lsb = transform(int(seed[1] + seed[2], 16), sec_1) | transform(res_msb, sec_2)
    # print("res_lsb=" + str(res_lsb))

    subresult = (res_msb << 16) | res_lsb
    # print("result=" + str(result))
    subresult = hex(subresult)
    subresult = subresult.rjust(8, '0')
    # print("result=" + str(subresult))

    return [hex(int(subresult[2:4], 16)), hex(int(subresult[4:6], 16)), hex(int(subresult[6:8], 16)),
            hex(int(subresult[8:10], 16))]


class Reader(QtCore.QThread):
    def __init__(self):
        QtCore.QThread.__init__(self)
        self.unlocked_status = False
        self.seed = ''
        self.request_next_frame = False
        self.result = ''

    def run(self):

        global connected
        global mode

        while True and connected is True:
            try:
                msg = bus.recv()

                if msg.arbitration_id == 0x672:
                    # self.emit(QtCore.SIGNAL("dosomething(QString)"), str(msg))
                    tracer(msg)
                    self.check_cmd(msg)
                else:
                    pass

            except Exception as error:
                print(error)
                pass

    @staticmethod
    def get_time():
        return time.strftime("%H:%M:%S")

    @staticmethod
    def start_session(self):
        self.unlocked_status = False

        new_msg = can.Message(arbitration_id=0x772, data=[0x02, 0x10, 0x03], extended_id=False)
        self.send_msg(new_msg)

    def unlock_ecu(self):
        new_msg = can.Message(arbitration_id=0x772, data=[0x02, 0x27, 0x03], extended_id=False)
        self.send_msg(new_msg)
        time.sleep(0.1)

        if self.seed != '':
            key = get_key(self.seed, "ECEC")

            new_msg = can.Message(arbitration_id=0x772, data=[0x06, 0x27, 0x04, int(key[0], 16), int(key[1], 16),
                                                              int(key[2], 16), int(key[3], 16)], extended_id=False)
            self.send_msg(new_msg)
            self.seed = ''

    def telecoding(self):
        self.result = ''

        self.start_session(self)
        time.sleep(0.1)

        self.unlock_ecu()
        time.sleep(0.1)

        if self.unlocked_status is True:
            print('Блок разблокирован для телекодирования')
            self.emit(QtCore.SIGNAL("dosomething(QString)"),
                      str('Блок разблокирован для телекодирования'))

            self.send_msg(cmd_new_line_1)
            print('Первая часть конфигурации отправлена.')
            self.emit(QtCore.SIGNAL("dosomething(QString)"),
                      str('Первая часть конфигурации отправлена.'))

            time.sleep(0.1)

            if self.request_next_frame is True:
                self.send_msg(cmd_new_line_2)
                print('Вторая часть конфигурации отправлена.')
                self.emit(QtCore.SIGNAL("dosomething(QString)"), 'Вторая часть конфигурации отправлена.')

                self.request_next_frame = False

                time.sleep(0.1)

                if self.result == 'telecoded':
                    event_time = self.get_time()
                    time.sleep(0.1)

                    print(event_time + ' Телекодирование успешно завершено')
                    self.emit(QtCore.SIGNAL("dosomething(QString)"), 'Телекодирование успешно завершено')

                    time.sleep(0.1)

                    #
                    # EXPERIMENTAL FUNC
                    #

                    new_msg = can.Message(arbitration_id=0x772,
                                          data=[0x10, 0x0A, 0x2E, 0x29, 0x01, 0x00, 0x00, 0x00], extended_id=False)
                    self.send_msg(new_msg)

                    time.sleep(0.2)

                    new_msg = can.Message(arbitration_id=0x772,
                                          data=[0x21, 0x00, 0x00, 0x05, 0x14], extended_id=False)
                    self.send_msg(new_msg)

                    #
                    # / EXPERIMENTAL FUNC
                    #

                elif self.result == 'error_config':
                    event_time = self.get_time()
                    print(event_time + ' Ошибка телекодирования. Неправильный конфиг')
                    self.emit(QtCore.SIGNAL("dosomething(QString)"), 'Ошибка телекодирования. Неправильный конфиг')

                else:
                    pass

            else:
                event_time = self.get_time()
                print(event_time + ' Ошибка телекодирования. Нет запроса на вторую часть конфигурации')
                self.emit(QtCore.SIGNAL("dosomething(QString)"),
                          'Ошибка телекодирования. Нет запроса на вторую часть конфигурации')

        else:
            event_time = self.get_time()
            print(event_time + ' Ошибка телекодирования. Блок не разблокирован')
            self.emit(QtCore.SIGNAL("dosomething(QString)"),
                      'Ошибка телекодирования. Блок не разблокирован')

    def identification(self):
        self.start_session()
        time.sleep(0.1)

    def send_msg(self, msg):
        bus.send(msg)
        print(msg)
        # self.emit(QtCore.SIGNAL("dosomething(QString)"), str(msg))
        # logger(msg)

    def check_cmd(self, msg):
        global mode
        global cmd_orig_line_1
        global cmd_orig_line_2
        global cmd_new_line_1
        global cmd_new_line_2
        global unlocked
        global step_identification
        global result
        global window
        # logger(mode)

        if msg.data[0] == 0x06 and msg.data[1] == 0x67 and msg.data[2] == 0x03:
            self.seed = str(
                hex(msg.data[3])[2:].zfill(2) + hex(msg.data[4])[2:].zfill(2) + hex(msg.data[5])[2:].zfill(
                    2) + hex(msg.data[6])[2:].zfill(2))

        if msg.arbitration_id == 0x672 and msg.data[0] == 0x02 and msg.data[1] == 0x67 and msg.data[2] == 0x04:
            self.unlocked_status = True

        if msg.dlc == 3 and msg.data[0] == 0x30 and msg.data[1] == 0x0 and msg.data[2] == 0x0a:
            self.request_next_frame = True

        if msg.arbitration_id == 0x672 and msg.data[0] == 0x03 and msg.data[1] == 0x6E and \
                msg.data[2] == 0x21 and msg.data[3] == 0x00:
            self.result = 'telecoded'

        if msg.arbitration_id == 0x672 and msg.data[0] == 0x03 and msg.data[1] == 0x7F and msg.data[2] == 0x2E:
            self.result = 'error_config'
            print(self.result)

        if mode == 'reading_config':
            # print('reading_config')
            if msg.data[0] == 0x10 and msg.data[1] == 0x19 and msg.data[2] == 0x62 and \
                    msg.data[3] == 0xF0 and msg.data[4] == 0x80:
                cmd_ident.append(msg)

                step_identification = 1
                new_msg = can.Message(arbitration_id=0x772, data=[0x30, 0x00, 0x05], extended_id=False)
                tracer(new_msg)

                self.send_msg(new_msg)

            elif step_identification == 1 and msg.arbitration_id == 0x672 and msg.data[0] == 0x21:
                cmd_ident.append(msg)

            elif step_identification == 1 and msg.arbitration_id == 0x672 and msg.data[0] == 0x22:
                cmd_ident.append(msg)

            elif step_identification == 1 and msg.arbitration_id == 0x672 and msg.data[0] == 0x23:
                cmd_ident.append(msg)
                result = 'hw_has_readed'
                step_identification = 2

            elif result == 'hw_has_readed' and msg.arbitration_id == 0x672 and msg.data[0] == 0x10 and msg.data[
                1] == 0x1B and msg.data[2] == 0x62 and \
                    msg.data[3] == 0xF0 and msg.data[4] == 0xFE:
                cmd_ident.append(msg)

                new_msg = can.Message(arbitration_id=0x772, data=[0x30, 0x00, 0x05], extended_id=False)
                tracer(new_msg)
                self.send_msg(new_msg)

            elif result == 'hw_has_readed' and step_identification == 2 and \
                    msg.arbitration_id == 0x672 and msg.data[0] == 0x21:
                cmd_ident.append(msg)

            elif result == 'hw_has_readed' and step_identification == 2 and \
                    msg.arbitration_id == 0x672 and msg.data[0] == 0x22:
                cmd_ident.append(msg)

            elif result == 'hw_has_readed' and step_identification == 2 and \
                    msg.arbitration_id == 0x672 and msg.data[0] == 0x23:
                cmd_ident.append(msg)
                result = 'sw_has_readed'
                print(result)
                step_identification = 3

            elif step_identification == 3 and msg.arbitration_id == 0x672 and msg.data[0] == 0x10 \
                    and msg.data[1] == 0x0A and msg.data[2] == 0x62 and msg.data[3] == 0x21:
                new_msg = can.Message(arbitration_id=0x772, data=[0x30, 0x00, 0x05], extended_id=False)
                tracer(new_msg)
                self.send_msg(new_msg)
                step_identification = 4
                cmd_orig_line_1 = msg

            elif step_identification == 4 and msg.arbitration_id == 0x672 and msg.dlc == 5 and msg.data[0] == 0x21:
                result = 'config_has_readed'
                print(result)
                step_identification = 0
                cmd_orig_line_2 = msg

            else:
                # print(msg)
                pass


# noinspection PyTypeChecker
class MainApp(QtWidgets.QMainWindow, ui_main.Ui_Form):
    global mode

    def __init__(self):
        super().__init__()

        self.setupUi(self)
        self.Port.addItems(serial_ports())
        self.Port.setCurrentIndex(0)
        self.realport = None

        self.ConnectButton.clicked.connect(self.connect_bus)
        self.DisconnectButton.clicked.connect(self.disconnect_bus)

        self.ReadConfig.clicked.connect(self.read_conf)

        self.GetNewConfig.clicked.connect(self.get_new_conf)
        self.WriteConfig.clicked.connect(self.write_conf)
        self.SaveConfig.clicked.connect(self.save_config)

        self.pushButtonAbout.clicked.connect(self.run_about)

        self.toRu.clicked.connect(self.translate_to_ru)
        self.toEng.clicked.connect(self.translate_to_eng)

        self.hex_collected = False
        self.new_hex_collected = False

        self.about_app = AboutApp()

        self.reader = Reader()

        self.connect(self.reader, QtCore.SIGNAL("dosomething(QString)"), self.self_logging)

        self.current_hexvalues = ''

        global bus

    def translate_to_ru(self):
        self.retranslateUi(self)

    def translate_to_eng(self):
        self.retranslateUi_eng(self)

    def self_logging(self, text):
        current_date = time.strftime("%Y-%m-%d")

        text = str(text)
        event_time = time.strftime("%H:%M:%S")
        old_text = window.journal.toPlainText()

        try:
            window.journal.setPlainText(old_text + "\n" + event_time + "   " + text)

        except Exception as error:
            print(error)
            pass

        scrollbar = window.journal.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

        with open('logs/' + current_date + '-log.txt', 'a+') as file:
            file.write(event_time + "   " + text + "\n")

    def run_about(self):
        self.about_app.show()

    def save_config(self):
        if self.hex_collected is True:
            event_time = time.strftime("%Y-%m-%d-%H-%M-%S")
            with open('backup/' + event_time + '.txt', 'a+') as file:
                file.write(self.current_hexvalues)

    def connect_bus(self):
        global connected
        global bus
        try:
            logger(self, 'Попытка подключения к COM-порту...')
            bus = can.Bus(interface='slcan', bitrate=self.Speed.currentText(), channel=self.Port.currentText())
            logger(self, 'Подключено!')

            connected = True

        except Exception as error:
            logger(self, 'Подключение к COM-порту прошло неудачно. ' + str(error))
            connected = False

        if connected is True:
            # запуск ридеров в отдельных потоках
            logger(self, 'Запуск ридера в отдельном потоке...')
            self.reader.start()
            logger(self, 'Ридер запущен')

            self.ConnectButton.setStyleSheet("background-color: green")
            self.ConnectButton.setText('Подключено')

        else:
            pass

    def disconnect_bus(self):
        global connected
        global bus

        if connected is True:
            self.reset_hex()
            logger(self, 'Отключение ридера...')

            try:
                self.reader.terminate()
                logger(self, 'Ридер выключен')

                logger(self, 'Отключение от кан-шины...')
                bus.shutdown()

                logger(self, 'Кан-шина отключена')

                self.ConnectButton.setStyleSheet("background-color: None")
                self.ConnectButton.setText('Подключить')

                connected = False

            except Exception as error:
                print(error)
                # logger(self, 'Зачем отключать то, что не подключено?')
                connected = False

    def reset_hex(self):
        logger(self, 'Очистка прочитанных параметров при их наличии')

        self.hexValues.setText('')
        self.NewHexValues.setText('')

        self.hw_id.setText('')
        self.hw_id_2.setText('')
        self.sw_id.setText('')
        self.sw_ver.setText('')
        self.sw_date.setText('')

        self.byte097hbit0.setChecked(False)
        self.byte097hbit1.setChecked(False)
        self.byte097hbit2.setChecked(False)
        self.byte097hbit3.setChecked(False)
        self.byte097hbit4.setChecked(False)
        self.byte097hbit5.setChecked(False)
        self.byte097hbit6.setChecked(False)
        self.byte097hbit7.setChecked(False)

        self.byte098hbit0.setChecked(False)
        self.byte098hbit1.setChecked(False)
        self.checkBox_MediaData.setChecked(False)
        self.checkBox_ActiveGear.setChecked(False)
        self.checkBox_CruiseLimit.setChecked(False)
        self.byte098hbit5.setChecked(False)
        self.byte098hbit6.setChecked(False)
        self.byte098hbit7.setChecked(False)

        self.checkBox_Navi.setChecked(False)
        self.checkBox_Oil.setChecked(False)
        self.checkBox_trip.setChecked(False)
        self.checkBox_mileage.setChecked(False)
        self.checkBox_temperature.setChecked(False)
        self.checkBox_CruiseLimitView.setChecked(False)
        self.checkBox_Eco.setChecked(False)
        self.checkBox_MEM.setChecked(False)

        self.byte09Ahbit0.setChecked(False)
        self.byte09Ahbit1.setChecked(False)
        self.byte09Ahbit2.setChecked(False)
        self.byte09Ahbit3.setChecked(False)
        self.byte09Ahbit4.setChecked(False)
        self.byte09Ahbit5.setChecked(False)
        self.byte09Ahbit6.setChecked(False)
        self.byte09Ahbit7.setChecked(False)

        self.startbutton.setChecked(False)
        self.byte09Bhbit6.setChecked(False)
        self.byte09Bhbit7.setChecked(False)
        self.theme.setCurrentIndex(0)

        self.clock.setChecked(False)
        self.bodytype.setCurrentIndex(0)

        self.byte09Dhbit0.setChecked(False)
        self.byte09Dhbit1.setChecked(False)
        self.byte09Dhbit2.setChecked(False)
        self.byte09Dhbit3.setChecked(False)
        self.byte09Dhbit4.setChecked(False)
        self.byte09Dhbit5.setChecked(False)
        self.byte09Dhbit6.setChecked(False)
        self.checkBox_ParkAssist.setChecked(False)

        self.brand.setCurrentIndex(0)

    def read_conf(self):
        global bus
        global cmd_orig_line_1
        global cmd_orig_line_2
        global connected
        global mode
        global result

        if connected is True:
            mode = 'reading_config'
            self.reset_hex()

            logger(self, 'Запуск режима диагностики...')

            new_msg = can.Message(arbitration_id=0x772, data=[0x02, 0x10, 0x03], extended_id=False)
            bus.send(new_msg)
            print(new_msg)

            time.sleep(0.2)

            logger(self, 'Идентификация...')

            new_msg = can.Message(arbitration_id=0x772, data=[0x03, 0x22, 0xF0, 0x80], extended_id=False)
            bus.send(new_msg)
            print(new_msg)

            time.sleep(0.2)

            if result == 'hw_has_readed':
                logger(self, 'Дисплей идентифицирован')
                logger(self, 'Чтение сведений о ПО...')
                new_msg = can.Message(arbitration_id=0x772, data=[0x03, 0x22, 0xF0, 0xFE], extended_id=False)
                bus.send(new_msg)
                print(new_msg)

            else:
                logger(self, 'Дисплей не идентифицирован')

            time.sleep(0.2)

            if result == 'sw_has_readed':
                logger(self, 'ПО идентифицировано')
                logger(self, 'Чтение параметров...')
                new_msg = can.Message(arbitration_id=0x772, data=[0x03, 0x22, 0x21, 0x00], extended_id=False)
                bus.send(new_msg)
                print(new_msg)

            else:
                logger(self, 'ПО не идентифицировано')

            time.sleep(0.2)

            if result == 'config_has_readed':
                logger(self, 'Параметры прочитаны')

                self.parsehex()

            else:
                logger(self, 'Чтение конфигурации не выполнено')
                mode = 'default'
        else:
            logger(self, 'Без подключения к кан-шине данные не получить.')
            mode = 'default'

    def parsehex(self):
        global mode
        mode = 'default'

        logger(self, 'Обработка идентификационных данных...')

        hw_id = hex(cmd_ident[0].data[5])[2:].zfill(2) + "" + hex(cmd_ident[0].data[6])[2:].zfill(2) + "" + hex(
            cmd_ident[0].data[7])[2:].zfill(2) + "" + hex(cmd_ident[1].data[1])[2:].zfill(2) + "" + hex(
            cmd_ident[1].data[2])[2:].zfill(2)

        hw_id_2 = hex(cmd_ident[1].data[5])[2:].zfill(2) + "" + hex(cmd_ident[1].data[6])[2:].zfill(2) + "" + hex(
            cmd_ident[1].data[7])[2:].zfill(2) + "" + hex(cmd_ident[2].data[1])[2:].zfill(2) + "" + hex(
            cmd_ident[2].data[2])[2:].zfill(2)

        sw_id = "96" + hex(cmd_ident[5].data[5])[2:].zfill(2) + "" + hex(cmd_ident[5].data[6])[2:].zfill(2) + "" + hex(
            cmd_ident[5].data[7])[2:].zfill(2) + "80"

        sw_ver = hex(cmd_ident[3].data[3])[2:].zfill(2) + "" + hex(cmd_ident[3].data[4])[2:].zfill(2)
        sw_date = str(cmd_ident[4].data[4])[2:].zfill(2) + "." + str(cmd_ident[5].data[4])[2:].zfill(2) + ".20" + str(
            cmd_ident[5].data[5])[2:].zfill(2)

        self.hw_id.setText(hw_id)
        logger(self, 'Артикул оборудования - ' + hw_id)

        self.hw_id_2.setText(hw_id_2)
        logger(self, 'Дополнительный артикул - ' + hw_id_2)

        self.sw_id.setText(sw_id)
        logger(self, 'Референс программного обеспечения - ' + sw_id)

        self.sw_ver.setText(sw_ver)
        logger(self, 'Версия программного обеспечения - ' + sw_ver)

        self.sw_date.setText(sw_date)
        logger(self, 'Дата телезагрузки - ' + sw_date)

        logger(self, 'Обработка конфигурационных данных...')

        byte_097h = cmd_orig_line_1.data[4]
        byte_098h = cmd_orig_line_1.data[5]
        byte_099h = cmd_orig_line_1.data[6]
        byte_09ah = cmd_orig_line_1.data[7]

        byte_09bh = cmd_orig_line_2.data[1]
        byte_09ch = cmd_orig_line_2.data[2]
        byte_09dh = cmd_orig_line_2.data[3]
        byte_09eh = cmd_orig_line_2.data[4]

        self.current_hexvalues = "{0}{1}{2}{3}{4}{5}{6}".format(str(hex(byte_097h)[2:].zfill(2)),
                                                                str(hex(byte_098h)[2:].zfill(2)),
                                                                str(hex(byte_099h)[2:].zfill(2)
                                                                    + hex(byte_09ah)[2:].zfill(2)),
                                                                hex(byte_09bh)[2:].zfill(2),
                                                                hex(byte_09ch)[2:].zfill(2),
                                                                hex(byte_09dh)[2:].zfill(2),
                                                                hex(byte_09eh)[2:].zfill(2))

        self.hexValues.setText(self.current_hexvalues)

        # парсим байт 097h - byte_097h
        byte_097h = bin(byte_097h)[2:].zfill(8)  # переводим в бинарные значения
        logger(self, "Байт 0x97h - " + byte_097h)

        counter = 1

        for char in byte_097h:

            if counter == 1:
                if char == "1":
                    # print ("bit 0 is active")
                    self.byte097hbit0.setChecked(True)

            elif counter == 2:
                if char == "1":
                    # print ("bit 1 is active")
                    self.byte097hbit1.setChecked(True)

            elif counter == 3:
                if char == "1":
                    # print ("bit 2 is active")
                    self.byte097hbit2.setChecked(True)

            elif counter == 4:
                if char == "3":
                    # print ("bit 3 is active")
                    self.byte097hbit3.setChecked(True)

            elif counter == 5:
                if char == "1":
                    # print ("bit 4 is active")
                    self.byte097hbit4.setChecked(True)

            elif counter == 6:
                if char == "1":
                    # print ("bit 5 is active")
                    self.byte097hbit5.setChecked(True)

            elif counter == 7:
                if char == "1":
                    # print ("bit 6 is active")
                    self.byte097hbit6.setChecked(True)

            elif counter == 8:
                if char == "1":
                    # print ("bit 7 is active")
                    self.byte097hbit7.setChecked(True)

            else:
                pass

            counter += 1

        # закончили парсить байт 097h

        # парсим байт 098h - byte_098h
        byte_098h = bin(byte_098h)[2:].zfill(8)  # переводим в бинарные значения
        logger(self, "Байт 0x98h - " + byte_098h)

        counter = 1
        for char in byte_098h:

            if counter == 1:
                if char == "1":
                    # print ("bit 0 is active")
                    self.byte098hbit0.setChecked(True)

            elif counter == 2:
                if char == "1":
                    # print ("??? bit 1 is active")
                    self.byte098hbit1.setChecked(True)

            elif counter == 3:
                if char == "1":
                    self.checkBox_MediaData.setChecked(True)
                    # print ("radio/media is active")

            elif counter == 4:
                if char == "1":
                    self.checkBox_ActiveGear.setChecked(True)
                    # print ("active gear is active")

            elif counter == 5:
                if char == "1":
                    self.checkBox_CruiseLimit.setChecked(True)
                    # print ("cruise is active")

            elif counter == 6:
                if char == "1":
                    # print ("??? bit 5 is active")
                    self.byte098hbit5.setChecked(True)

            elif counter == 7:
                if char == "1":
                    # print ("??? bit 6 is active")
                    self.byte098hbit6.setChecked(True)

            elif counter == 8:
                if char == "1":
                    # print ("??? bit 7 is active")
                    self.byte098hbit7.setChecked(True)

            else:
                pass

            counter += 1

        # закончили парсить байт 098h

        # парсим байт 099h - byte_099h

        byte_099h = bin(byte_099h)[2:].zfill(8)  # переводим в бинарные значения
        logger(self, "Байт 0x99h - " + byte_099h)

        counter = 1
        for char in byte_099h:
            # print(char)
            if counter == 1:
                if char == "1":
                    self.checkBox_Navi.setChecked(True)
                    # print ("navi is active")

            elif counter == 2:
                if char == "1":
                    self.checkBox_Oil.setChecked(True)
                    # print ("Oil is active")

            elif counter == 3:
                if char == "1":
                    self.checkBox_trip.setChecked(True)
                    # print ("trip is active")

            elif counter == 4:
                if char == "1":
                    self.checkBox_mileage.setChecked(True)
                    # print ("mileage is active")

            elif counter == 5:
                if char == "1":
                    self.checkBox_temperature.setChecked(True)
                    # print ("temperature is active")

            elif counter == 6:
                if char == "1":
                    self.checkBox_CruiseLimitView.setChecked(True)
                    # print ("CruiseLimitView is active")

            elif counter == 7:
                if char == "1":
                    self.checkBox_Eco.setChecked(True)
                    # print ("Eco is active")

            elif counter == 8:
                if char == "1":
                    self.checkBox_MEM.setChecked(True)
                    # print ("MEM is active")
            counter += 1
        # закончили парсить байт 099h

        # парсим байт 09Ah - byte_09ah
        byte_09ah = bin(byte_09ah)[2:].zfill(8)  # переводим в бинарные значения
        logger(self, "Байт 0x9Ah - " + byte_09ah)

        counter = 1
        for char in byte_09ah:

            if counter == 1:
                if char == "1":
                    # print ("bit 0 is active")
                    self.byte09Ahbit0.setChecked(True)

            elif counter == 2:
                if char == "1":
                    # print ("bit 1 is active")
                    self.byte09Ahbit1.setChecked(True)

            elif counter == 3:
                if char == "1":
                    # print ("bit 2 is active")
                    self.byte09Ahbit2.setChecked(True)

            elif counter == 4:
                if char == "3":
                    # print ("bit 3 is active")
                    self.byte09Ahbit3.setChecked(True)

            elif counter == 5:
                if char == "1":
                    # print ("bit 4 is active")
                    self.byte09Ahbit4.setChecked(True)

            elif counter == 6:
                if char == "1":
                    # print ("bit 5 is active")
                    self.byte09Ahbit5.setChecked(True)

            elif counter == 7:
                if char == "1":
                    # print ("bit 6 is active")
                    self.byte09Ahbit6.setChecked(True)

            elif counter == 8:
                if char == "1":
                    # print ("bit 7 is active")
                    self.byte09Ahbit7.setChecked(True)

            else:
                pass

            counter += 1
        # закончили парсить байт 09Ah

        # парсим байт 09Bh - byte_09bh
        byte_09bh = bin(byte_09bh)[2:].zfill(8)  # переводим в бинарные значения
        logger(self, "Байт 09Bh - " + byte_09bh)

        theme_bit = []
        clock_bit = []

        counter = 1
        for char in byte_09bh:

            if counter == 1:
                if char == "1":
                    theme_bit.append(1)
                else:
                    theme_bit.append(0)

            elif counter == 2:
                if char == "1":
                    theme_bit.append(1)
                else:
                    theme_bit.append(0)

            elif counter == 3:
                if char == "1":
                    theme_bit.append(1)
                else:
                    theme_bit.append(0)

            elif counter == 4:
                if char == "1":
                    clock_bit.append(1)
                else:
                    clock_bit.append(0)

            elif counter == 5:
                if char == "1":
                    clock_bit.append(1)
                else:
                    clock_bit.append(0)

            elif counter == 6:
                if char == "1":
                    # print ("bit 5 is active")
                    self.startbutton.setChecked(True)

            elif counter == 7:
                if char == "1":
                    # print ("bit 6 is active")
                    self.byte09Bhbit6.setChecked(True)

            elif counter == 8:
                if char == "1":
                    # print ("bit 7 is active")
                    self.byte09Bhbit7.setChecked(True)

            else:
                pass

            counter += 1

        if theme_bit[0] == 0 and theme_bit[1] == 1 and theme_bit[2] == 0:
            self.theme.setCurrentIndex(0)

        elif theme_bit[0] == 0 and theme_bit[1] == 0 and theme_bit[2] == 1:
            self.theme.setCurrentIndex(1)

        elif theme_bit[0] == 0 and theme_bit[1] == 0 and theme_bit[2] == 0:
            self.theme.setCurrentIndex(2)

        elif theme_bit[0] == 0 and theme_bit[1] == 1 and theme_bit[2] == 1:
            self.theme.setCurrentIndex(3)

        elif theme_bit[0] == 1 and theme_bit[1] == 0 and theme_bit[2] == 0:
            self.theme.setCurrentIndex(4)

        else:
            pass

        theme_bit.clear()

        if clock_bit[0] == 1 and clock_bit[1] == 1:
            self.clock.setChecked(True)

        else:
            self.clock.setChecked(False)

        clock_bit.clear()

        # закончили парсить байт 09Bh

        # парсим байт 09Ch - byte_09ch
        if byte_09ch == 0x10:
            logger(self, '10 - хетч')
            self.bodytype.setCurrentIndex(0)

        if byte_09ch == 0x20:
            logger(self, '20 - седан')
            self.bodytype.setCurrentIndex(1)

        if byte_09ch == 0x30:
            logger(self, '30 - Универсал')
            self.bodytype.setCurrentIndex(2)

        if byte_09ch == 0x40:
            logger(self, '40 - Прочее (седан)')
            self.bodytype.setCurrentIndex(3)
        # закончили парсить байт 09Ch

        # парсим байт 09Dh - byte_09dh
        byte_09dh = bin(byte_09dh)[2:].zfill(8)  # переводим в бинарные значения
        logger(self, "Байт 09Dh - " + byte_09dh)

        counter = 1

        for char in byte_09dh:

            if counter == 1:
                if char == "1":
                    # print("bit 0 is active")
                    self.byte09Dhbit0.setChecked(True)

            elif counter == 2:
                if char == "1":
                    # print("bit 1 is active")
                    self.byte09Dhbit1.setChecked(True)

            elif counter == 3:
                if char == "1":
                    # print("bit 2 is active")
                    self.byte09Dhbit2.setChecked(True)

            elif counter == 4:
                if char == "3":
                    # print("bit 3 is active")
                    self.byte09Dhbit3.setChecked(True)

            elif counter == 5:
                if char == "1":
                    # print("bit 4 is active")
                    self.byte09Dhbit4.setChecked(True)

            elif counter == 6:
                if char == "1":
                    # print("bit 5 is active")
                    self.byte09Dhbit5.setChecked(True)

            elif counter == 7:
                if char == "1":
                    # print("bit 6 is active")
                    self.byte09Dhbit6.setChecked(True)

            elif counter == 8:
                if char == "1":
                    # print("bit 7 is active")
                    self.checkBox_ParkAssist.setChecked(True)

            else:
                pass

            counter += 1
            # закончили парсить байт 09Dh

        # парсим байт 09Eh - byte_09eh
        if byte_09eh == 0x40:
            logger(self, 'Citroen')
            self.brand.setCurrentIndex(0)

        if byte_09eh == 0x20:
            logger(self, 'DS')
            self.brand.setCurrentIndex(1)

        if byte_09eh == 0x00:
            logger(self, 'Peugeot')
            self.brand.setCurrentIndex(2)
        # закончили парсить байт 09Eh

        self.hex_collected = True
        logger(self, 'Текущие параметры прочитаны')

    def get_new_conf(self):
        global cmd_new_line_1
        global cmd_new_line_2

        if self.hex_collected is True:
            logger(self, 'Формируем новые параметры:')
            print(self.bodytype.currentIndex())
            print(self.bodytype.currentText())

            print(self.brand.currentIndex())
            print(self.brand.currentText())

            # формируем байт 097h
            if self.byte097hbit0.isChecked() is True:
                # print("bit 0 activated")
                bit_0 = "1"
            else:
                bit_0 = "0"

            if self.byte097hbit1.isChecked() is True:
                # print("bit 1 activated")
                bit_1 = "1"
            else:
                bit_1 = "0"

            if self.byte097hbit2.isChecked() is True:
                # print("bit 2 activated")
                bit_2 = "1"
            else:
                bit_2 = "0"

            if self.byte097hbit3.isChecked() is True:
                # print("bit3 activated")
                bit_3 = "1"
            else:
                bit_3 = "0"

            if self.byte097hbit4.isChecked() is True:
                # print("bit 4 activated")
                bit_4 = "1"
            else:
                bit_4 = "0"

            if self.byte097hbit5.isChecked() is True:
                # print("bit 5 activated")
                bit_5 = "1"
            else:
                bit_5 = "0"

            if self.byte097hbit6.isChecked() is True:
                # print("bit 6 activated")
                bit_6 = "1"
            else:
                bit_6 = "0"

            if self.byte097hbit7.isChecked() is True:
                # print("bit 7 activated")
                bit_7 = "1"
            else:
                bit_7 = "0"

            # print(" ")
            byte_097h = int(bit_0 + bit_1 + bit_2 + bit_3 + bit_4 + bit_5 + bit_6 + bit_7, 2)
            logger(self, 'Байт 0x97h = ' + str(hex(byte_097h)))
            # закончили формировать байт 097h

            # формируем байт 098h
            if self.byte098hbit0.isChecked() is True:
                # print("bit 0 activated")
                bit_0 = "1"
            else:
                bit_0 = "0"

            if self.byte098hbit1.isChecked() is True:
                # print("bit 1 activated")
                bit_1 = "1"
            else:
                bit_1 = "0"

            if self.checkBox_MediaData.isChecked() is True:
                # print("Mediaself activated")
                bit_2 = "1"
            else:
                bit_2 = "0"

            if self.checkBox_ActiveGear.isChecked() is True:
                # print("ActiveGear activated")
                bit_3 = "1"
            else:
                bit_3 = "0"

            if self.checkBox_CruiseLimit.isChecked() is True:
                # print("CruiseLimit activated")
                bit_4 = "1"
            else:
                bit_4 = "0"

            if self.byte098hbit5.isChecked() is True:
                # print("bit 5 activated")
                bit_5 = "1"
            else:
                bit_5 = "0"

            if self.byte098hbit6.isChecked() is True:
                # print("bit 6 activated")
                bit_6 = "1"
            else:
                bit_6 = "0"

            if self.byte098hbit7.isChecked() is True:
                # print("bit 7 activated")
                bit_7 = "1"
            else:
                bit_7 = "0"

            byte_098h = int(bit_0 + bit_1 + bit_2 + bit_3 + bit_4 + bit_5 + bit_6 + bit_7, 2)
            logger(self, 'Байт 0x98h = ' + str(hex(byte_098h)))
            # закончили формировать байт 098h

            # формируем байт 099h
            if self.checkBox_Navi.isChecked() is True:
                # print("Navi activated")
                bit_0 = "1"
            else:
                bit_0 = "0"

            if self.checkBox_Oil.isChecked() is True:
                # print("Check oil level activated")
                bit_1 = "1"
            else:
                bit_1 = "0"

            if self.checkBox_trip.isChecked() is True:
                # print("trip activated")
                bit_2 = "1"
            else:
                bit_2 = "0"

            if self.checkBox_mileage.isChecked() is True:
                # print("mileage activated")
                bit_3 = "1"
            else:
                bit_3 = "0"

            if self.checkBox_temperature.isChecked() is True:
                # print("temperature activated")
                bit_4 = "1"
            else:
                bit_4 = "0"

            if self.checkBox_CruiseLimitView.isChecked() is True:
                # print("CruiseLimitView activated")
                bit_5 = "1"
            else:
                bit_5 = "0"

            if self.checkBox_Eco.isChecked() is True:
                # print("Eco activated")
                bit_6 = "1"
            else:
                bit_6 = "0"

            if self.checkBox_MEM.isChecked() is True:
                # print("MEM")
                bit_7 = "1"
            else:
                bit_7 = "0"

            byte_099h = int(bit_0 + bit_1 + bit_2 + bit_3 + bit_4 + bit_5 + bit_6 + bit_7, 2)
            logger(self, 'Байт 0x99h = ' + str(hex(byte_099h)))
            # закончили формировать байт 098h

            # формируем байт 09Ah
            if self.byte09Ahbit0.isChecked() is True:
                # print("bit 0 activated")
                bit_0 = "1"
            else:
                bit_0 = "0"

            if self.byte09Ahbit1.isChecked() is True:
                # print("bit 1 activated")
                bit_1 = "1"
            else:
                bit_1 = "0"

            if self.byte09Ahbit2.isChecked() is True:
                # print("bit 2 activated")
                bit_2 = "1"
            else:
                bit_2 = "0"

            if self.byte09Ahbit3.isChecked() is True:
                # print("bit3 activated")
                bit_3 = "1"
            else:
                bit_3 = "0"

            if self.byte09Ahbit4.isChecked() is True:
                # print("bit 4 activated")
                bit_4 = "1"
            else:
                bit_4 = "0"

            if self.byte09Ahbit5.isChecked() is True:
                # print("bit 5 activated")
                bit_5 = "1"
            else:
                bit_5 = "0"

            if self.byte09Ahbit6.isChecked() is True:
                # print("bit 6 activated")
                bit_6 = "1"
            else:
                bit_6 = "0"

            if self.byte09Ahbit7.isChecked() is True:
                # print("bit 7 activated")
                bit_7 = "1"
            else:
                bit_7 = "0"

            # print(" ")
            byte_09ah = int(bit_0 + bit_1 + bit_2 + bit_3 + bit_4 + bit_5 + bit_6 + bit_7, 2)
            logger(self, 'Байт 0x9Ah = ' + str(hex(byte_09ah)))
            # закончили формировать байт 09Ah

            # формируем байт 09Bh
            if self.theme.currentIndex() == 0:
                bit_0 = "0"
                bit_1 = "1"
                bit_2 = "0"

            if self.theme.currentIndex() == 1:
                bit_0 = "0"
                bit_1 = "0"
                bit_2 = "1"

            if self.theme.currentIndex() == 2:
                bit_0 = "0"
                bit_1 = "0"
                bit_2 = "0"

            if self.theme.currentIndex() == 3:
                bit_0 = "0"
                bit_1 = "1"
                bit_2 = "1"

            if self.theme.currentIndex() == 4:
                bit_0 = "1"
                bit_1 = "0"
                bit_2 = "0"

            if self.clock.isChecked() is True:
                # print("clock activated")
                bit_3 = "1"
                bit_4 = "1"
            else:
                bit_3 = "0"
                bit_4 = "0"

            if self.startbutton.isChecked() is True:
                # print("startbutton activated")
                bit_5 = "1"
            else:
                bit_5 = "0"

            if self.byte09Bhbit6.isChecked() is True:
                # print("bit 6 activated")
                bit_6 = "1"
            else:
                bit_6 = "0"

            if self.byte09Bhbit7.isChecked() is True:
                # print("bit7 activated")
                bit_7 = "1"
            else:
                bit_7 = "0"

            byte_09bh = int(bit_0 + bit_1 + bit_2 + bit_3 + bit_4 + bit_5 + bit_6 + bit_7, 2)
            logger(self, 'Байт 0x9Bh = ' + str(hex(byte_09bh)))
            # закончили формировать байт 09Bh

            # формируем 09Ch
            if self.bodytype.currentIndex() == 0:
                byte_09ch = 0x10

            elif self.bodytype.currentIndex() == 1:
                byte_09ch = 0x20

            elif self.bodytype.currentIndex() == 2:
                byte_09ch = 0x30

            elif self.bodytype.currentIndex() == 3:
                byte_09ch = 0x40
            else:
                byte_09ch = ''

            logger(self, 'Байт 0x9Ch = ' + str(hex(byte_09ch)))
            # закончили формировать 09Ch

            # формируем байт 09Dh
            if self.byte09Dhbit0.isChecked() is True:
                # print("bit 0 activated")
                bit_0 = "1"
            else:
                bit_0 = "0"

            if self.byte09Dhbit1.isChecked() is True:
                # print("bit 1 activated")
                bit_1 = "1"
            else:
                bit_1 = "0"

            if self.byte09Dhbit2.isChecked() is True:
                # print("bit 2 activated")
                bit_2 = "1"
            else:
                bit_2 = "0"

            if self.byte09Dhbit3.isChecked() is True:
                # print("bit3 activated")
                bit_3 = "1"
            else:
                bit_3 = "0"

            if self.byte09Dhbit4.isChecked() is True:
                # print("bit 4 activated")
                bit_4 = "1"
            else:
                bit_4 = "0"

            if self.byte09Dhbit5.isChecked() is True:
                # print("bit 5 activated")
                bit_5 = "1"
            else:
                bit_5 = "0"

            if self.byte09Dhbit6.isChecked() is True:
                # print("bit 6 activated")
                bit_6 = "1"
            else:
                bit_6 = "0"

            if self.checkBox_ParkAssist.isChecked() is True:
                # print("ParkAssist activated")
                bit_7 = "1"
            else:
                bit_7 = "0"

            byte_09dh = int(bit_0 + bit_1 + bit_2 + bit_3 + bit_4 + bit_5 + bit_6 + bit_7, 2)
            logger(self, 'Байт 0x9Dh = ' + str(hex(byte_09dh)))
            # закончили формировать байт 09Dh

            # формируем 09Eh
            byte_09eh = 0x0

            if self.brand.currentIndex() == 0:
                byte_09eh = 0x40

            if self.brand.currentIndex() == 1:
                byte_09eh = 0x20

            if self.brand.currentIndex() == 2:
                byte_09eh = 0x00

            logger(self, 'Байт 0x9Eh = ' + str(hex(byte_09eh)))
            # закончили формировать 09Eh

            self.NewHexValues.setText(
                hex(byte_097h)[2:].zfill(2) + hex(byte_098h)[2:].zfill(2) + hex(byte_099h)[2:].zfill(2) + hex(
                    byte_09ah)[2:].zfill(2) + hex(byte_09bh)[2:].zfill(2) + hex(byte_09ch)[2:].zfill(2) + hex(
                    byte_09dh)[2:].zfill(2) + hex(byte_09eh)[2:].zfill(2))

            cmd_new_line_1 = can.Message(arbitration_id=0x772,
                                         data=[0x10, 0x0A, 0x2E, 0x21, byte_097h, byte_098h, byte_099h,
                                               byte_09ah], extended_id=False)
            cmd_new_line_2 = can.Message(arbitration_id=0x772,
                                         data=[0x21, byte_09bh, byte_09ch, byte_09dh, byte_09eh],
                                         extended_id=False)

            self.new_hex_collected = True
            logger(self, 'Новые параметры для записи сформированы')

        else:
            logger(self, 'Без прочитанных параметров дисплея формировать новые параметры нельзя')

    @asyncSlot()
    async def write_conf(self):
        global cmd_new_line_1
        global cmd_new_line_2
        global mode

        if self.new_hex_collected is True:
            mode = 'telecode'
            self.reader.telecoding()

        else:
            logger(self, 'До формирования новых параметров активация невозможна')
            mode = 'default'


class AboutApp(QtWidgets.QMainWindow, ui_about.Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = MainApp()
    window.show()

    sys.exit(app.exec_())
