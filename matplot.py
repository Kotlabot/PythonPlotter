#!/bin/python3
from collections import namedtuple
from tkinter import Tk, BooleanVar, Entry, Label, Menu,\
Button, BOTH, StringVar, OptionMenu, Checkbutton
import datetime
import os
import matplotlib
import matplotlib.dates as mdates
matplotlib.use("TkAgg")
import matplotlib.backends.backend_tkagg as back
import matplotlib.pyplot as plt
import port_reader

#Definition of GraphData structure, where x,y,z are arrays with data.
GraphData = namedtuple("GraphData", "x_data y_data z_data")
class Context:
    def __init__(self):
        self.root = Tk()
        self.fig, self.axs = plt.subplots(3) #Creating subplots
        self.canvas = back.FigureCanvasTkAgg(self.fig, self.root)
        self.points_per_frame = 5
        self.is_animating = False #If animation running.
        self.record = False #Status of recording.
        self.rc_path = "recorded.txt" #Path for recording file.
        self.ld_path = "" #Load file path
        self.frame_rate = 50 #In miliseconds
        #Used for calculation of next timestamp
        self.last_time = datetime.timedelta(0, 0)
        self.time = [str(self.last_time)] #X line of each plot
        self.ports = [] #Founded conected ports.
        self.port = "" #Choosen port.
        self.graphs = [] #Data for graph.
        self.status = Label() #Status label.
        self.settigs_window_showed = False
        self.show_full_graph = BooleanVar()
        self.show_full_graph.set(False)
        self.x_show = BooleanVar() #Show X line.
        self.x_show.set(True)
        self.y_show = BooleanVar() #Show Y line.
        self.y_show.set(True)
        self.z_show = BooleanVar() #Show Z line.
        self.z_show.set(True)

class SettingsWindow:
    def __init__(self, ctx):
        self.settings = Tk()
        self.ctx = ctx
        #Setting path to load file.
        self.label_ld_path = Label(self.settings, text="Load file path:")
        self.label_ld_path.grid(column=0, row=0)
        self.ld_path_entry = Entry(self.settings)
        self.ld_path_entry.grid(column=1, row=0)

        #Setting path to record file.
        self.label_rc_path = Label(self.settings, text="Path to record file:")
        self.label_rc_path.grid(column=0, row=1)
        self.rc_path_entry = Entry(self.settings, textvariable=ctx.rc_path)
        self.rc_path_entry.insert(0, ctx.rc_path)
        self.rc_path_entry.grid(column=1, row=1)

        #Setting describer.
        self.label_port_path = Label(self.settings,\
        text="Select from founded connected ports:")
        self.label_port_path.grid(column=0, row=2)

        self.variable = StringVar(self.settings)
        if len(ctx.ports) > 0:
            self.variable.set(ctx.ports[0])
        else:
            self.variable.set('None')
        self.opt = OptionMenu(self.settings, self.variable, *ctx.ports)
        self.opt.grid(column=1, row=2)

        #Scan ports
        self.scan_button = Button(self.settings, text="Scan ports", command=self.scan_ports)
        self.scan_button.grid(column=2, row=2)

        #Set's how many data points should be in each line.
        self.frames_p_plt_l = Label(self.settings, text="Set's maximum points in lines:")
        self.frames_p_plt_l.grid(column=0, row=3)
        self.frames_p_plt_e = Entry(self.settings, textvariable=ctx.points_per_frame)
        self.frames_p_plt_e.insert(0, ctx.points_per_frame)
        self.frames_p_plt_e.grid(column=1, row=3)

        #Save and destroy widget
        self.exit_button = Button(self.settings, text="OK", command=self.save_and_quit)
        self.exit_button.grid(column=0, row=5)

        self.info_label = Label(self.settings, text="Info label")
        self.info_label.grid(column=1, row=6)
        self.settings.mainloop()

    #Scanning all avalible serial ports.
    def scan_ports(self):
        self.info_label.config(text="")
        port_list = self.ctx.reader.list_serial_ports()
        if port_list != None:
            self.ctx.ports = port_list
            if self.ctx.port == '' and len(port_list) != 1:
                self.ctx.port = port_list[0]
                self.info_label.config(text="Devices were founded!")
            elif len(port_list) == 1:
                self.info_label.config(text="No devices were founded!")

    #Saving all variables at the end. Destroyer
    def save_and_quit(self):
        ld_path_entry = self.ld_path_entry.get()
        if ld_path_entry != '':
            self.ctx.ld_path = ld_path_entry

        rc_path_entry = self.rc_path_entry.get()
        if rc_path_entry != '':
            self.ctx.rc_path = rc_path_entry

        if self.variable.get() != '' and self.variable.get() != "None":
            self.ctx.port = self.variable.get()

        frames_p_plt_entry = self.frames_p_plt_e.get()
        if frames_p_plt_entry != '' and frames_p_plt_entry != 0:
            self.ctx.points_per_frame = int(frames_p_plt_entry)

        self.ctx.settigs_window_showed = False
        self.settings.destroy()

class NavigationToolbar(back.NavigationToolbar2Tk):
    # only display the buttons we need
    toolitems = [t for t in back.NavigationToolbar2Tk.toolitems if
                 t[0] in ('Home', 'Back', 'Forward', 'Pan', 'Zoom', 'Subplots')]

#Loads data from recorded file
def load_data_from_file(ctx):
    records = init_graph_data() #Init new graphs data structure
    if os.path.exists(ctx.ld_path) or os.access(os.path.dirname(ctx.ld_path), os.W_OK):
        file_load = open(ctx.ld_path, "r") #Open file for reading
        text = file_load.readlines()
        for line in text:
            if line[0] == '#':
                try:
                    graphid = int(line[7])
                    yindex = line.index('Y')
                    zindex = line.index('Z')
                    #Getting substring of X,Y,Z fields by X,Y,Z index
                    records[graphid].x_data.append(int(line[11:(yindex-1)]))
                    records[graphid].y_data.append(int(line[(yindex + 2):(zindex -1)]))
                    records[graphid].z_data.append(int(line[(zindex + 2):]))
                except:
                    change_status("Invalid data!! : {0}".format(line))
                    return None
        change_status("Data loaded")
        file_load.close()
        return records
    else:
        #If file doesn't exists.
        change_status("Invalid destinantion for load file! Please set path in settings.")
        return None

#For now just random data.
def read_data(ctx):
    readed_data = []
    if ctx.port != 'Test':
        readed_data = ctx.reader.read_chunk_from_port(ctx.port, ctx.port)
        if readed_data == None:
            change_status("Permission denied! Run code under sudo/admin")
            return None
    else:
        readed_data = ctx.reader.generate_random_data()
    
    ctx.last_time = ctx.last_time + datetime.timedelta(0, 50)
    ctx.time.append(str(ctx.last_time))
    points = len(ctx.graphs[0].x_data)

    for i in range(0, 3):
        ctx.graphs[i].x_data.append(readed_data[i].x_data)
        ctx.graphs[i].y_data.append(readed_data[i].y_data)
        ctx.graphs[i].z_data.append(readed_data[i].z_data)

        #Remove all except last few points.
        if (not ctx.show_full_graph.get()) and (points > ctx.points_per_frame):
            ctx.axs[i].cla()
            for z in range(points - ctx.points_per_frame):
                ctx.graphs[i].x_data.pop(0)
                ctx.graphs[i].y_data.pop(0)
                ctx.graphs[i].z_data.pop(0)
        if ctx.record:
            write_data_to_rc(ctx, "# Plot:{0};X:{1};Y:{2};Z:{3}\n".format(i,\
            ctx.graphs[i].x_data[-1], ctx.graphs[i].y_data[-1], ctx.graphs[i].z_data[-1]))

    #Remove overflowing timestamp.
    if (not ctx.show_full_graph.get())\
        and (points > ctx.points_per_frame):
            for z in range(points - ctx.points_per_frame):
                ctx.time.pop(0)

#TODO: Figure out, how to make this better. Don't open file per frame
def write_data_to_rc(ctx, text):
    if os.path.exists(ctx.rc_path) or os.access(os.path.dirname(ctx.rc_path), os.W_OK):
        record_file = open(ctx.rc_path, "a+")
        record_file.writelines(text)
        record_file.close()
    else:
        change_status("Invalid destinantion for record file!")
        ctx.record = False
        ctx.is_animating = False

#Plots graph data to subplot with given graphid.
def plot_graph(ctx, graphid):
    if ctx.x_show.get():
	#Plots 'X' line in subplot.
        ctx.axs[graphid].plot(ctx.time, ctx.graphs[graphid].x_data, color="red", label="X")
    if ctx.y_show.get():
	#Plots 'Y' line in subplot.
        ctx.axs[graphid].plot(ctx.time, ctx.graphs[graphid].y_data, color="blue", label="Y")
    if ctx.z_show.get():
	#Plots 'Z' line in subplot.
        ctx.axs[graphid].plot(ctx.time, ctx.graphs[graphid].z_data, color="green", label="Z")

#Add legend to given subplot.
def set_legend(ctx, graphid):
    plot_graph(ctx, graphid)
    #Loc determinates location of legend grid.
    ctx.axs[graphid].legend(loc="upper left")

#Generate new timestamps after loading data.
def generate_timestamps(ctx):
    #Generate empty field
    ctx.time = []
    ctx.last_time = datetime.timedelta(0, 0)
    #Generate timestamps by data
    for i in range(0, len(ctx.graphs[0].x_data)):
        timestamp = ctx.last_time + datetime.timedelta(0, 50)
        ctx.time.append(str(timestamp))
        ctx.last_time = timestamp

#Draws plotted data.
def draw_data(ctx):
    ctx.canvas.draw()
    #Important line of code. That's allows you to connect matplotlib
    #with tkinter.
    #Creates new widget and packs it to TK main widget.
    #fill=BOTH is necessary for filling the widget on unused space of
    # masterwidget.
    ctx.canvas.get_tk_widget().pack(fill=BOTH, expand=1)

def animate(ctx):
    for x in range(0, 3):
        plot_graph(ctx, x)
    draw_data(ctx)

def set_animator(ctx):
    if ctx.is_animating:
        read_data(ctx)
        animate(ctx)
        #Instead of while loop. It's only way how to do this, because
        #root.mainloop doesn't allows you to redraw widets other way.
        ctx.root.after(ctx.frame_rate, lambda: set_animator(ctx))

#Set actual status of app.
def change_status(text):
    global CTX
    CTX.status.config(text=text)

#If you want to turn of graph full show, this will reduce points
#per frame.
def discard_overflowing_points(ctx):
    points = len(ctx.graphs[0].x_data)
    if points > ctx.points_per_frame:
        ctx.time = ctx.time[points - ctx.points_per_frame:]
        for i in range(0, 3):
            #Saving last n points
            x_data = ctx.graphs[i].x_data[points - ctx.points_per_frame:]
            y_data = ctx.graphs[i].y_data[points - ctx.points_per_frame:]
            z_data = ctx.graphs[i].z_data[points - ctx.points_per_frame:]
            ctx.graphs[i] = GraphData(x_data, y_data, z_data)

#Stopbutton click event handler
def stop_animator_event(ctx):
    ctx.is_animating = False
    change_status("Idling...")

#Startbutton click event handler
def start_animator_event(ctx):
    #If animator is not already running
    if not ctx.is_animating:
        ctx.is_animating = True
        set_animator(ctx)
        change_status("Reading from port:{0}".format(ctx.port))

def clear_graph_event(ctx):
    #Clear timestamps
    ctx.last_time = datetime.timedelta(0, 0)
    ctx.time = [str(ctx.last_time)]

    #Init empty data arrays
    ctx.graphs = init_graph_data()
    for x in range(0, 3):
        ctx.axs[x].cla() #Clearing old subplot data
        set_legend(ctx, x)
    draw_data(ctx)

def set_recorder_event(ctx):
    ctx.record = not ctx.record
    if ctx.record: #Start recording
        change_status("Recording...")
        #TODO: Coplete port
        write_data_to_rc(ctx,\
        "Recording started at: {0}  port: {1}\n".format(datetime.datetime.now(), ctx.port))
    #If recording should be stopped, change status for reading or idling.
    elif ctx.is_animating:
        change_status("Reading from port: {0}".format(ctx.port))
    else:
        change_status("Idling...")

def load_data_event(ctx):
    #Load data from file
    ctx.graphs = load_data_from_file(ctx)
    if ctx.graphs != None:
        #Generate new timestamps for loaded data
        generate_timestamps(ctx)
        for x in range(0, 3):
            #If there is no data, throw excepion.
            if len(ctx.graphs[x].x_data) == 1 or len(ctx.graphs[x].y_data) == 1 \
                or len(ctx.graphs[x].z_data) == 1:
                change_status("Invalid file! No datas for graph:{0}".format(x))
            else:
                ctx.axs[x].cla()
                plot_graph(ctx, x)
        draw_data(ctx)

def settings_widget_show_event(ctx):
    if (not ctx.settigs_window_showed):
        ctx.settigs_window_showed = True
        SettingsWindow(ctx)

#Changing viewable lines in plot
def view_set(ctx):
    for x in range(0, 3):
        ctx.axs[x].cla()
        set_legend(ctx, x)

#Init reader, scan avalible ports and set first as default.
def init_reader(ctx):
    reader = port_reader.Reader()
    founded = reader.list_serial_ports()
    if founded != None: 
        if len(founded) > 0:
            ctx.ports = founded
            ctx.port = ctx.ports[0]
        else:
            change_status("No ports founded! Mayby run under su/admin")
    else:
        change_status("Invalid Os!! Unable to read from USB!!")
    return reader

#Initialize empty data arrrays.
def init_graph_data():
    return [GraphData([0], [0], [0]), GraphData([0], [0], [0]), GraphData([0], [0], [0])]

def init_gui(ctx):
    for x in range(0, 3):
        set_legend(ctx, x)
    draw_data(ctx)

    #Setting navigation toolbar
    nav_tool = NavigationToolbar(ctx.canvas, ctx.root)
    nav_tool.place_configure(bordermode="inside")

    #Seting menu
    menu = Menu(ctx.root)
    menu.add_command(label="Start", command=lambda: start_animator_event(ctx))
    menu.add_command(label="Stop", command=lambda: stop_animator_event(ctx))
    menu.add_command(label="Clear", command=lambda: clear_graph_event(ctx))
    menu.add_command(label="Record", command=lambda: set_recorder_event(ctx))
    menu.add_command(label="Load", command=lambda: load_data_event(ctx))

    #Setting view menu layout
    viewmenu = Menu(menu)
    menu.add_cascade(label="View", menu=viewmenu)
    viewmenu.add_checkbutton(label="X", variable=ctx.x_show, command=lambda: view_set(ctx))
    viewmenu.add_checkbutton(label="Y", variable=ctx.y_show, command=lambda: view_set(ctx))
    viewmenu.add_checkbutton(label="Z", variable=ctx.z_show, command=lambda: view_set(ctx))
    viewmenu.add_checkbutton(label="Show full graph", variable=ctx.show_full_graph,\
    command=lambda: discard_overflowing_points(ctx))

    #TODO: Implement framerate, zooming, data source.
    menu.add_command(label="Settings", command=lambda: settings_widget_show_event(ctx))
    menu.add_command(label="Abort", command=lambda: exit(0))
    ctx.root.config(menu=menu)
    ctx.status = Label(ctx.root, text="Idling...")
    ctx.status.pack()

CTX = Context()
CTX.graphs = init_graph_data() #Init data arrays.
init_gui(CTX)
CTX.reader = init_reader(CTX)
CTX.root.mainloop()
