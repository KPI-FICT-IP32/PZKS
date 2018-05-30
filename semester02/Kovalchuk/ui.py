import sys
import tkinter as tk

from collections import defaultdict
from tkinter import simpledialog, filedialog, messagebox, ttk

import dot_parser

from graph import Graph as TGraph
from system_graph import Graph as SGraph
from task_graph import (
    TaskGraph,
    alg_diff_late_early,
    alg_critical_path_start,
    alg_node_connectivity,
)
from reader import save, read_task_graph_file, read_system_graph_file
from validators import (
    validate_acyclic,
    validate_not_empty,
    validate_connected,
    ValidationError,
)


class SystemGraphEditor(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.g = SGraph()
        self.init_window()

    def init_window(self):
        self.init_editor()
        self.pack(fill=tk.BOTH, expand=True)

    def init_menu(self, root):
        menu = tk.Menu(self)
        file_menu = tk.Menu(menu)
        file_menu.add_command(label='New system', command=self.on_new_clicked)
        file_menu.add_command(label='Open', command=self.on_open_clicked)
        file_menu.add_command(label='Save', command=self.on_save_clicked)
        file_menu.add_separator()
        file_menu.add_command(label='Exit', command=sys.exit)

        menu.add_cascade(label='File', menu=file_menu)

        actions_menu = tk.Menu(menu)
        actions_menu.add_command(label='Validate system graph',
                                 command=self.on_validate_clicked)
        menu.add_cascade(label='System Actions', menu=actions_menu)
        root.config(menu=menu)

    def init_editor(self):
        self.canvas = tk.Canvas(master=self, bg='white')
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind('<Button-3>', self.on_canvas_right_click)

        self.__node_links = defaultdict(set)
        self.__editor_mode = 'draw'
        self.__connect_source = None
        self.__conn = None

        def show_connection(event):
            if self.__editor_mode == 'draw':
                return
            x, y = event.x, event.y
            (_, node) = self.__connect_source
            (x1, y1, x2, y2) = self.canvas.coords(node)
            cx, cy = ((x1 + x2) / 2), ((y1 + y2) / 2)
            x = x - 2 if cx < x else x + 2
            y = y - 2 if cy < y else y + 2
            if self.__conn is not None:
                self.canvas.delete(self.__conn)
            self.__conn = self.canvas.create_line(cx, cy, x, y)
        self.canvas.bind('<Motion>', show_connection)

    def on_new_clicked(self):
        del self.g
        self.g = SGraph()
        self.canvas.delete(tk.ALL)
        self.__node_links = defaultdict(set)
        self.__editor_mode = 'draw'
        self.__connect_source = None
        self.__conn = None

    def on_open_clicked(self):
        filename = filedialog.askopenfilename(defaultextension='.dot')
        if filename is None:
            return
        self.on_new_clicked()
        del self.g
        self.g = read_system_graph_file(filename)
        generated_dot = (
            dot_parser
            .parse_dot_data(str(self.g))[0]
            .create_dot()
            .decode('utf-8')
        )
        dot_data = dot_parser.parse_dot_data(generated_dot)[0]
        _, gh = map(float, dot_data.get_bb()[len('"0,0,'):-1].split(','))
        nodes = [
            (int(node.get_name()[len('Node_'):]), node)
            for node in dot_data.get_nodes()
            if node.get_name().startswith('Node_')
        ]
        node_gnode = {}
        for (node_id, node) in nodes:
            weight = self.g[node_id].weight
            coordinates = tuple(map(float, node.get_pos()[1:-1].split(',')))
            coordinates = (coordinates[0], gh - coordinates[1])
            node_gnode[node_id] = self.draw_task_node(coordinates, weight,
                                                      node_id)
        for node in self.g:
            for edge in node.connections_out:
                self.draw_connection(
                    (edge.source.id, node_gnode[edge.source.id]),
                    (edge.target.id, node_gnode[edge.target.id]),
                )

    def on_save_clicked(self):
        filename = filedialog.asksaveasfilename(defaultextension='.dot')
        if not filename:
            return
        save(self.g, filename)

    def on_canvas_right_click(self, event):
        canvas_menu = tk.Menu(master=self.master, tearoff=0)
        coordinates = (event.x, event.y)
        canvas_menu.add_command(
            label='Add Processor...',
            command=lambda: self.on_add_task_clicked(coordinates)
        )
        canvas_menu.add_separator()
        canvas_menu.add_command(label='Cancel', command=lambda: None)
        canvas_menu.post(event.x_root, event.y_root)

    def on_add_task_clicked(self, coordinates):
        weight = simpledialog.askinteger(
            title='Enter processor performance',
            prompt='Enter processor performance',
            minvalue=1, maxvalue=100,
        )
        if weight is not None:
            self.add_task_node(coordinates, weight)

    def on_validate_clicked(self):
        try:
            validate_not_empty(self.g)
            validate_connected(self.g)
        except ValidationError as e:
            messagebox.showerror('Invalid system graph', str(e))
        else:
            messagebox.showinfo('System graph valid', 'OK!')

    def switch_to_draw(self):
        self.__editor_mode = 'draw'
        self.canvas.delete(self.__conn)
        self.__conn = None
        self.__connect_source = None

    def connect_nodes(self, source, target):
        source_id, source_node = source
        target_id, target_node = target
        self.g.connect(source_id, target_id)
        self.draw_connection(source, target)

    def draw_connection(self, source, target):
        source_id, source_node = source
        target_id, target_node = target
        (sx1, sy1, sx2, sy2) = self.canvas.coords(source_node)
        (tx1, ty1, tx2, ty2) = self.canvas.coords(target_node)
        sx, sy = (sx1 + sx2) / 2, (sy1 + sy2) / 2
        tx, ty = (tx1 + tx2) / 2, (ty1 + ty2) / 2

        conn = self.canvas.create_line(sx, sy, tx, ty, width=5)
        self.canvas.tag_lower(conn)
        self.__node_links[source_id].add(conn)
        self.__node_links[target_id].add(conn)

        def disconnect(evt):
            self.g.disconnect(source_id, target_id)
            self.canvas.delete(conn)
            self.__node_links[source_id].discard(conn)
            self.__node_links[target_id].discard(conn)

        self.canvas.tag_bind(conn, '<Button-3>', disconnect)

    def add_task_node(self, coordinates, weight):
        node_id = self.g.add_node(weight)
        self.draw_task_node(coordinates, weight, node_id)

    def draw_task_node(self, coordinates, weight, node_id):
        r = 20
        (x, y) = coordinates
        node = self.canvas.create_oval(x - r, y - r, x + r, y + r,
                                       fill='white', outline='red')
        label = self.canvas.create_text(x, y, text=f'{node_id} ({weight})')

        def delete():
            self.g.del_node(node_id)
            self.canvas.delete(node)
            self.canvas.delete(label)
            for conn in self.__node_links[node_id]:
                self.canvas.delete(conn)

        def connect():
            self.__connect_source = (node_id, node)
            self.__editor_mode = 'connect'

        def on_node_clicked(event):
            if self.__editor_mode == 'draw':
                node_menu = tk.Menu(master=self.master, tearoff=0)
                node_menu.add_command(label='Connect', command=connect)
                node_menu.add_command(label='Delete', command=delete)
                node_menu.add_separator()
                node_menu.add_command(label='Cancel', command=lambda: None)
                node_menu.post(event.x_root, event.y_root)
            elif self.__editor_mode == 'connect':
                if self.__connect_source != (node_id, node):
                    self.connect_nodes(self.__connect_source, (node_id, node))
                return self.switch_to_draw()
            else:
                assert False
        self.canvas.tag_bind(node, '<Button-1>', on_node_clicked)
        self.canvas.tag_bind(label, '<Button-1>', on_node_clicked)
        return node


class TaskGraphEditor(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.g = TGraph()
        self.init_window()

    def init_window(self):
        self.init_editor()
        self.pack(fill=tk.BOTH, expand=True)

    def init_menu(self, root):
        menu = tk.Menu(self)
        file_menu = tk.Menu(menu)
        file_menu.add_command(label='New tasks', command=self.on_new_clicked)
        file_menu.add_command(label='Open', command=self.on_open_clicked)
        file_menu.add_command(label='Save', command=self.on_save_clicked)
        file_menu.add_separator()
        file_menu.add_command(label='Exit', command=sys.exit)

        menu.add_cascade(label='File', menu=file_menu)

        actions_menu = tk.Menu(menu)
        actions_menu.add_command(label='Validate tasks graph',
                                 command=self.on_validate_clicked)
        actions_menu.add_separator()
        for alg in [
            alg_diff_late_early,
            alg_node_connectivity,
            alg_critical_path_start
        ]:
            actions_menu.add_command(
                label=alg.__doc__,
                command=lambda: self.on_task_queue_clicked(alg)
            )
        menu.add_cascade(label='Task Actions', menu=actions_menu)
        root.config(menu=menu)

    def init_editor(self):
        self.canvas = tk.Canvas(master=self, bg='white')
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind('<Button-3>', self.on_canvas_right_click)

        self.__node_links = defaultdict(set)
        self.__editor_mode = 'draw'
        self.__connect_source = None
        self.__conn = None

        def show_connection(event):
            if self.__editor_mode == 'draw':
                return
            x, y = event.x, event.y
            (_, node) = self.__connect_source
            (x1, y1, x2, y2) = self.canvas.coords(node)
            cx, cy = ((x1 + x2) / 2), ((y1 + y2) / 2)
            x = x - 2 if cx < x else x + 2
            y = y - 2 if cy < y else y + 2
            if self.__conn is not None:
                self.canvas.delete(self.__conn)
            self.__conn = self.canvas.create_line(cx, cy, x, y, arrow=tk.LAST)
        self.canvas.bind('<Motion>', show_connection)

    def on_new_clicked(self):
        del self.g
        self.g = TGraph()
        self.canvas.delete(tk.ALL)
        self.__node_links = defaultdict(set)
        self.__editor_mode = 'draw'
        self.__connect_source = None
        self.__conn = None

    def on_open_clicked(self):
        filename = filedialog.askopenfilename(defaultextension='.dot')
        if filename is None:
            return
        self.on_new_clicked()
        del self.g
        self.g = read_task_graph_file(filename)
        generated_dot = (
            dot_parser
            .parse_dot_data(str(self.g))[0]
            .create_dot()
            .decode('utf-8')
        )
        dot_data = dot_parser.parse_dot_data(generated_dot)[0]
        _, gh = map(float, dot_data.get_bb()[len('"0,0,'):-1].split(','))
        nodes = [
            (int(node.get_name()[len('Node_'):]), node)
            for node in dot_data.get_nodes()
            if node.get_name().startswith('Node_')
        ]
        node_gnode = {}
        for (node_id, node) in nodes:
            weight = self.g[node_id].weight
            coordinates = tuple(map(float, node.get_pos()[1:-1].split(',')))
            coordinates = (coordinates[0], gh - coordinates[1])
            node_gnode[node_id] = self.draw_task_node(coordinates, weight,
                                                      node_id)
        for node in self.g:
            for edge in node.connections_out:
                self.draw_connection(
                    (edge.source.id, node_gnode[edge.source.id]),
                    (edge.target.id, node_gnode[edge.target.id]),
                    edge.weight
                )

    def on_save_clicked(self):
        filename = filedialog.asksaveasfilename(defaultextension='.dot')
        if filename is None:
            return
        save(self.g, filename)

    def on_canvas_right_click(self, event):
        canvas_menu = tk.Menu(master=self.master, tearoff=0)
        coordinates = (event.x, event.y)
        canvas_menu.add_command(
            label='Add Task...',
            command=lambda: self.on_add_task_clicked(coordinates)
        )
        canvas_menu.add_separator()
        canvas_menu.add_command(label='Cancel', command=lambda: None)
        canvas_menu.post(event.x_root, event.y_root)

    def on_add_task_clicked(self, coordinates):
        weight = simpledialog.askinteger(
            title='Enter task weight',
            prompt='Enter task weight',
            minvalue=1, maxvalue=100,
        )
        if weight is not None:
            self.add_task_node(coordinates, weight)

    def on_validate_clicked(self):
        try:
            validate_not_empty(self.g)
            validate_acyclic(self.g)
        except ValidationError as e:
            messagebox.showerror('Invalid task graph', str(e))
        else:
            messagebox.showinfo('Task graph valid', 'OK!')

    def on_task_queue_clicked(self, alg):
        tg = TaskGraph(self.g)
        queue = tg.prioritize_nodes(alg)
        messagebox.showinfo(alg.__doc__, f'{queue}')

    def switch_to_draw(self):
        self.__editor_mode = 'draw'
        self.canvas.delete(self.__conn)
        self.__conn = None
        self.__connect_source = None

    def connect_nodes(self, source, target, weight):
        source_id, source_node = source
        target_id, target_node = target
        self.g.connect(source_id, target_id, weight)
        self.draw_connection(source, target, weight)

    def draw_connection(self, source, target, weight):
        source_id, source_node = source
        target_id, target_node = target
        (sx1, sy1, sx2, sy2) = self.canvas.coords(source_node)
        (tx1, ty1, tx2, ty2) = self.canvas.coords(target_node)
        sx, sy = (sx1 + sx2) / 2, (sy1 + sy2) / 2
        tx, ty = (tx1 + tx2) / 2, (ty1 + ty2) / 2

        conn = self.canvas.create_line(sx, sy, tx, ty, arrow=tk.LAST)
        conn_label = self.canvas.create_text((sx + tx) / 2, (sy + ty) / 2,
                                             text=weight)
        self.__node_links[source_id].add((conn, conn_label))
        self.__node_links[target_id].add((conn, conn_label))

        def disconnect(evt):
            self.g.disconnect(source_id, target_id)
            self.canvas.delete(conn)
            self.canvas.delete(conn_label)
            self.__node_links[source_id].discard((conn, conn_label))
            self.__node_links[target_id].discard((conn, conn_label))

        self.canvas.tag_bind(conn, '<Button-3>', disconnect)
        self.canvas.tag_bind(conn_label, '<Button-3>', disconnect)

    def add_task_node(self, coordinates, weight):
        node_id = self.g.add_node(weight)
        self.draw_task_node(coordinates, weight, node_id)

    def draw_task_node(self, coordinates, weight, node_id):
        r = 20
        (x, y) = coordinates
        node = self.canvas.create_oval(x - r, y - r, x + r, y + r,
                                       fill='white', outline='red')
        label = self.canvas.create_text(x, y, text=f'{node_id} ({weight})')

        def delete():
            self.g.del_node(node_id)
            self.canvas.delete(node)
            self.canvas.delete(label)
            for (conn, conn_label) in self.__node_links[node_id]:
                self.canvas.delete(conn)
                self.canvas.delete(conn_label)

        def connect():
            self.__connect_source = (node_id, node)
            self.__editor_mode = 'connect'

        def on_node_clicked(event):
            if self.__editor_mode == 'draw':
                node_menu = tk.Menu(master=self.master, tearoff=0)
                node_menu.add_command(label='Connect', command=connect)
                node_menu.add_command(label='Delete', command=delete)
                node_menu.add_separator()
                node_menu.add_command(label='Cancel', command=lambda: None)
                node_menu.post(event.x_root, event.y_root)
            elif self.__editor_mode == 'connect':
                if self.__connect_source == (node_id, node):
                    return self.switch_to_draw()
                conn_weight = simpledialog.askinteger(
                    title='Enter connection weight',
                    prompt='Enter connection weight',
                    minvalue=1, maxvalue=100
                )
                if conn_weight:
                    self.connect_nodes(self.__connect_source, (node_id, node),
                                       conn_weight)
                    return self.switch_to_draw()
                else:
                    return self.switch_to_draw()
            else:
                assert False
        self.canvas.tag_bind(node, '<Button-1>', on_node_clicked)
        self.canvas.tag_bind(label, '<Button-1>', on_node_clicked)
        return node


class App(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.init_window()

    def init_window(self):
        self.pack(fill=tk.BOTH, expand=True)
        self.tabs = ttk.Notebook(self, name='tabs')
        self.tabs.pack(fill=tk.BOTH, expand=True, padx=2, pady=3)
        self.tasks_editor = TaskGraphEditor(self.tabs)
        self.system_editor = SystemGraphEditor(self.tabs)
        self.tabs.add(self.tasks_editor, text='Tasks Graph')
        self.tabs.add(self.system_editor, text='System Graph')

        self.tabs.bind('<<NotebookTabChanged>>', self.on_tab_change)

    def on_tab_change(self, event):
        tab = event.widget.winfo_children()[event.widget.index("current")]
        tab.init_menu(self.master)


if __name__ == '__main__':
    root = tk.Tk()
    root.geometry('640x480')
    app = App(root)
    root.mainloop()
