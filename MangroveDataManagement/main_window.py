from tkinter import Tk, Label, StringVar, OptionMenu, Entry, BooleanVar, Checkbutton, Button, messagebox
from tkcalendar import DateEntry
from typing import Any, Callable, Dict, List

FONT_NAME = 'Segoe UI'
FONT_SIZE = 18
FONT = (FONT_NAME, FONT_SIZE)

class MainWindow(Tk):
    def __init__(self, config: Dict[str, Any], removable_drives: List[str], fixed_drives: List[str], copy_clicked_callback: Callable[[Dict[str, Any]], None]):
        Tk.__init__(self)
        self._config = config
        self._copy_clicked_callback = copy_clicked_callback

        self.title('Data Organizer')
        self.config(bg='black')
        self.grid_columnconfigure(1, weight=1)

        _, _, self._source_drive_variable = self._add_dropdown('Source Drive', 0, removable_drives, default=self._get_value_or_default(config, 'source_drive'))
        _, _, self._target_drive_variable = self._add_dropdown('Target Drive', 1, fixed_drives, default=self._get_value_or_default(config, 'target_drive'))
        _, self._aircraft_entry = self._add_entry('Aircraft', 2, default=self._get_value_or_default(config, 'aircraft'))
        _, self._country_entry = self._add_entry('Country', 3, default=self._get_value_or_default(config, 'country'))
        _, self._region_entry = self._add_entry('Region', 4, default=self._get_value_or_default(config, 'region'))
        _, self._date_entry = self._add_date('Flight Date', 5)
        _, self._site_entry = self._add_entry('Site', 6, default=self._get_value_or_default(config, 'site'))
        _, self._flight_entry = self._add_entry('Flight', 7)
        
        copy_button = Button(self, text='Copy', command=self._copy_command)
        copy_button.grid(row=9, column=1, pady=(10, 10))
        copy_button.config(bg='black', fg='white', font=FONT)

    def _get_value_or_default(self, config: Dict[str, Any], key: str, default=None):
        return config[key] if key in config else default

    def _fix_input(self, input: str):
        return input.lower().replace(' ', '-')

    def _copy_command(self):
        self._config['source_drive'] = self._source_drive_variable.get()
        self._config['target_drive'] = self._target_drive_variable.get()
        self._config['aircraft'] = self._aircraft_entry.get()
        self._config['country'] = self._fix_input(self._country_entry.get())
        self._config['region'] = self._fix_input(self._region_entry.get())
        self._config['date'] = self._date_entry.get_date()
        self._config['site'] = self._fix_input(self._site_entry.get())
        self._config['flight'] = self._fix_input(self._flight_entry.get())

        if not self._config['aircraft'] or not self._config['country'] or not self._config['region'] or not self._config['date'] or not self._config['site'] or not self._config['flight']:
            messagebox.showerror(title='Missing data', message='Please ensure all fields have been filled out and try again.')
            return

        self._copy_clicked_callback(self._config)

    def get_value_or_default(self, config: Dict[str, Any], key: str, default=None):
        return config[key] if key in config else default

    def _add_dropdown(self, label: str, row: int, data: List[str], default=None):
        label = Label(self, text=label)
        label.grid(row=row, column=0)
        label.config(bg='black', fg='white', font=FONT)

        variable = StringVar()
        if default and default in data:
            variable.set(default)
        elif data:
            variable.set(data[0])

        dropdown = OptionMenu(self, variable, *data)
        dropdown.grid(row=row, column=1, sticky='we', pady=(10, 10))
        dropdown.config(bg='black', fg='white', font=FONT)

        return label, dropdown, variable

    def _add_entry(self, label: str, row: int, default=None):
        label = Label(self, text=label)
        label.grid(row=row, column=0)
        label.config(bg='black', fg='white', font=FONT)

        entry = Entry(self)
        entry.grid(row=row, column=1, sticky='we', pady=(10, 10))
        entry.config(bg='black', fg='white', insertbackground='white', font=FONT)

        if default:
            entry.insert(0, default)

        return label, entry

    def _add_date(self, label: str, row: int, default=None):
        label = Label(self, text=label)
        label.grid(row=row, column=0)
        label.config(bg='black', fg='white', font=FONT)

        date = DateEntry(self, selectmode='day')
        date.grid(row=row, column=1, sticky='we', pady=(10, 10))
        date.config(font=FONT)

        if default:
            date.set_date(default)

        return label, date

    def _add_checkbox(self, label: str, row:int, default=None):
        variable = BooleanVar()
        if default:
            variable.set(default)

        checkbox = Checkbutton(self, text=label,variable=variable, onvalue=True, offvalue=False)
        checkbox.grid(row=row, column=0, pady=(10, 10))
        checkbox.config(bg='black', fg='white', selectcolor='black', activebackground='black', activeforeground='white', font=FONT)

        return checkbox, variable