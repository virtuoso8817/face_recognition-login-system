#FACE RECOGNITION LOGIN SYSTEM

import json

from tkinter import Tk, Canvas, PhotoImage, Label, Toplevel, Entry, StringVar, Frame, Button, simpledialog, filedialog
from tkinter import ttk
from PIL import Image, ImageTk
import cv2
import face_recognition
import threading
import os
import pickle
import pyttsx3
import datetime
from openpyxl import Workbook
from pathlib import Path
import re
import queue
from tkinter import messagebox
from multiprocessing import Process,Queue

CONFIG_FILE = 'config.json'

class Dlib_Face_Unlock:

    def __init__(self):
        try:
            with open('labels.pickle', 'rb') as f:
                self.og_labels = pickle.load(f)
        except FileNotFoundError:
            print("No label.pickle file detected, will create required pickle files")

        self.current_id = 0
        self.labels_ids = {}

        self.BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.image_dir = os.path.join(self.BASE_DIR, 'images')
        for root, dirs, files in os.walk(self.image_dir):
            for file in files:
                if file.endswith(('png', 'jpg','jpeg')):
                    path = os.path.join(root, file)
                    label = os.path.basename(os.path.dirname(path)).replace(' ', '-').lower()
                    if label not in self.labels_ids:
                        self.labels_ids[label] = self.current_id
                        self.current_id += 1

        print(self.labels_ids)

        if self.labels_ids != self.og_labels:
            with open('labels.pickle', 'wb') as file:
                pickle.dump(self.labels_ids, file)

            self.known_faces = []
            for i in self.labels_ids:
                directory = os.path.join(self.image_dir, i)
                if not os.path.exists(directory):
                    os.makedirs(directory)

                for imgNo, filename in enumerate(os.listdir('images/' + i), start=1):
                    img_path = os.path.join('images', i, filename)
                    if os.path.exists(img_path) and img_path.lower().endswith(('png', 'jpg', 'jpeg')):
                        img = face_recognition.load_image_file(img_path)
                        face_encodings = face_recognition.face_encodings(img)
                        if face_encodings:
                            img_encoding = face_encodings[0]  # Use the first encoding if available
                            self.known_faces.append([i, img_encoding])
                        else:
                            print(f"No face found in image: {img_path}")
                    else:
                        print(f"No image file found at {img_path}")

            print(self.known_faces)
            print("No Of Imgs" + str(len(self.known_faces)))
            with open('KnownFace.pickle', 'wb') as known_faces_file:
                pickle.dump(self.known_faces, known_faces_file)
        else:
            with open('KnownFace.pickle', 'rb') as faces_file:
                self.known_faces = pickle.load(faces_file)
            print(self.known_faces)


    def ID(self):
        cap = cv2.VideoCapture(0)
        running = True
        face_names = []
        while running:
            ret, frame = cap.read()
            small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
            rgb_small_frame = small_frame[:, :, ::-1]
            if running:
                face_locations = face_recognition.face_locations(frame)
                if len(face_locations) > 0:
                    face_encodings = face_recognition.face_encodings(frame, face_locations)
                    face_names = []
                    for face_encoding in face_encodings:
                        for face in self.known_faces:
                            matches = face_recognition.compare_faces([face[1]], face_encoding)
                            if True in matches:
                                running = False
                                face_names.append(face[0])
                                break
            cv2.imshow('Login', frame)

            # Hit 'q' on the keyboard to quit!
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            print("The best match(es) is" + str(face_names))
            cap.release()
            cv2.destroyAllWindows()
            break
        return face_names

def prompt_for_base_directory():
    root = Tk()
    root.withdraw()  # Hide the main window
    base_directory = filedialog.askdirectory(title="Select Base Directory")
    if base_directory:
        with open(CONFIG_FILE, 'w') as f:
            json.dump({'base_directory': base_directory}, f)
        return base_directory
    else:
        raise ValueError("Base directory must be selected to proceed.")


def set_base_directory():
    root = Tk()
    root.withdraw()  # Hide the main window
    base_directory = filedialog.askdirectory(title="Select Base Directory")
    if base_directory:
        with open(CONFIG_FILE, 'w') as f:
            json.dump({'base_directory': base_directory}, f)
        return base_directory
    else:
        raise ValueError("Base directory must be selected to proceed.")

def get_base_directory():
    if not os.path.exists(CONFIG_FILE):
        raise ValueError("Base directory not set. Please register first.")
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
    return config.get('base_directory')


def register():
    base_directory = set_base_directory()
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        workbook = Workbook()
        sheet = workbook.active
        sheet.append(["Timestamp", "Name", "Phone", "Position"])
    except Exception as e:
        print(f"Error creating workbook: {e}")
        return
    registration_info = [current_time, name.get(), phone.get(), position.get()]
    sheet.append(registration_info)
    name_input = name.get()
    phone_input = phone.get()

    # Check if name contains only letters
    if not re.match("^[A-Za-z]*$", name_input):
        messagebox.showerror("Alert", "Not a valid name")
        return

    # Check if phone contains only digits
    if not phone_input.isdigit():
        messagebox.showerror("Alert", "Not a valid number")
        return

        # Use simpledialog to ask for username and password
    username = simpledialog.askstring("Set Credentials", "Set your username:", parent=master)
    if username is None:  # User cancelled the dialog
        return
    password = simpledialog.askstring("Set Credentials", "Set your password:", parent=master, show='*')
    if password is None:  # User cancelled the dialog
        return


    try:
        workbook.save("registration_log.xlsx")
        print("Registration information saved to registration_log.xlsx")
    except Exception as e:
        print(f"Error saving workbook: {e}")

    with open("log.txt", "a") as log_file:
        log_file.write(f"[{current_time}] User registered: {name.get()}\n")

    base_dir = get_base_directory()
    user_dir = os.path.join(base_dir, name.get().lower())
    Path(user_dir).mkdir(parents=True, exist_ok=True)


    if not os.path.exists("images"):
        os.makedirs("images")

    dfu = Dlib_Face_Unlock()
    if name.get().lower() in dfu.labels_ids:
        messagebox.showerror("Alert", "Face Already Registered")
        return

    Path("images/" + name.get()).mkdir(parents=True, exist_ok=True)

    numberOfFile = len([filename for filename in os.listdir('images/' + name.get())
                        if os.path.isfile(os.path.join('images/' + name.get(), filename))])
    numberOfFile += 1

    cam = cv2.VideoCapture(0)

    cv2.namedWindow("test")

    while True:
        ret, frame = cam.read()
        cv2.imshow("test", frame)
        if not ret:
            break
        k = cv2.waitKey(1)

        if k % 256 == 27:
            print("Escape hit, closing...")
            cam.release()
            cv2.destroyAllWindows()
            break
        elif k % 256 == 32:
            img_name = str(numberOfFile) + ".png"
            cv2.imwrite(img_name, frame)
            print("{} written!".format(img_name))
            os.replace(str(numberOfFile) + ".png", "images/" + name.get().lower() + "/" + str(numberOfFile) + ".png")
            cam.release()
            cv2.destroyAllWindows()
            break

    with open('images/' + name.get() + '/details.pickle', 'wb') as f:
        pickle.dump({'name': name.get(), 'phone': phone.get(), 'position': position.get(),'username': username, 'password': password}, f)
    raiseFrame(master)

    try:
        engine = pyttsx3.init()
        engine.say("Registered successfully")
        engine.runAndWait()
    except Exception as e:
        print(f"Error while speaking: {e}")

master = Tk()

'''
userMenuFrame.columnconfigure(3, weight=1)
'''


master.title("Project")
master.geometry('900x500')



userMenuFrame = Frame(master)


def raiseFrame(frame):
        frame.tkraise()

def logFrameRaiseFrame():
        raiseFrame(master)


def show_user_details(details, photo):
    # Create a new top-level window
    details_window = Toplevel()
    details_window.title("User Details")
    details_window.geometry("500x500")  # Adjust size as needed
    details_window.configure(bg='#f0f0f0')
    # If a photo is available, display it
    if photo is not None:
        img_label = Label(details_window, image=photo,bg='#f0f0f0')
        img_label.pack(pady=10)  # Adjust padding as needed

    # Display user details
    Label(details_window, text=f"Hello, {details['name']}", font=("Helvetica", 18,"bold"), fg='#333333', bg='#f0f0f0').pack(pady=10)
    Label(details_window, text=f"Phone: {details['phone']}", font=("Helvetica", 16),fg='#666666', bg='#f0f0f0').pack(pady=5)
    Label(details_window, text=f"Position: {details['position']}", font=("Helvetica", 16), fg='#666666', bg='#f0f0f0').pack(pady=5)

    logout_button = Button(details_window, text="Logout", command=lambda: logout(details_window, details))
    logout_button.pack(pady=30)

    # Keep the window open
    details_window.mainloop()

def logout(window, details):
    # Log the logout event
    with open('logout.txt', 'a') as log:
        log.write(f'{datetime.datetime.now()}: {details["name"]} logged out\n')

    # Close the current window
    window.destroy()

    # Redirect to the master window
    master.deiconify()




def get_image_path(username):
    base_dir = get_base_directory()
    images_dir = os.path.join(base_dir, "images")
    user_dir = os.path.join(images_dir, username)
    image_path = os.path.join(user_dir, "1.png")
    return image_path

def disable_event():
    pass


def open_registration_window():
    regFrame = Toplevel(master)
    regFrame.title("Registration")
    regFrame.geometry('900x500')

    # Load and resize background image
    bck_image1 = Image.open('mo.jpg')
    resized_bck_image1 = bck_image1.resize((900, 600), Image.Resampling.LANCZOS)
    bck_end1 = ImageTk.PhotoImage(resized_bck_image1)

    # Create a canvas and display the background image
    canvas = Canvas(regFrame, width=900, height=500)
    canvas.pack(fill="both", expand=True)
    canvas.create_image(0, 0, image=bck_end1, anchor="nw")

    # Attach the background image to the regFrame to prevent garbage collection
    regFrame.bck_end1 = bck_end1

    # Load, resize, and display the PNG image
    png_image1 = Image.open('register.png')
    resized_png_image1 = png_image1.resize((450, 150), Image.Resampling.LANCZOS)
    logo_image1 = ImageTk.PhotoImage(resized_png_image1)
    canvas.create_image(300, 0, image=logo_image1, anchor="nw")

    # Attach the logo image to the regFrame to prevent garbage collection
    regFrame.logo_image1 = logo_image1
    name_label = Label(regFrame, text="Name:       ", font=("Arial", 30), bg="white")
    nameEntry = Entry(regFrame, font=("Arial", 30), textvariable=name)
    canvas.create_window(130, 150, window=name_label, anchor="nw")
    canvas.create_window(330, 150, window=nameEntry, anchor="nw")

    phone_label = Label(regFrame, text="Phone:       ", font=("Arial", 30), bg="white")
    phoneEntry = Entry(regFrame, font=("Arial", 30), textvariable=phone)
    canvas.create_window(130, 200, window=phone_label, anchor="nw")
    canvas.create_window(330, 200, window=phoneEntry, anchor="nw")

    position_label = Label(regFrame, text="Position:     ", font=("Arial", 30), bg="white")
    positionEntry = Entry(regFrame, font=("Arial", 30), textvariable=position)
    canvas.create_window(130, 250, window=position_label, anchor="nw")
    canvas.create_window(330, 250, window=positionEntry, anchor="nw")

    btn_image2 = Image.open('button_register.png')  # Replace 'button_image.png' with your button image path
    resized_btn_image2 = btn_image2.resize((200, 100), Image.Resampling.LANCZOS)  # Adjust size as needed
    button_img2 = ImageTk.PhotoImage(resized_btn_image2)
    regFrame.button_img2 = button_img2
    # Create an image button using a Label
    button2 = Label(regFrame, image= button_img2, cursor="hand2")
    button2.place(x=350, y=350)  # Adjust position as needed
    button2.bind("<Button-1>", lambda event:register() )


def button_click(event=None):
    print("button clicked")

def get_username():
    try:
        return simpledialog.askstring("Login", "Enter your username:")
    except Tk.TclError as e:
        print("TclError occurred. Retrying...")
        return get_username()

def login(queue):


    dfu = Dlib_Face_Unlock()
    user = dfu.ID()
    photo = None
    if user == []:
        queue.put("FACE_NOT_RECOGNIZED")

    else:
        with open('images/' + user[0] + '/details.pickle', 'rb') as f:
            details = pickle.load(f)
            loggedInUser.set(details['name'])
            loggedInPhone.set(details['phone'])
            loggedInPosition.set(details['position'])
        try:
            engine = pyttsx3.init()
            engine.say("Login Successful")
            engine.runAndWait()
        except Exception as e:
            print(f"Error while speaking: {e}")



    # Load the image
    if user:
        image_path = get_image_path(user[0].lower())  # replace with actual image path
        if os.path.exists(image_path):
            try:
                image = Image.open(image_path)
                img_resized = image.resize((200, 220))  # Resize as needed
                photo = ImageTk.PhotoImage(img_resized)

                # Create a label and add it to the GUI
                if photo is not None:
                    img_label = Label(userMenuFrame, image=photo)
                    img_label.image = photo  # Keep a reference to the image
                    img_label.grid(row=0, column=3, sticky='nsew', padx=0, pady=0)
                else:
                    print("Failed to load image.")
            except Exception as e:
                print(f"Error loading image: {e}")
        else:
            print("Image not found.")

        # Log the login
        with open('login_log.txt', 'a') as log:
            log.write(f'{datetime.datetime.now()}: {details["name"]} logged in with face recognition\n')

        if details:
            show_user_details(details, photo)
            raiseFrame(userMenuFrame)

        else:
            print("User details not found.")


def threaded_login():
    q = queue.Queue()
    thread = threading.Thread(target=login, args=(q,))
    thread.start()

    def check_queue():
        try:
            msg = q.get_nowait()
            if msg == "FACE_NOT_RECOGNIZED":
                username = simpledialog.askstring("Login", "Enter your username: ")
                password = simpledialog.askstring("Login", "Enter your password:", parent=master, show='*')
                user_found = False
                details = None
                photo = None
                # Here you should verify the username and password. This is just a placeholder.
                for user_dir in os.listdir('images/'):
                    with open(f'images/{user_dir}/details.pickle', 'rb') as f:
                        details = pickle.load(f)
                        if details['username'] == username and details['password'] == password:
                            print(f"Login Successful for user: {details['name']}")
                            loggedInUser.set(details['name'])
                            loggedInPhone.set(details['phone'])
                            loggedInPosition.set(details['position'])
                            user_found = True
                            image_path = get_image_path(user_dir.lower())
                            if os.path.exists(image_path):
                                image = Image.open(image_path)
                                img_resized = image.resize((200, 220))  # Resize as needed
                                photo = ImageTk.PhotoImage(img_resized)
                                with open('login_log.txt', 'a') as log:
                                    log.write(
                                        f'{datetime.datetime.now()}: {details["name"]} logged in with username and password\n')
                            break
                if not user_found:
                    print("Invalid username or password")
                else:
                    show_user_details(details, photo)
        except queue.Empty:
            master.after(100, check_queue)

    check_queue()


# Background image setup
bck_image = Image.open('mo.jpg')
resized_bck_image = bck_image.resize((900, 600), Image.Resampling.LANCZOS)
bck_end = ImageTk.PhotoImage(resized_bck_image)










canvas = Canvas(master, width=900, height=500)
canvas.pack(fill="both", expand=True)
canvas.create_image(0, 0, image=bck_end, anchor="nw")

# PNG image setup
png_image = Image.open('kom.png')
resized_png_image = png_image.resize((450, 150), Image.Resampling.LANCZOS)
logo_image = ImageTk.PhotoImage(resized_png_image)

# Use Canvas to display the PNG image to preserve transparency
canvas.create_image(300, 0, image=logo_image, anchor="nw")

# Button image setup
btn_image = Image.open('button_login.png')  # Replace 'button_image.png' with your button image path
resized_btn_image = btn_image.resize((100, 50), Image.Resampling.LANCZOS)  # Adjust size as needed
button_img = ImageTk.PhotoImage(resized_btn_image)

# Create an image button using a Label
button = Label(master, image=button_img, cursor="hand2")
button.place(x=190, y=350)  # Adjust position as needed
button.bind("<Button-1>", lambda event:threaded_login())

# Button image setup
btn_image1 = Image.open('button_register.png')  # Replace 'button_image.png' with your button image path
resized_btn_image1 = btn_image1.resize((100, 50), Image.Resampling.LANCZOS)  # Adjust size as needed
button_img1 = ImageTk.PhotoImage(resized_btn_image1)

# Create an image button using a Label
button1 = Label(master, image=button_img1, cursor="hand2")
button1.place(x=350, y=350)  # Adjust position as needed
button1.bind("<Button-1>", lambda event: open_registration_window())


name = StringVar()
phone = StringVar()
position = StringVar()
loggedInUser = StringVar()
loggedInPhone = StringVar()
loggedInPosition = StringVar()



dfu = Dlib_Face_Unlock()
master.mainloop()
