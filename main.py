import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib
import subprocess
import requests
import time
import threading

RAMALAMA_URL = "http://127.0.0.1:8080/v1/chat/completions"

class LLMChatApp(Gtk.Window):
    def __init__(self):
        super().__init__(title="Bob")
        self.set_default_size(800, 600)

        self.ramalama_proc = subprocess.Popen(
            ["ramalama", "serve", "granite3-moe"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        self.wait_for_server()

        self.conversations = []
        self.current_convo_index = -1

        # Create a vertical box to hold the menu bar, paned widget, and the status bar
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        menu_bar = self.create_menu_bar()

        # Add the menu bar to the main box
        main_box.pack_start(menu_bar, False, False, 0)
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        main_box.pack_start(separator, False, False, 0)

        paned = Gtk.Paned.new(Gtk.Orientation.HORIZONTAL)
        main_box.pack_start(paned, True, True, 0)

        self.conversation_list = Gtk.ListBox()
        self.conversation_list.connect("row-selected", self.on_convo_selected)

        left_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        left_box.pack_start(self.conversation_list, True, True, 0)

        add_button = Gtk.Button(label="Add")
        delete_button = Gtk.Button(label="Delete")
        add_button.connect("clicked", self.add_conversation)
        delete_button.connect("clicked", self.delete_conversation)

        button_box = Gtk.Box(spacing=6)
        button_box.pack_start(add_button, True, True, 0)
        button_box.pack_start(delete_button, True, True, 0)
        left_box.pack_start(button_box, False, False, 6)

        left_frame = Gtk.Frame(label="Conversations")
        left_frame.add(left_box)
        paned.pack1(left_frame, resize=True, shrink=False)

        right_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        self.chat_view = Gtk.TextView()
        self.chat_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.chat_view.set_editable(False)
        self.chat_buffer = self.chat_view.get_buffer()
        chat_scroller = Gtk.ScrolledWindow()
        chat_scroller.add(self.chat_view)
        right_box.pack_start(chat_scroller, True, True, 0)

        prompt_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.prompt_entry = Gtk.Entry()
        self.prompt_entry.connect("activate", self.on_send_clicked)
        send_button = Gtk.Button(label="Enter")
        send_button.connect("clicked", self.on_send_clicked)
        prompt_box.pack_start(self.prompt_entry, True, True, 0)
        prompt_box.pack_start(send_button, False, False, 0)
        right_box.pack_start(prompt_box, False, False, 6)

        right_frame = Gtk.Frame(label="Chat")
        right_frame.add(right_box)
        paned.pack2(right_frame, resize=True, shrink=False)

        # Create default conversation
        self.add_conversation(None)
        self.conversation_list.select_row(self.conversation_list.get_row_at_index(0))  # Focus on the first conversation

        # Add a status bar at the bottom
        self.statusbar = Gtk.Statusbar()
        self.statusbar_context_id = self.statusbar.get_context_id("Status")
        self.statusbar.push(self.statusbar_context_id, "Checking ramalama status...")
        main_box.pack_start(self.statusbar, False, False, 0)

        # Add the main box to the window
        self.add(main_box)

        self.connect("realize", lambda w: paned.set_position(int(self.get_allocated_width() * 0.25)))
        self.connect("destroy", self.on_destroy)
        self.show_all()

        # Start monitoring ramalama status
        GLib.timeout_add(1000, self.update_ramalama_status)  # Check status every 1000 ms (1 second)

    def create_menu_bar(self):
        # Create the menu bar
        menu_bar = Gtk.MenuBar()

        # Create the "File" menu
        file_menu = Gtk.Menu()
        file_item = Gtk.MenuItem(label="File")
        file_item.set_submenu(file_menu)

        # Add options to the "File" menu
        new_item = Gtk.MenuItem(label="New")
        open_item = Gtk.MenuItem(label="Open")
        exit_item = Gtk.MenuItem(label="Exit")
        exit_item.connect("activate", self.on_exit_clicked)
        file_menu.append(new_item)
        file_menu.append(open_item)
        file_menu.append(exit_item)

        # Create the "Edit" menu
        edit_menu = Gtk.Menu()
        edit_item = Gtk.MenuItem(label="Edit")
        edit_item.set_submenu(edit_menu)

        # Add options to the "Edit" menu
        undo_item = Gtk.MenuItem(label="Undo")
        redo_item = Gtk.MenuItem(label="Redo")
        edit_menu.append(undo_item)
        edit_menu.append(redo_item)

        # Create the "Model" menu
        model_menu = Gtk.Menu()
        model_item = Gtk.MenuItem(label="Model")
        model_item.set_submenu(model_menu)

        # Create the "Help" menu
        help_menu = Gtk.Menu()
        help_item = Gtk.MenuItem(label="Help")
        help_item.set_submenu(help_menu)

        # Add the menus to the menu bar
        menu_bar.append(file_item)
        menu_bar.append(edit_item)
        menu_bar.append(model_item)
        menu_bar.append(help_item)
        return menu_bar


    def wait_for_server(self):
        print("Waiting for ramalama to come up")
        for _ in range(30):
            try:
                r = requests.get("http://127.0.0.1:8080/")
                if r.ok:
                    print("success: ramalama up")
                    return
            except requests.ConnectionError:
                time.sleep(1)
        print("Ramalama server did not start in time.")
        exit(1)

        
        # Start monitoring ramalama status
        GLib.timeout_add(1000, self.update_ramalama_status)  # Check status every 1000 ms (1 second)

    def update_ramalama_status(self):
        """Periodically check and update the status of ramalama."""
        try:
            response = requests.get("http://127.0.0.1:8080/")
            if response.ok:
                self.statusbar.push(self.statusbar_context_id, "Ramalama is running.")
            else:
                self.statusbar.push(self.statusbar_context_id, "Ramalama is not responding!")
        except requests.ConnectionError:
            self.statusbar.push(self.statusbar_context_id, "Ramalama is down!")
        return True  # Return True to keep the timeout running

    def on_destroy(self, *args):
        if self.ramalama_proc:
            self.ramalama_proc.terminate()
            self.ramalama_proc.wait()

    def add_conversation(self, button):
        self.conversations.append([])
        row = Gtk.ListBoxRow()
        label = Gtk.Label(label=f"Conversation {len(self.conversations)}", xalign=0)
        row.add(label)
        self.conversation_list.add(row)
        self.conversation_list.show_all()
        self.conversation_list.select_row(row)

    def delete_conversation(self, button):
        selected_row = self.conversation_list.get_selected_row()
        if selected_row:
            index = selected_row.get_index()
            del self.conversations[index]
            self.conversation_list.remove(selected_row)
            self.chat_buffer.set_text("")
            self.current_convo_index = -1

    def on_convo_selected(self, listbox, row):
        if row:
            self.current_convo_index = row.get_index()
            self.render_conversation()

    def render_conversation(self):
        self.chat_buffer.set_text("")
        if self.current_convo_index >= 0:
            messages = self.conversations[self.current_convo_index]
            for msg in messages:
                who = "You" if msg["role"] == "user" else "Bob"
                self.chat_buffer.insert_at_cursor(f"{who}: {msg['content']}\n")

    def on_send_clicked(self, button):
        prompt = self.prompt_entry.get_text().strip()
        if not prompt or self.current_convo_index < 0:
            return

        convo = self.conversations[self.current_convo_index]
        convo.append({"role": "user", "content": prompt})
        self.render_conversation()
        self.prompt_entry.set_text("")
        self.chat_buffer.insert_at_cursor("Bob: [thinking...]\n")

        threading.Thread(target=self.fetch_response, args=(convo,), daemon=True).start()

    def fetch_response(self, convo):
        try:
            response = requests.post(RAMALAMA_URL, json={"messages": convo})
            if response.ok:
                print(response.text)
                try:
                    message = response.json()["choices"][0]["message"]["content"]
                    if not message:
                      message = "[No response]"
                except:
                    message = "[No response]"
                convo.append({"role": "assistant", "content": message})
            else:
                convo.append({"role": "assistant", "content": "[Error from server]"})
                print(response)
        except Exception as e:
            convo.append({"role": "assistant", "content": f"[Exception: {e}]"})

        # Update chat view on the main thread
        GLib.idle_add(self.render_conversation)

    def on_exit_clicked(self, widget):
        """Handle the Exit menu item."""
        self.destroy()
win = LLMChatApp()
Gtk.main()

