import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk
import ramalama

class LLMChatApp(Gtk.Window):
    def __init__(self):
        super().__init__(title="Bob")
        self.set_default_size(800, 600)

        # Use a Paned container to divide left/right
        paned = Gtk.Paned.new(Gtk.Orientation.HORIZONTAL)
        self.add(paned)

        # Left side: conversation list
        self.conversation_list = Gtk.ListBox()
        left_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        left_box.pack_start(self.conversation_list, True, True, 0)

        add_button = Gtk.Button(label="Add")
        delete_button = Gtk.Button(label="Delete")
        button_box = Gtk.Box(spacing=6)
        button_box.pack_start(add_button, True, True, 0)
        button_box.pack_start(delete_button, True, True, 0)
        left_box.pack_start(button_box, False, False, 6)

        left_frame = Gtk.Frame(label="Conversations")
        left_frame.add(left_box)
        paned.pack1(left_frame, resize=True, shrink=False)

        # Right side: conversation view
        right_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        self.chat_view = Gtk.TextView()
        self.chat_view.set_editable(False)
        self.chat_buffer = self.chat_view.get_buffer()
        chat_scroller = Gtk.ScrolledWindow()
        chat_scroller.add(self.chat_view)
        right_box.pack_start(chat_scroller, True, True, 0)

        prompt_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.prompt_entry = Gtk.Entry()
        send_button = Gtk.Button(label="Enter")
        send_button.connect("clicked", self.on_send_clicked)
        prompt_box.pack_start(self.prompt_entry, True, True, 0)
        prompt_box.pack_start(send_button, False, False, 0)
        right_box.pack_start(prompt_box, False, False, 6)

        right_frame = Gtk.Frame(label="Chat")
        right_frame.add(right_box)
        paned.pack2(right_frame, resize=True, shrink=False)

        # Set initial pane position (40/60 split)
        self.connect("realize", lambda w: paned.set_position(int(self.get_allocated_width() * 0.4)))

    def on_send_clicked(self, button):
        prompt = self.prompt_entry.get_text()
        if prompt:
            self.chat_buffer.insert_at_cursor(f"You: {prompt}\n")
            self.prompt_entry.set_text("")
            # Dummy reply for now
            self.chat_buffer.insert_at_cursor("Bot: [thinking...]\n")
            # TODO: Use ramalama to respond

win = LLMChatApp()
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()
