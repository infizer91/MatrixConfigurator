
def parsehex(self):
    global mode
    mode = 'default'

    logger(self, 'Обработка данных...')

    hw_id = hex(cmd_ident[0].data[5])[2:].zfill(2) + "" + hex(cmd_ident[0].data[6])[2:].zfill(2) + "" + hex(
        cmd_ident[0].data[7])[2:].zfill(2) + "" + hex(cmd_ident[1].data[1])[2:].zfill(2) + "" + hex(
        cmd_ident[1].data[2])[2:].zfill(2)

    hw_id_2 = hex(cmd_ident[1].data[5])[2:].zfill(2) + "" + hex(cmd_ident[1].data[6])[2:].zfill(2) + "" + hex(
        cmd_ident[0].data[7])[2:].zfill(2) + "" + hex(cmd_ident[2].data[1])[2:].zfill(2) + "" + hex(
        cmd_ident[2].data[2])[2:].zfill(2)

    sw_id = "96" + hex(cmd_ident[5].data[5])[2:].zfill(2) + "" + hex(cmd_ident[5].data[6])[2:].zfill(2) + "" + hex(
        cmd_ident[5].data[7])[2:].zfill(2) + "80"

    sw_ver = hex(cmd_ident[3].data[3])[2:].zfill(2) + "" + hex(cmd_ident[3].data[4])[2:].zfill(2)
    sw_date = str(cmd_ident[4].data[4])[2:].zfill(2) + "." + str(cmd_ident[5].data[4])[2:].zfill(2) + ".20" + str(
        cmd_ident[5].data[5])[2:].zfill(2)

    self.hw_id.setText(hw_id)
    self.hw_id_2.setText(hw_id_2)
    self.sw_id.setText(sw_id)
    self.sw_ver.setText(sw_ver)
    self.sw_date.setText(sw_date)

    byte_097h = cmd_orig_line_1.data[4]
    byte_098h = cmd_orig_line_1.data[5]
    byte_099h = cmd_orig_line_1.data[6]
    byte_09ah = cmd_orig_line_1.data[7]

    byte_09bh = cmd_orig_line_2.data[1]
    byte_09ch = cmd_orig_line_2.data[2]
    byte_09dh = cmd_orig_line_2.data[3]
    byte_09eh = cmd_orig_line_2.data[4]

    self.hexValues.setText(
        str(hex(byte_097h)[2:].zfill(2)) + " " + str(hex(byte_098h)[2:].zfill(2)) + " " + str(
            hex(byte_099h)[2:].zfill(2) + " " + hex(
                byte_09ah)[2:].zfill(2)) + " " + hex(byte_09bh)[2:].zfill(2) + " " + hex(byte_09ch)[2:].zfill(
            2) + " " + hex(
            byte_09dh)[2:].zfill(2) + " " + hex(byte_09eh)[2:].zfill(2))

    # парсим байт 097h - byte_097h
    byte_097h = bin(byte_097h)[2:].zfill(8)  # переводим в бинарные значения
    logger(self, "Байт 0x97h -   bin =  " + byte_097h)

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
        # else:
        # print("nothing else")
        counter += 1

    # закончили парсить байт 097h

    # парсим байт 098h - byte_098h
    byte_098h = bin(byte_098h)[2:].zfill(8)  # переводим в бинарные значения
    logger(self, "byte 098h is " + byte_098h)

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

        # else:
        # print("nothing else")

        counter += 1

    # закончили парсить байт 098h

    # парсим байт 099h - byte_099h

    byte_099h = bin(byte_099h)[2:].zfill(8)  # переводим в бинарные значения
    logger(self, "byte 099h is " + byte_099h)

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
    logger(self, "Байт 0x9Ah is " + byte_09ah)

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
        # else:
        # print("nothing else")

        counter += 1
    # закончили парсить байт 09Ah

    # парсим байт 09Bh - byte_09bh
    byte_09bh = bin(byte_09bh)[2:].zfill(8)  # переводим в бинарные значения
    logger(self, "byte 09Bh is " + byte_09bh)

    theme_bit = []
    clock_bit = []

    counter = 1
    for char in byte_09bh:

        if i == 1:
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
        # else:
        # print("nothing else")

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

    theme_bit.clear()
    # else:
    # print('nothing')

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
    logger(self, "byte 09Dh is " + byte_09dh)

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
        # else:
        # print("nothing else")

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