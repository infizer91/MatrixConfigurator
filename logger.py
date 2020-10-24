import time

current_date = time.strftime("%Y-%m-%d")


def tracer(text):

    text = str(text)
    print(text)

    with open('traces/' + current_date + '-trace.txt', 'a+') as file:
        file.write(text + "\n")


def logger(window, text):
    text = str(text)
    event_time = time.strftime("%H:%M:%S")
    print(text)
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
