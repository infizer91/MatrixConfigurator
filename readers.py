from PySide2.QtCore import QThread


class Reader_0(QThread):
    def run(i):
        #logger('Ридер_0 запущен')

        cycle = True
        global mode

        while cycle is True and connected is True:
            try:
                msg_0 = bus_0.recv()

                if msg_0.arbitration_id == 0x772:
                    tracer(msg_0)
                    check_cmd_0(msg_0)

                else:
                    new_msg_0 = msg_0
                    bus_1.send(new_msg_0)

            except Exception as e:
                #print(str(e))
                pass


# Ридер 1
class Reader_1(QThread):
    def run(i):
        #logger('Ридер_1 запущен')
        cycle = True
        global unlocked
        global mode

        while cycle is True and connected is True:
            try:
                msg_1 = bus_1.recv()
                if msg_1.arbitration_id == 0x672:
                    tracer(msg_1)
                    check_cmd_1(msg_1)

                new_msg_1 = msg_1
                bus_0.send(new_msg_1)

            except Exception as e:
                print(e)
                pass

