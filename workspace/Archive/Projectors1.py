import tkinter as win
import socket
import os
import csv
import time
from tkinter import *
from pypjlink import *
from tkinter import messagebox
from tendo import singleton


def clearStatus():
    showStatusMessage("")


def showStatusMessage(statusText):
    statusMessage = Label(mainForm, width=22, height=1, bg="yellow", fg="Red",
                          relief=SUNKEN, font=("Arial Bold", 12), text=statusText)
    statusMessage.place(x=35, y=60)


def showOnButton(color):
    onButton = Button(mainForm, text="הדלק", width=6, height=1, bg=color,
                      font=("Arial Bold", 12), command=poweronprojector)
    onButton.place(x=35, y=10)


def showOffButton(color):
    offButton = Button(mainForm, text="כבה", width=6, height=1, bg=color,
                       font=("Arial Bold", 12), command=shutdownprojector)
    offButton.place(x=130, y=10)



# check if projector is alive using ping
def checkifalive():
    global pingstatus
    pingstatus = ""
    response = os.popen("ping " + projectorIP + " \n -c 1").read()
    if ("unreachable" in response):
        pingstatus = "False"
        # print (pingstatus)
    else:
        pingstatus = "True"
        # print(pingstatus)


def connectProjector():
    global projectorName
    global projectorState
    global projector
    try:
        projector = Projector.from_address(projectorIP)
    except:
        win.Tk().withdraw()
        win.messagebox.showwarning("תקלה", "לא ניתן להתחבר למקרן\nנא לפנות לתמיכה טכנית")
        os._exit(0)
    projector.authenticate('Angel')
    projectorName = projector.get_name()
    projectorState = projector.get_power()


def checkstatus():
    global statusTimer
    checkifalive()
    if pingstatus == "False":
        showStatusMessage("המקרן לא מחובר")
        showOnButton("grey")
        showOffButton("grey")
    else:
        connectProjector()
        if projectorState == "off":
            showStatusMessage("המקרן כבוי")
            showOnButton("grey")
            showOffButton("red")
            """
            elif projectorState == "warm-up":
                showStatusMessage("המקרן מתחמם")
                showOnButton("green")
                showOffButton("grey")
            """
        elif projectorState == "cooling":
            showStatusMessage("המקרן מתקרר")
            showOnButton("grey")
            showOffButton("red")
        else:
            showStatusMessage("המקרן דלוק")
            showOnButton("green")
            showOffButton("grey")
    time.sleep(3)


def poweronprojector():
    checkifalive()
    if pingstatus == "False":
        showStatusMessage("המקרן לא מחובר")
    else:
        connectProjector()
        if projectorState == "off":
            projector.set_power('on')
            showStatusMessage("המקרן דלוק")
            showOnButton("green")
            showOffButton("grey")
        elif projectorState == "cooling":
            showStatusMessage("המקרן מתקרר")
            showOnButton("grey")
            showOffButton("red")
    time.sleep(3)


def shutdownprojector():
    checkifalive()
    if pingstatus == "False":
        showStatusMessage("המקרן לא מחובר")
    else:
        connectProjector()
        if projectorState == "on":
            projector.set_power('off')
        showStatusMessage("המקרן כבוי")
        showOnButton("grey")
        showOffButton("red")
    time.sleep(3)


def on_closing():
    if messagebox.askokcancel("יציאה", "אישור יציאה"):
        mainForm.destroy()
        os._exit(0)


try:
    current_instance = singleton.SingleInstance()
except:
    os._exit(0)

currentFolder = os.getcwd()
with open(currentFolder + '/projlist.csv') as csv_file:
    csv_reader = csv.DictReader(csv_file, delimiter=',')
    try:
        result = next(z for z in csv_reader if z["computerName"] == socket.gethostname().upper())
    except:
        win.Tk().withdraw()
        win.messagebox.showwarning("תקלה", "המחשב אינו מופיע ברשימת המקרנים\nנא לפנות לתמיכה טכנית")
        os._exit(0)

    projectorName = result["projName"]
    projectorIP = result["projIP"]

mainForm = Tk()
mainForm.withdraw()
mainForm.iconbitmap(currentFolder + '/video_projector.ico')
mainForm.wm_title('ניהול מקרן כיתה')
    # mainForm.geometry('300x200')  # setting the size of the window
Tk_Width = 300
Tk_Height = 100
positionRight = int(mainForm.winfo_screenwidth() / 2 - Tk_Width / 2)
positionDown = int(mainForm.winfo_screenheight() / 2 - Tk_Height / 2)
    # Set window in center screen with following way.
mainForm.geometry("{}x{}+{}+{}".format(300, 100, positionRight, positionDown))
mainForm.maxsize(width=300, height=100)
mainForm.minsize(width=300, height=100)
statusButton = Button(mainForm, text="Status", width=6, height=1, bg="yellow", command=checkstatus)
statusButton.place(x=230, y=15)
checkstatus()
mainForm.deiconify()
mainForm.protocol("WM_DELETE_WINDOW", on_closing)
mainForm.mainloop()
