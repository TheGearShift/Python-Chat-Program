import sys, threading, socket, time, os, select
from tkinter import Tk, Frame, Scrollbar, Text, Entry, Button, Label

host = "127.0.0.1"
port = 7777
name = ""
first = True
stop = False

Connection_List = []

def center(width, height): #Centers the window
    positionRight = int(root.winfo_screenwidth()/2 - width/2)
    positionDown = int(root.winfo_screenheight()/2 - height/2)
    root.geometry("{}x{}+{}+{}".format(width, height, positionRight, positionDown))

def Type_message(msg): #Types message
    global first
    Text_display.config(state = "normal")
    if first:
        Text_display.insert("end", msg)
        first = False
    else:
        Text_display.insert("end", "\n" + msg) 
    Text_display.config(state = "disabled")
    Text_display.see("end")

def receive(): #Always checks if server broadcast a message and is connected
    while True:
        try:
            message = client_socket.recv(1024).decode()
        except socket.error:
            Type_message("Client: Lost connection to server")
            break
        else:
            Type_message(message)

def send(event = None): #Sends a message to server
    global name, host, first, client_socket        
    msg = entry_field.get()
    entry_field.delete(0, "end")
    if msg == "/clear":
        Text_display.config(state = "normal")
        Text_display.delete(1.0, "end")
        Text_display.update()
        Text_display.config(state = "disabled")
        first = True
    elif "/name" in msg:
        new_name = msg.replace("/name ","")
        try:
            client_socket.send(str.encode("Server: " + name + " changed their name to " + new_name))
        except socket.error:
            Type_message("Client: You are not connected to a server")
        name = new_name
    elif "/connect" in msg:
        try:
            client_socket.send(str.encode("Server: " + name + " disconnected from the server"))
        except socket.error:
            host = ""
        time.sleep(1)
        host = msg.replace("/connect ","")
        if host == "localhost":
            host = socket.gethostbyname(socket.gethostname())
        reconnect_server(host)
    elif not str(msg).isspace() and msg != "":
        try:
            client_socket.send(str.encode(name + ": " + msg))
        except socket.error:
            Type_message("Client: You are not connected to a server")

def on_closing(event = None): #When the application is closed
    global name, client_socket
    try:
        client_socket.send(str.encode("Server: " + name + " disconnected from the server"))
    except socket.error:
        Type_message("")
    time.sleep(1)
    client_socket.close()
    root.quit()
    sys.exit()

def set_name(event = None): #Set name for chat
    global name
    name = str(Name_Entry.get())
    Name_Entry.delete(0, "end")
    name_frame.pack_forget()
    start_frame.pack(fill = "x", expand = 1)

def Server_input(event = None): #Server sends a message to everyone
    global name    
    msg = entry_field.get()
    entry_field.delete(0, "end")
    if msg == "/stop":
        os._exit(0)
    elif "/name" in msg:
        new_name = msg.replace("/name ","")
        Type_message("Server: " + name + " changed their name to " + new_name)
        broadcast_toall(client_socket, "Server: " + name + " changed their name to " + new_name)
        name = new_name
    else:
        Type_message(name + ": " + msg)
        broadcast_toall(client_socket, name + ": " + msg)

def broadcast_toall(sock, message): #Sends a message to all peers
    global Connection_List, client_socket
    for socket in Connection_List:
        if socket != client_socket and socket != sock:
            try:
                socket.send(message.encode())
            except:
                socket.close()
                Connection_List.remove(socket)       

def server_run(): #Always checks if a new client connected or if a message was sent, then sends the message to everyone
    global client_socket, Connection_List
    while True:
        read_sockets, _write_sockets, _error_sockets = select.select(Connection_List, [], [])
        for sock in read_sockets:
            if sock == client_socket:
                sockfd, _addr = client_socket.accept()
                Connection_List.append(sockfd)
            else:
                try:
                    data = sock.recv(1024)
                    if data:
                        sock.send(data)
                        Type_message(data.decode())
                        broadcast_toall(sock, data.decode())
                except:
                    sock.close()
                    Connection_List.remove(sock)
                    continue
                
    #client_socket.close()

def host_server(event = None): #Hosts server
    global host, port, client_socket, send_button
    host = socket.gethostbyname(socket.gethostname())    
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    client_socket.bind((host, port))
    client_socket.listen(4)    
    Connection_List.append(client_socket)    
    threading.Thread(target = server_run, daemon = True).start()
    Type_message("Server: Started port on " + str(port))
    entry_field.bind("<Return>", Server_input)
    send_button.config(command = Server_input)
    start_frame.pack_forget()
    chat_frame.pack(fill = "both", expand = 1)    

def connect_server(event = None): #Tries to connect to the server host
    global name, host, client_socket, send_button    
    entry_field.bind("<Return>", send)
    send_button.config(command = send)
    host = Ip_Entry.get()
    if host == "localhost":
        host = socket.gethostbyname(socket.gethostname())
    Ip_Entry.delete(0, "end")
    try:
        client_socket.connect((host, port))
    except socket.error:
        Response.config(text = "Client: Failed to connect to server")
        client_socket.close()
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    else:
        chat_frame.pack(fill = "both", expand = 1)
        start_frame.pack_forget()
        threading.Thread(target = receive, daemon = True).start()
        client_socket.send(str.encode("Server: " + name + " connected to the server"))

def reconnect_server(host): #Tries to connect to a specified host
    global name, client_socket
    client_socket.close()
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((host, port))
    except socket.error:
        Type_message("Client: Failed to connect to " + host)
    else:
        threading.Thread(target = receive, daemon = True).start()
        client_socket.send(str.encode("Server: " + name + " connected to the server"))

root = Tk()
root.title("Chat")
center(400, 300)

chat_frame = Frame(root) #Sets up chat frame

messages_frame = Frame(chat_frame) #Sets up message frame
type_frame = Frame(chat_frame) #Sets up text frame
start_frame = Frame(root)
name_frame = Frame(root)

messages_frame.pack(fill = "both", expand = 1, padx = (5, 0))
type_frame.pack(fill = "x", padx = 5, pady = 5)
name_frame.pack(fill = "x", expand = 1)

Label(name_frame, text = "What is your name?").pack()
Name_Entry = Entry(name_frame, justify = "center")

Name_Entry.pack(pady = 20)

Button(start_frame, text = "Host Server", command = host_server).pack(pady = 10) #Sets up first page
Label(start_frame, text = "or").pack(pady = 10)
Label(start_frame, text = "Enter IP to connect:").pack(pady = 10)
Ip_Entry = Entry(start_frame, justify = "center")
Response = Label(start_frame)

Ip_Entry.pack(pady = 10)
Response.pack(pady = 5)

fnt = ("", 15)

Label(messages_frame, text = "Welcome to the chat").pack() #Sets up chat page
Scroll = Scrollbar(messages_frame)
Text_display = Text(messages_frame, height = 1, width = 1, wrap = "word", spacing3 = 5, state = "disabled", yscrollcommand = Scroll.set)
entry_field = Entry(type_frame)
send_button = Button(type_frame, text = "Send")

Text_display.pack(side = "left", fill = "both", expand = 1)
Scroll.pack(side = "right", fill = "both")
entry_field.pack(side = "left", fill = "both", expand = 1)
send_button.pack(fill = "both", padx = (5, 0))

Scroll.config(command=Text_display.yview)
Name_Entry.bind("<Return>", set_name)
Ip_Entry.bind("<Return>", connect_server)

root.protocol("WM_DELETE_WINDOW", on_closing)

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

root.mainloop()