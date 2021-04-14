import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
from tkinter import simpledialog
import pyperclip
import random
import re
import pickle
import sys

# yes this code is very shitty but it works, ok?
# if you notice anything strange lmk at thalea@uw.edu

# default graded and not graded categories

DEFAULT_CATEGORIES = ["Behavior",
                 "Structure & Design",
                 "Use of Language Features",
                 "Documentation & Readability"]

DEFAULT_NOT_GRADED = ["Notes (not graded)"]

DEFAULT_ABBREVIATIONS = {"Behavior" : "B",
                 "Structure & Design" : "SD",
                 "Use of Language Features" : "UOLF",
                 "Documentation & Readability" : "DR",
                 "Notes (not graded)" : "NOTE"}

# the grades
GRADES = ["E", "S", "N", "U"]

HEADING = "## <category>: **<grade>**\n"
HEADING_NOT_GRADED = "## <category>:\n"

# Mistake bullet points
MISTAKE_SINGULAR = "* **Line <lines>**: <desc>\n"
MISTAKE_PLURAL = "* **Lines <lines>**: <desc>\n"
MISTAKE_LINE_TEXT = "* **<lines>**: <desc>\n"
MISTAKE_ONLY_DESC = "* <desc>\n"
NO_MISTAKES = ["* Perfect, great job!!\n",
                "* Awesome work!\n",
                "* Nice job!!\n",
                "* Great job!!!\n",
                "* Well done!!\n",
                "* Perfect!!\n"]

DEFAULT_GENERAL = [
    ["Great work, <name>!!",
     "Good work, <name>!",
     "Nice work, <name>!!"],
    ["I've left some feedback on how to improve your **SOMETHING UNIQUE**, be sure to take a look!!",
     "I've left some annotations with advice on how to improve your **SOMETHING UNIQUE**, be sure to check it out!!"],
    ["As always, let me know if you have any questions at all (my email is [<email>](mailto:<email>))! Keep it up!!",
     "As always, if you have any questions feel free to ask (my email is [<email>](mailto:<email>))!! Keep it up!"]
]

DEFAULT_PERFECT = "Perfect, <name>!! Keep it up!!"

DEFAULT_POOR = ("Good start on this assignment <name>! I left feedback that will hopefully help," + 
          " but if you feel stuck I recommend going to support hours. Let me know if you have" +
          " any questions at all about your feedback (my email is [<email>](mailto:<email>)). You got this!!")

MAC = 'darwin' in sys.platform
MAC_BG_COLOR = "#ececeb"

class GradingAssistantModel:
    def __init__(self):
        self.view = None
        self.ta_email = "your_email@uw.edu"
        self.bank_filename = '' 
        self.assignments = []
        self.annotations = []
        self.mistakes = []
        self.perfect = DEFAULT_PERFECT
        self.poor = DEFAULT_POOR
        self.general = DEFAULT_GENERAL.copy()
        self.categories = DEFAULT_CATEGORIES.copy()
        self.not_graded_categories = DEFAULT_NOT_GRADED.copy()
        self.abbreviations = DEFAULT_ABBREVIATIONS.copy()
        self.reset_scoresheet()

    def add_view(self, view):
        self.view = view
        self.reset_scoresheet()

    def reset_scoresheet(self):
        self.category_grades = {}
        for category in self.categories:
            self.category_grades[category] = GRADES[0]
        self.mistakes = []
        self.student_name = ""
        if self.view:
            self.view.notify()

    def all_categories(self):
        return self.categories + self.not_graded_categories

    def graded(self):
        return self.categories

    def not_graded(self):
        return self.not_graded_categories

    def abbreviation(self, category):
        return self.abbreviations[category]

    def add_category(self, category, abbreviation, graded):
        if category not in self.all_categories():
            if graded:
                self.categories.append(category)
            else:
                self.not_graded_categories.append(category)
            self.abbreviations[category] = abbreviation
            self._calculate_grades()
            if self.view:
                self.view.notify()

    def edit_category(self, category, new_name, abbreviation, graded):
        if category in self.all_categories() and (new_name not in self.all_categories() or new_name == category):
            if category in self.categories and not graded:
                self.categories.remove(category)
                self.not_graded_categories.append(new_name)
            elif category in self.not_graded_categories and graded:
                self.not_graded_categories.remove(category)
                self.categories.append(new_name)
            elif category in self.categories:
                index = self.categories.index(category)
                self.categories.remove(category)
                self.categories.insert(index, new_name)
            else:
                index = self.not_graded_categories.index(category)
                self.not_graded_categories.remove(category)
                self.not_graded_categories.insert(index, new_name)
            del self.abbreviations[category]
            self.abbreviations[new_name] = abbreviation
            for annotation in self.annotations:
                assignment, notes, curr_cat, grade, description, annotation_text, tags = annotation
                if curr_cat == category:
                    index = self.annotations.index(annotation)
                    self.annotations.remove(annotation)
                    self.annotations.insert(index, (assignment, notes, new_name, grade,
                            description, annotation_text, tags))
            for mistake in self.mistakes:
                lines, curr_cat, grade, description = mistake
                if curr_cat == category:
                    index = self.mistakes.index(mistake)
                    self.mistakes.remove(mistake)
                    self.mistakes.insert(index, (lines, new_name, grade, description))
            self._calculate_grades()
            if self.view:
                self.view.notify()

    def remove_category(self, category):
        for mistake in reversed(self.mistakes):
            if mistake[1] == category:
                self.mistakes.remove(mistake)
        for annotation in reversed(self.annotations):
            if annotation[2] == category:
                self.annotations.remove(annotation)
        if category in self.categories:
            self.categories.remove(category)
            del self.category_grades[category]
        else:
            self.not_graded_categories.remove(category)
        del self.abbreviations[category]
        self._calculate_grades()
        if self.view:
            self.view.notify()

    def move_category(self, category, index):
        if category in self.categories and 0 <= index < len(self.categories):
            self.categories.remove(category)
            self.categories.insert(index, category)
        elif category in self.not_graded_categories and 0 <= index < len(self.not_graded_categories):
            self.not_graded_categories.remove(category)
            self.not_graded_categories.insert(index, category)
        if self.view:
            self.view.notify()

    def set_name(self, name):
        self.student_name = name
    
    def set_email(self, email):
        self.ta_email = email

    def add_mistake(self, lines, category, grade, description, index=None):
        if index:
            self.mistakes.insert(index, (lines, category, grade, description))
        else:
            self.mistakes.append((lines, category, grade, description))
            self.mistakes.sort(key = lambda x: x[3])
        self._calculate_grades()
        if self.view:
            self.view.notify()

    def remove_mistake(self, index):
        del self.mistakes[index]
        self._calculate_grades()
        if self.view:
            self.view.notify()        

    def _calculate_grades(self):
        for category in self.categories:
            grade = GRADES[0]
            for mistake in self.mistakes:
                if mistake[1] == category:
                    mistake_grade = mistake[2]
                    grade = GRADES[max(GRADES.index(grade), GRADES.index(mistake_grade))]
            self.category_grades[category] = grade

    def copy_scoresheet(self):
        markdown = ''
        no_mistakes_chosen = []
        score = 0
        for category in self.all_categories():
            heading = ''
            if category not in self.not_graded_categories:
                score += GRADES.index(self.category_grades[category])
                heading += HEADING.replace('<category>', category).replace('<grade>',
                    self.category_grades[category])
            else:
                heading += HEADING_NOT_GRADED.replace('<category>', category)
            count = 0
            mistakes = ''
            for lines, mistake_cat, grade, desc in self.mistakes:
                if mistake_cat == category:
                    count += 1
                    if re.search('[a-zA-Z]', lines.strip()):
                        mistakes += MISTAKE_LINE_TEXT.replace('<lines>',
                            lines.strip()).replace('<desc>', desc.strip())
                    elif ',' in lines or '-' in lines or ' ' in lines.strip(): 
                        mistakes += MISTAKE_PLURAL.replace('<lines>',
                            lines.strip()).replace('<desc>', desc.strip())
                    elif lines.strip():
                        mistakes += MISTAKE_SINGULAR.replace('<lines>',
                            lines.strip()).replace('<desc>', desc.strip())
                    else:
                        mistakes += MISTAKE_ONLY_DESC.replace('<desc>', desc.strip())

            if count == 0 and category not in self.not_graded_categories:
                # add random unique nice job message
                message = random.sample(NO_MISTAKES, 1)[0]
                while message in no_mistakes_chosen and len(no_mistakes_chosen) < len(NO_MISTAKES):
                    message = random.sample(NO_MISTAKES, 1)[0]
                no_mistakes_chosen.append(message)
                mistakes += message

            if category not in self.not_graded_categories or (category in self.not_graded_categories   and count > 0):
                markdown += heading + mistakes

        def format(message):
            return message.replace('<name>', self.student_name).replace('<email>', self.ta_email)

        markdown += '\n'
        # overall feedback
        if score == 0:
            markdown += format(self.perfect)
        elif score <= 5:
            overall = ''
            for sentence_option in self.general:
                overall += format(random.sample(sentence_option, 1)[0]) + ' '
            markdown += overall.strip()
        else:
            markdown += format(self.poor)

        pyperclip.copy(markdown)
        pyperclip.paste()

    def add_annotation(self, assignment, notes, category, grade,
                       description, annotation, tags, index=None):
        if index:
            self.annotations.insert(index, (assignment, notes, category, grade,
                                            description, annotation, tags))
        else:
            self.annotations.append((assignment, notes, category, grade, description, annotation, tags))
            self.annotations.sort(key = lambda x: x[4])
        if self.view:
            self.view.notify()

    def remove_annotation(self, index):
        del self.annotations[index]
        if self.view:
            self.view.notify() 

class GradingAssistantView:
    """
    A Graphical Interface for the Grading Assistant
    """

    class Scoresheet(ttk.Frame):

        class MistakeEditor(tk.Toplevel):
            def __init__(self, model, cancel_fn, master=None):
                super().__init__(master)
                self.title("Add Mistake")
                self.resizable(False, False)
                if MAC:
                    self['background'] = MAC_BG_COLOR
                self.model = model
                # line frame
                self.line_frame = ttk.Frame(self, width=100)
                self.line_frame.grid(row=1, column=0, columnspan=2, padx=2, pady=2, sticky='w')
                # line label
                self.line = ttk.Label(self.line_frame, text="Lines: ")
                self.line.pack(side='left')
                # line entry
                self.line_entry = ttk.Entry(self.line_frame)
                self.line_entry.config(width=44)
                self.line_entry.pack()
                # Category
                self.category_var = tk.StringVar(self.master)
                self.category = ttk.OptionMenu(self, self.category_var,
                    self.model.all_categories()[0], *(self.model.all_categories()))
                self.category.config(width=30)
                self.category.grid(row=0, column=0, padx=2, pady=2, sticky='ew')
                # Grade
                self.grade_var = tk.StringVar(self.master)
                self.grade = ttk.OptionMenu(self, self.grade_var, GRADES[0], *GRADES)
                self.grade.config(width=2)
                self.grade.grid(row=0, column=1, padx=2, pady=2, sticky='ew')
                # description entry
                self.desc_entry = tk.Text(self, height=10, width=50, wrap=tk.WORD)
                self.desc_entry.grid(row=2, column=0, columnspan=2, padx=2, pady=2, sticky='nsew')
                self.desc_entry.insert("1.0", "Description...")
                #button frame
                self.buttons = ttk.Frame(self)
                self.buttons.grid(row=3, column=0, columnspan=2, padx=9, pady=2, sticky='ew')
                # cancel button
                self.cancel_button = ttk.Button(self.buttons, text="Cancel")
                self.cancel_button.pack(side='left')
                def cancel():
                    cancel_fn()
                    self.destroy()
                self.cancel_button.bind("<Button>", lambda _: cancel())
                self.protocol("WM_DELETE_WINDOW", lambda: cancel())
                # add button
                self.add_button = ttk.Button(self.buttons, text="Add Mistake")
                self.add_button.pack(side='right')
                def add_mistake():
                    model.add_mistake(self.line_entry.get(), self.category_var.get(),
                            self.grade_var.get(), self.desc_entry.get("1.0", tk.END))
                    self.destroy()
                self.add_button.bind("<Button>", lambda _: add_mistake())

        def __init__(self, model, master=None):
            super().__init__(master)
            self.model = model
            self.master = master
            self.mistake_editor = None
            self.category_grades_frames = []
            self.add_grade_entries()
            self.add_selected_mistakes()

        def add_grade_entries(self):
            # frame
            self.grade_entries_frame = ttk.Frame(self)
            self.grade_entries_frame.grid(column=0, padx=2, pady=2, sticky='ew')
            # name frame
            self.name_frame = ttk.Frame(self.grade_entries_frame)
            self.name_frame.grid(row=0, sticky='nw', padx=2)
            # name label
            self.name = ttk.Label(self.name_frame, text="Name")
            self.name.pack(side="left")
            # name entry
            sv = tk.StringVar()
            sv.trace("w", lambda name, index, mode, sv=sv: self.model.set_name(sv.get()))
            self.name_entry = ttk.Entry(self.name_frame, textvariable=sv)
            self.name_entry.pack(padx=4)
            # category grades frame
            self.category_grades_frame = ttk.Frame(self.grade_entries_frame)
            self.category_grades_frame.grid(row=1)
            # category entries and labels
            self.add_category_grade_entries()
            # email entry
            email_sv = tk.StringVar()
            email_sv.trace("w",
                    lambda name, index, mode, sv=sv: self.model.set_email(email_sv.get()))
            self.email_entry = ttk.Entry(self.grade_entries_frame, textvariable=email_sv)
            self.email_entry.grid(row=2, column=0, padx=4, sticky='ew')
            # copy scoresheet button
            self.copy_scoresheet_button = \
                    ttk.Button(self.grade_entries_frame, text="Copy Scoresheet")
            self.copy_scoresheet_button.grid(row=2, column=1, padx=4, sticky='ew')
            self.unique = False
            def copy():
                if not self.unique:
                    tk.messagebox.showinfo(title="Uniqueness", 
                        message="Be sure to make your annotations and scoresheets unique to each student!")
                    self.unique = True
                self.model.copy_scoresheet()
            self.copy_scoresheet_button.bind("<Button>", lambda _: copy())
                

        def add_selected_mistakes(self):
            # frame
            self.mistakes_frame = ttk.Frame(self, width=350)
            self.mistakes_frame.grid(row=0, column=1, padx=2, pady=2, sticky='ew')
            # table
            self.mistakes_scrollbar = tk.Scrollbar(self.mistakes_frame)
            self.mistakes_scrollbar.grid(row=0, rowspan=2, column=1, padx=1, sticky='ns')
            self.mistakes_table = ttk.Treeview(self.mistakes_frame,
                    yscrollcommand=self.mistakes_scrollbar.set)
            self.mistakes_table["columns"] = ("#1", "#2", "#3")
            self.mistakes_table.column("#0", width=75, minwidth=50)
            self.mistakes_table.heading("#0", text="Category", anchor='w')
            self.mistakes_table.column("#1", width=100, minwidth=50)
            self.mistakes_table.heading("#1", text="Lines", anchor='w')
            self.mistakes_table.column("#2", width=275, minwidth=150)
            self.mistakes_table.heading("#2", text="Description", anchor='w')
            self.mistakes_table.column("#3", width=75, minwidth=75)
            self.mistakes_table.heading("#3", text="Grade", anchor='w')
            self.mistakes_table.grid(row=0, column=0, pady=2, rowspan=2)
            self.mistakes_scrollbar.config(command=self.mistakes_table.yview)
            # Add buttons
            self.mistakes_table_buttons = ttk.Frame(self.mistakes_frame)
            self.mistakes_table_buttons.grid(row=2, sticky='e')
            self.add_mistake_button = ttk.Button(self.mistakes_table_buttons)
            self.add_mistake_button["text"] = "+"
            self.add_mistake_button["width"] = 3
            self.add_mistake_button.bind("<Button>", lambda _: self.add_new_mistake())
            self.add_mistake_button.pack(side="right")
            self.edit_mistake_button = ttk.Button(self.mistakes_table_buttons)
            self.edit_mistake_button["text"] = "..."
            self.edit_mistake_button["width"] = 3
            self.edit_mistake_button.bind("<Button>", lambda _: self.edit_mistake())
            self.edit_mistake_button.pack(side="right")
            self.remove_mistake_button = ttk.Button(self.mistakes_table_buttons)
            self.remove_mistake_button["text"] = "-"
            self.remove_mistake_button["width"] = 3
            self.remove_mistake_button.bind("<Button>", lambda _: self.remove_mistake())
            self.remove_mistake_button.pack(side="right")

        def add_category_grade_entries(self):
            for frame in self.category_grades_frames:
                frame.destroy()
            self.category_grades_entries = {}
            row_index = 0
            if len(self.model.graded()) > 0:
                pady = max(4, (225 - 25 * len(self.model.graded())) / (2 * len(self.model.graded())))
                for category in self.model.graded():
                    frame = ttk.Frame(self.category_grades_frame)
                    frame.grid(row=row_index, padx=3, pady=pady, sticky='w')
                    entry = ttk.Entry(frame, width=3, justify=tk.CENTER, state='disabled')
                    entry.grid(row=0, column=0)
                    label = ttk.Label(frame,  text=category)
                    label.grid(row=0, column=1, padx=2)
                    self.category_grades_entries[category] = entry
                    self.category_grades_frames.append(frame)
                    row_index += 1

        def add_new_mistake(self):
            if self.mistake_editor:
                self.mistake_editor.destroy()
            def nothing():
                pass
            self.mistake_editor = self.MistakeEditor(self.model, nothing, self.master)
            if self.mistakes_table.selection():
                iid = self.mistakes_table.selection()[0]
                if iid in self.model.all_categories():
                    self.mistake_editor.category_var.set(iid)

        def edit_mistake(self):
            if self.mistakes_table.selection():
                item = self.mistakes_table.selection()[0]
                #index = self.mistakes_table.item(mistake, 'iid')
                if item not in self.model.all_categories():
                    index = int(item)
                    lines, category, grade, desc = self.model.mistakes[index]
                    if self.mistake_editor:
                        self.mistake_editor.destroy()
                    self.model.remove_mistake(index)
                    def cancel_fn():
                        self.model.add_mistake(lines, category, grade, desc, index)
                    self.mistake_editor = self.MistakeEditor(self.model,
                            cancel_fn,
                            self.master)
                    self.mistake_editor.category_var.set(category)
                    self.mistake_editor.grade_var.set(grade)
                    self.mistake_editor.line_entry.delete(0, tk.END)
                    self.mistake_editor.line_entry.insert(0, lines)
                    self.mistake_editor.desc_entry.delete("1.0", tk.END)
                    self.mistake_editor.desc_entry.insert("1.0", desc)

        def remove_mistake(self):
            if self.mistakes_table.selection():
                item = self.mistakes_table.selection()[0]
                if item not in self.model.all_categories():
                    index = int(item)
                    self.model.remove_mistake(index)

        def update(self):
            name = self.model.student_name
            self.name_entry.delete(0, tk.END)
            self.name_entry.insert(0, name)
            email = self.model.ta_email
            self.email_entry.delete(0, tk.END)
            self.email_entry.insert(0, email)
            total = ''
            opened = []
            for item in self.mistakes_table.get_children():
                if self.mistakes_table.item(item)['open']:
                    opened.append(item)
            self.mistakes_table.delete(*self.mistakes_table.get_children())
            self.add_category_grade_entries()
            category_table_entries = {}
            for category in self.model.all_categories():
                if category:
                    if category not in self.model.not_graded():
                        grade_entry = self.category_grades_entries[category]
                        grade_entry.config(state='normal')
                        grade_entry.delete(0, tk.END)
                        grade_entry.insert(0, model.category_grades[category])
                        total += self.model.category_grades[category]
                        grade_entry.config(state='disabled')
                    category_table_entries[category] = \
                            self.mistakes_table.insert("", "end", category, text=self.model.abbreviation(category), values=("", "", ""))
            for item in opened:
                if item in self.mistakes_table.get_children():
                    self.mistakes_table.item(item, open=True)
            for i in range(len(self.model.mistakes)):
                lines, category, grade, desc = self.model.mistakes[i]
                self.mistakes_table.insert(category_table_entries[category], "end", iid=i, text="",
                        values=(lines, desc, grade))





    class AnnotationBank(ttk.Frame):
        class AnnotationEditor(tk.Toplevel):
            def __init__(self, model, cancel_fn, add_assignment_fn, del_assignment_fn,
                    master=None):
                super().__init__(master)
                self.title("Add Annotation")
                self.resizable(False, False)
                self.model = model
                if MAC:
                    self['background'] = MAC_BG_COLOR
                # Assignment
                self.assignment_var = tk.StringVar(self.master)
                self.assignment = ttk.OptionMenu(self, self.assignment_var, "General",
                        *(["General"] + model.assignments))
                self.assignment.grid(row=0, column=1, columnspan=1, padx=2, pady=2, sticky='ew')
                self.assignment_buttons = ttk.Frame(self)
                self.assignment_buttons.grid(row=0, column=2, padx=2, pady=2, sticky='ew')
                def add_assignment(fn):
                    fn()
                    self.destroy()
                def del_assignment(fn, name):
                    fn(name)
                    self.destroy()
                self.remove_assignment_button = ttk.Button(self.assignment_buttons) 
                self.remove_assignment_button["text"] = "-"
                self.remove_assignment_button["width"] = 3
                self.remove_assignment_button.bind("<Button>",
                        lambda _: del_assignment(del_assignment_fn, self.assignment_var.get()))
                self.remove_assignment_button.grid(row=0, column=0, padx=2, pady=2, sticky='e')
                self.add_assignment_button = ttk.Button(self.assignment_buttons) 
                self.add_assignment_button["text"] = "+"
                self.add_assignment_button["width"] = 3
                self.add_assignment_button.bind("<Button>",
                        lambda _: add_assignment(add_assignment_fn))
                self.add_assignment_button.grid(row=0, column=1, padx=2, pady=2, sticky='e')
                # Category
                self.category_var = tk.StringVar(self.master)
                self.category = ttk.OptionMenu(self, self.category_var,
                    self.model.all_categories()[0], *(self.model.all_categories()))
                self.category.config(width=30)
                self.category.grid(row=1, column=1, padx=2, pady=2, sticky='ew')
                # Grade
                self.grade_var = tk.StringVar(self.master)
                self.grade = ttk.OptionMenu(self, self.grade_var, GRADES[0], *GRADES)
                self.grade.config(width=2)
                self.grade.grid(row=1, column=2, padx=2, pady=2, sticky='ew')
                # grading notes
                self.note_label = ttk.Label(self, text="Grading Notes")
                self.note_label.grid(row=2, column=0, padx=2, pady=2, sticky='nw')
                self.note_entry = tk.Text(self, height=3, width=40, wrap=tk.WORD)
                self.note_entry.grid(row=2, column=1, columnspan=2, padx=2, pady=2, sticky='nsew')
                self.note_entry.insert("1.0", "")
                # description entry
                self.desc_label = ttk.Label(self, text="Description")
                self.desc_label.grid(row=3, column=0, padx=2, pady=2, sticky='nw')
                self.desc_entry = tk.Text(self, height=6, width=40, wrap=tk.WORD)
                self.desc_entry.grid(row=3, column=1, columnspan=2, padx=2, pady=2, sticky='nsew')
                self.desc_entry.insert("1.0", "")
                # annotation entry
                self.annotation_label = ttk.Label(self, text="Annotation")
                self.annotation_label.grid(row=4, column=0, padx=2, pady=2, sticky='nw')
                self.annotation_entry = tk.Text(self, height=14, width=40, wrap=tk.WORD)
                self.annotation_entry.grid(row=4, column=1, columnspan=2,
                        padx=2, pady=2, sticky='nsew')
                self.annotation_entry.insert("1.0", "")
                # tags
                self.tag_label = ttk.Label(self, text="Keywords")
                self.tag_label.grid(row=5, column=0, padx=2, pady=2, sticky='nw')
                self.tag_entry = tk.Text(self, height=2, width=40, wrap=tk.WORD)
                self.tag_entry.grid(row=5, column=1, columnspan=2, padx=2, pady=2, sticky='nsew')
                self.tag_entry.insert("1.0", "")
                #button frame
                self.buttons = ttk.Frame(self)
                self.buttons.grid(row=6, column=0, columnspan=3, padx=9, pady=2, sticky='ew')
                # cancel button
                self.cancel_button = ttk.Button(self.buttons, text="Cancel")
                self.cancel_button.pack(side='left')
                def cancel():
                    cancel_fn()
                    self.destroy()
                self.cancel_button.bind("<Button>", lambda _: cancel())
                self.protocol("WM_DELETE_WINDOW", lambda: cancel())
                # add button
                self.add_button = ttk.Button(self.buttons, text="Add to Bank")
                self.add_button.pack(side='right')
                def add_annotation():
                    model.add_annotation(self.assignment_var.get(),
                            self.note_entry.get("1.0", tk.END),
                            self.category_var.get(), self.grade_var.get(),
                            self.desc_entry.get("1.0", tk.END),
                            self.annotation_entry.get("1.0", tk.END),
                            self.tag_entry.get("1.0", tk.END))
                    self.destroy()
                self.add_button.bind("<Button>", lambda _: add_annotation())

        def __init__(self, model, scoresheet=None, master=None):
            super().__init__(master)
            self.master = master
            self.grid(row=0, column=0)
            self.model = model
            self.scoresheet = scoresheet
            self.annotation_editor = None
            self.add_selected_view()
            self.add_bank_view()

        def add_selected_view(self):
            # frame
            self.selected_view_frame = ttk.Frame(self)
            self.selected_view_frame.grid(row=0, column=0, padx=4, pady=2, sticky='ew')
            # assignment
            self.selected_assignment_entry = ttk.Entry(self.selected_view_frame, state='disabled')
            self.selected_assignment_entry.grid(row=0, column=0, pady=2, sticky='w')
            # category
            self.selected_category_entry = ttk.Entry(self.selected_view_frame, state='disabled')
            self.selected_category_entry.grid(row=0, column=1, pady=2, sticky='w')
            # saved grade
            self.selected_grade_entry = \
                    ttk.Entry(self.selected_view_frame, width=2, state='disabled')
            self.selected_grade_entry.grid(row=0, column=2, pady=2, sticky='ew')
            #description
            self.selected_desc_entry = ttk.Entry(self.selected_view_frame, state='disabled')
            self.selected_desc_entry.grid(row=1, column=0, columnspan=3, pady=2, sticky='ew')
            # annotation text
            self.selected_annotation_text = tk.Text(self.selected_view_frame, width=30, height=15,
                    state='disabled', wrap=tk.WORD)
            self.selected_annotation_text.grid(row=2, column=0, columnspan=3, pady=2, sticky='nsew')
             # notes
            self.selected_note_text = tk.Text(self.selected_view_frame, width=30, height=3,
                    state='disabled', wrap=tk.WORD)
            self.selected_note_text.grid(row=3, column=0, columnspan=3, pady=2, sticky='nsew')
            # copy, add buttons
            self.selected_annotation_buttons = ttk.Frame(self.selected_view_frame)
            self.selected_annotation_buttons.grid(row=4, column=0, pady=4, columnspan=3)
            self.copy_selected_annotation_button = ttk.Button(self.selected_annotation_buttons,
                    text="Copy Annotation")
            self.copy_selected_annotation_button.bind("<Button>", lambda _: self.copy_annotation())
            self.copy_selected_annotation_button.grid(row=0, column=0)
            self.add_selected_annotation_button = ttk.Button(self.selected_annotation_buttons,
                    text="Add to Scoresheet")
            self.add_selected_annotation_button.grid(row=0, column=1)
            self.add_selected_annotation_button.bind("<Button>", lambda _: self.add_to_scoresheet())
                
        def add_bank_view(self):
            # frame
            self.bank_view_frame = ttk.Frame(self)
            self.bank_view_frame.grid(row=0, column=1, padx=2, pady=2)
            # search bar
            self.search_bar_frame = ttk.Frame(self.bank_view_frame)
            self.search_bar_frame.grid(row=0, rowspan=2, column=0, sticky='w', padx=4, pady=4)
            self.search_bar_label = ttk.Label(self.search_bar_frame, text="Search:")
            self.search_bar_label.pack(side="left")
            self.search_bar_entry_var = tk.StringVar()
            self.search_bar_entry = ttk.Entry(self.search_bar_frame,
                    textvariable=self.search_bar_entry_var, width=30)
            self.search_bar_entry.pack(side="left")
            # filter assignment 
            self.assignment_var = tk.StringVar()
            self.assignment = ttk.OptionMenu(self.bank_view_frame, self.assignment_var, '',
                    *self.model.assignments)
            self.assignment.config(width=20)
            self.assignment_var.trace("w", lambda *args: self.update())
            self.search_bar_entry_var.trace("w", lambda *args: self.update())
            self.assignment.grid(row=0, column=1, pady=2, sticky='e')
            # include general annotations button
            self.general_annotations_check_var = tk.BooleanVar()
            self.general_annotations_check_var.set(True)
            self.general_annotations_check_button = ttk.Checkbutton(self.bank_view_frame,
                    text='Include General Annotations',
                    variable=self.general_annotations_check_var,
                    onvalue=True, offvalue=False)
            self.general_annotations_check_var.trace("w", lambda *args: self.update())
            self.general_annotations_check_button.grid(row=1, column=1, sticky='e')
            # table
            self.bank_table_frame = ttk.Frame(self.bank_view_frame)
            self.bank_table_frame.grid(row=2, column=0, columnspan=3, padx=6, pady=2, sticky='ew')
            self.bank_scrollbar = ttk.Scrollbar(self.bank_table_frame)
            self.bank_scrollbar.grid(row=0, column=1, padx=1, sticky='ns')
            self.bank_table = ttk.Treeview(self.bank_table_frame, height=15,
                    yscrollcommand=self.bank_scrollbar.set)
            self.bank_table["columns"] = ("#1", "#2")
            self.bank_table.column("#0", width=75, minwidth=50)
            self.bank_table.heading("#0", text="Category", anchor='w')
            self.bank_table.column("#1", width=400, minwidth=150)
            self.bank_table.heading("#1", text="Description", anchor='w')
            self.bank_table.column("#2", width=75, minwidth=75)
            self.bank_table.heading("#2", text="Grade", anchor='w')
            self.bank_table.grid(row=0, column=0)
            self.bank_scrollbar.config(command=self.bank_table.yview)
            self.bank_table.bind("<ButtonRelease-1>", lambda _: self.display_selected())
            # Add buttons
            self.bank_table_buttons = ttk.Frame(self.bank_table_frame)
            self.bank_table_buttons.grid(row=1, column=0, sticky='e')
            self.add_annotation_button = ttk.Button(self.bank_table_buttons)
            self.add_annotation_button["text"] = "+"
            self.add_annotation_button["width"] = 3
            self.add_annotation_button.bind("<Button>", lambda _: self.add_new_annotation())
            self.add_annotation_button.pack(side="right")
            self.edit_annotation_button = ttk.Button(self.bank_table_buttons)
            self.edit_annotation_button["text"] = "..."
            self.edit_annotation_button["width"] = 3
            self.edit_annotation_button.bind("<Button>", lambda _: self.edit_annotation())
            self.edit_annotation_button.pack(side="right")
            self.remove_annotation_button = ttk.Button(self.bank_table_buttons)
            self.remove_annotation_button["text"] = "-"
            self.remove_annotation_button["width"] = 3
            self.remove_annotation_button.bind("<Button>", lambda _: self.remove_annotation())
            self.remove_annotation_button.pack(side="right")

        def add_new_assignment(self):
            assignment_name = simpledialog.askstring("Add Assignment", "Assignment Name?")
            if assignment_name and assignment_name not in self.model.assignments and \
                    assignment_name != 'General':
                self.model.assignments.append(assignment_name)
                self.update()

        def remove_assignment(self, assignment):
            confirm = messagebox.askquestion("Delete Assignment", "Delete " + assignment +
                    " and all associated annotations?", icon='warning')
            if confirm == 'yes' and assignment in self.model.assignments:
                to_remove = []
                for i in range(len(self.model.annotations)):
                    annotation = self.model.annotations[i]
                    if annotation[0] == assignment:
                        to_remove.append(i)
                for i in reversed(to_remove):
                    self.model.remove_annotation(i)
                self.model.assignments.remove(assignment)
                self.update()

        def add_new_annotation(self):
            if self.annotation_editor:
                self.annotation_editor.destroy()
            def nothing():
                pass
            self.annotation_editor = self.AnnotationEditor(self.model, nothing,
                    self.add_new_assignment, self.remove_assignment, self.master)
            if self.assignment_var.get():
                self.annotation_editor.assignment_var.set(self.assignment_var.get())
            else:
                self.annotation_editor.assignment_var.set('General')
            if self.bank_table.selection():
                iid = self.bank_table.selection()[0]
                if iid in self.model.all_categories():
                    self.annotation_editor.category_var.set(iid)

        def edit_annotation(self):
            if self.bank_table.selection():
                item = self.bank_table.selection()[0]
                if item not in self.model.all_categories():
                    index = int(item)
                    assignment, notes, category, grade, desc, annotation, tags = \
                            self.model.annotations[index]
                    if self.annotation_editor:
                        self.annotation_editor.destroy()
                    self.model.remove_annotation(index)
                    def cancel_fn():
                        self.model.add_annotation(assignment, notes, category,
                                grade, desc, annotation, tags, index)
                    self.annotation_editor = self.AnnotationEditor(self.model, cancel_fn,
                            self.add_new_assignment, self.remove_assignment, self.master)
                    
                    self.annotation_editor.category_var.set(category)
                    self.annotation_editor.grade_var.set(grade)
                    self.annotation_editor.assignment_var.set(assignment)
                    self.annotation_editor.desc_entry.delete("1.0", tk.END)
                    self.annotation_editor.desc_entry.insert("1.0", desc)
                    self.annotation_editor.annotation_entry.delete("1.0", tk.END)
                    self.annotation_editor.annotation_entry.insert("1.0", annotation)
                    self.annotation_editor.tag_entry.delete("1.0", tk.END)
                    self.annotation_editor.tag_entry.insert("1.0", tags)
                    self.annotation_editor.note_entry.delete("1.0", tk.END)
                    self.annotation_editor.note_entry.insert("1.0", notes)

        def remove_annotation(self):
            if self.bank_table.selection():
                item = self.bank_table.selection()[0]
                if item not in self.model.all_categories():
                    index = int(item)
                    confirmation = tk.messagebox.askquestion('Delete Annotation',
                            "Permanently delete the selected annotation?", icon='warning')
                    if confirmation == 'yes':
                        self.model.remove_annotation(index)
                        self.display_selected()

        def copy_annotation(self):
            text = self.selected_annotation_text.get("1.0", tk.END)
            if text and self.selected_category_entry.get() in self.model.all_categories():
                category = self.selected_category_entry.get()
                abbreviation = self.model.abbreviation(category)
                annotation = ('**(' + abbreviation + ": " +
                        self.selected_desc_entry.get().strip() + ')** ' + text)
                pyperclip.copy(annotation)
                pyperclip.paste()   

        def add_to_scoresheet(self):
            if self.scoresheet and self.bank_table.selection():
                item = self.bank_table.selection()[0]
                #index = self.mistakes_table.item(mistake, 'iid')
                if item not in self.model.all_categories():
                    index = int(item)
                    assignment, notes, category, grade, desc, annotation, tags = \
                            self.model.annotations[index]
                    if self.scoresheet.mistake_editor:
                        self.scoresheet.mistake_editor.destroy()
                    def cancel_fn():
                        pass
                    self.scoresheet.mistake_editor = self.scoresheet.MistakeEditor(self.model,
                        cancel_fn, self.master)
                    self.scoresheet.mistake_editor.category_var.set(category)
                    self.scoresheet.mistake_editor.grade_var.set(grade)
                    self.scoresheet.mistake_editor.line_entry.delete(0, tk.END)
                    self.scoresheet.mistake_editor.line_entry.insert(0, '')
                    self.scoresheet.mistake_editor.desc_entry.delete("1.0", tk.END)
                    self.scoresheet.mistake_editor.desc_entry.insert("1.0", desc)
    
        def update(self):
            opened = []
            for item in self.bank_table.get_children():
                if self.bank_table.item(item)['open']:
                    opened.append(item)

            selection = self.bank_table.selection()
            self.bank_table.delete(*self.bank_table.get_children())
            category_table_entries = {}
            for category in self.model.all_categories():
                if category:
                    abbreviation = self.model.abbreviation(category)
                    category_table_entries[category] = \
                            self.bank_table.insert("", "end", category,
                                    text=abbreviation, values=("", ""))
            for item in opened:
                if item in self.bank_table.get_children():
                    self.bank_table.item(item, open=True)
            search_entry = self.search_bar_entry_var.get().lower()

            for i in range(len(self.model.annotations)):
                assignment, notes, category, grade, desc, annotation, tags = self.model.annotations[i]
                if ((self.assignment_var.get() == assignment or (assignment == "General" and
                        self.general_annotations_check_var.get() == True)) and 
                        (search_entry in desc.lower() or 
                        search_entry in annotation.lower() or
                        search_entry in tags.lower())):
                    self.bank_table.insert(category_table_entries[category],
                            "end", iid=i, text="", values=(desc, grade)) 

            if selection and self.bank_table.exists(selection[0]):
                self.bank_table.selection_add(selection[0])
                self.bank_table.see(selection[0])

            self.assignment['menu'].delete(0, 'end')
            if self.model.assignments:
                for assignment in self.model.assignments:
                    self.assignment['menu'].add_command(label=assignment,
                            command=tk._setit(self.assignment_var, assignment))
                if (not self.assignment_var.get() or
                        self.assignment_var.get() not in self.model.assignments):
                    self.assignment_var.set(self.model.assignments[0])
            else:
                self.assignment_var.set('')

            self.display_selected()

        def display_selected(self):
            selection = self.bank_table.selection()
            if selection and selection[0] not in self.model.all_categories():
                item = selection[0]
                index = int(item)
                assignment, notes, category, grade, desc, annotation, tags = \
                    self.model.annotations[index]
                self.selected_assignment_entry.config(state='enabled')
                self.selected_assignment_entry.delete(0, tk.END)
                self.selected_assignment_entry.insert(0, assignment.strip())
                self.selected_assignment_entry.config(state='disabled')
                self.selected_category_entry.config(state='enabled')
                self.selected_category_entry.delete(0, tk.END)
                self.selected_category_entry.insert(0, category.strip())
                self.selected_category_entry.config(state='disabled')
                self.selected_grade_entry.config(state='enabled')
                self.selected_grade_entry.delete(0, tk.END)
                self.selected_grade_entry.insert(0, grade.strip())
                self.selected_grade_entry.config(state='disabled')
                self.selected_note_text.config(state='normal')
                self.selected_note_text.delete("1.0", tk.END)
                self.selected_note_text.insert("1.0", notes.strip())
                self.selected_note_text.config(state='disabled')
                self.selected_desc_entry.config(state='enabled')
                self.selected_desc_entry.delete(0, tk.END)
                self.selected_desc_entry.insert(0, desc.strip())
                self.selected_desc_entry.config(state='disabled')
                self.selected_annotation_text.config(state='normal')
                self.selected_annotation_text.delete("1.0", tk.END)
                self.selected_annotation_text.insert("1.0", annotation.strip())
                self.selected_annotation_text.config(state='disabled')
            else:
                self.selected_assignment_entry.config(state='enabled')
                self.selected_assignment_entry.delete(0, tk.END)
                self.selected_assignment_entry.insert(0, '')
                self.selected_assignment_entry.config(state='disabled')
                self.selected_category_entry.config(state='enabled')
                self.selected_category_entry.delete(0, tk.END)
                self.selected_category_entry.insert(0, '')
                self.selected_category_entry.config(state='disabled')
                self.selected_grade_entry.config(state='enabled')
                self.selected_grade_entry.delete(0, tk.END)
                self.selected_grade_entry.insert(0, '')
                self.selected_grade_entry.config(state='disabled')
                self.selected_note_text.config(state='normal')
                self.selected_note_text.delete("1.0", tk.END)
                self.selected_note_text.insert("1.0", '')
                self.selected_note_text.config(state='disabled')
                self.selected_desc_entry.config(state='enabled')
                self.selected_desc_entry.delete(0, tk.END)
                self.selected_desc_entry.insert(0, '')
                self.selected_desc_entry.config(state='disabled')
                self.selected_annotation_text.config(state='normal')
                self.selected_annotation_text.delete("1.0", tk.END)
                self.selected_annotation_text.insert("1.0", '')
                self.selected_annotation_text.config(state='disabled')

    
    class CategoryEditor(tk.Toplevel):
        def __init__(self, model, master=None):
            super().__init__(master)
            self.title("Edit Categories")
            self.resizable(False, False)
            self.model = model
            if MAC:
                self['background'] = MAC_BG_COLOR
            self.category_list = tk.Listbox(self, width=35, selectmode=tk.SINGLE)
            self.category_list.configure(exportselection=False)
            self.add_categories_to_list()
            self.category_list.grid(row=0, column=0, columnspan=1, padx=2, pady=2, sticky='ew')
            self.category_list.bind("<ButtonRelease-1>", lambda _: self.display_selected())
            self.category_var = tk.StringVar(self.master)
            self.category = ttk.OptionMenu(self, self.category_var, self.model.all_categories()[0],
                    *(self.model.all_categories()))
            self.category_buttons = ttk.Frame(self)
            self.category_buttons.grid(row=1, column=0, padx=2, pady=2, sticky='ne')
            self.remove_category_button = ttk.Button(self.category_buttons) 
            self.remove_category_button["text"] = "-"
            self.remove_category_button["width"] = 3
            def remove():
                selection = self.category_list.curselection()
                if selection:
                    category = self.category_list.get(selection[0])
                    if category in self.model.all_categories():
                        confirmation = tk.messagebox.askquestion('Delete Category',
                                "Permanently delete the " + category + " category " +
                                "and all related annotations and mistakes?", icon='warning')
                        if confirmation == 'yes':
                            self.model.remove_category(category)
                            self.add_categories_to_list()
                            self.attributes("-topmost", True)
                            self.after_idle(self.attributes,"-topmost",False)
            self.remove_category_button.bind("<Button>", lambda _: remove())
            self.remove_category_button.grid(row=0, column=0, padx=2, pady=2, sticky='e')
            self.add_category_button = ttk.Button(self.category_buttons) 
            self.add_category_button["text"] = "+"
            self.add_category_button["width"] = 3
            def add():
                category_name = simpledialog.askstring("Add Category", "Category Name?")
                if category_name and category_name not in self.model.all_categories():
                    abbreviation = "".join(word[0].upper() for word in category_name.split())
                    graded = True
                    self.model.add_category(category_name, abbreviation, graded)
                    self.add_categories_to_list()
                    self.attributes("-topmost", True)
                    self.after_idle(self.attributes,"-topmost",False)
            self.add_category_button.bind("<Button>", lambda _: add())
            self.add_category_button.grid(row=0, column=1, padx=2, pady=2, sticky='e')
            self.move_category_buttons = ttk.Frame(self)
            self.move_category_buttons.grid(row=1, column=0, padx=2, pady=2, sticky='nw')
            self.move_down_button = ttk.Button(self.move_category_buttons) 
            self.move_down_button["text"] = "v"
            self.move_down_button["width"] = 3
            def move_down():
                selection = self.category_list.curselection()
                if selection:
                    index = selection[0]
                    actual_index = index
                    category = self.category_list.get(index)
                    if category in self.model.not_graded():
                        actual_index -= len(self.model.graded())
                    if category in self.model.all_categories():
                        self.model.move_category(category, actual_index + 1)
                        self.add_categories_to_list()
                        self.category_list.selection_set(index + 1)
            self.move_down_button.bind("<Button>", lambda _: move_down())
            self.move_down_button.grid(row=0, column=0, padx=2, pady=2, sticky='e')
            self.move_up_button = ttk.Button(self.move_category_buttons) 
            self.move_up_button["text"] = "^"
            self.move_up_button["width"] = 3
            def move_up():
                selection = self.category_list.curselection()
                if selection:
                    index = selection[0]
                    actual_index = index
                    category = self.category_list.get(index)
                    if category in self.model.not_graded():
                        actual_index -= len(self.model.graded())
                    if category in self.model.all_categories() and index > 0:
                        self.model.move_category(category, actual_index - 1)
                        self.add_categories_to_list()
                        self.category_list.selection_set(index - 1)
            self.move_up_button.bind("<Button>", lambda _: move_up())
            self.move_up_button.grid(row=0, column=1, padx=2, pady=2, sticky='e')
            self.switching = False
            def edit():
                selection = self.category_list.curselection()
                if selection and not self.switching:
                    category = self.category_list.get(selection[0])
                    self.model.edit_category(category, self.category_var.get(),
                            self.abbreviation_entry.get(),
                            self.graded_check_var.get())
                    self.add_categories_to_list()
                    self.category_list.selection_set(selection[0])
                    self.display_selected()
            self.selected_category_frame = ttk.Frame(self)
            self.selected_category_frame.grid(row=3, column=0, padx=2, pady=2, sticky='ew')
            self.category_var = tk.StringVar()
            self.selected_category_entry = ttk.Entry(self.selected_category_frame, width=50, textvariable=self.category_var)
            self.selected_category_entry.grid(row=0, column=0, columnspan=3, pady=2, sticky='ew')
            self.category_var.trace("w", lambda *args: edit())
            self.abbreviation_label = ttk.Label(self.selected_category_frame, text='Abbreviation')
            self.abbreviation_label.grid(row=1, column=0, pady=2, sticky='w')
            self.abbreviation_var = tk.StringVar()
            self.abbreviation_entry = ttk.Entry(self.selected_category_frame, width=25, textvariable=self.abbreviation_var)
            self.abbreviation_entry.grid(row=1, column=1, pady=2, sticky='w')
            self.abbreviation_var.trace("w", lambda *args: edit())
            self.graded_check_var = tk.BooleanVar()
            self.graded_check_var.set(False)
            self.graded_check_button = ttk.Checkbutton(self.selected_category_frame,
                    text='Graded',
                    variable=self.graded_check_var,
                    onvalue=True, offvalue=False)
            self.graded_check_button.grid(row=1, column=2, columnspan=2, padx=4,  pady=2, sticky='e')
            self.graded_check_var.trace("w", lambda *args: edit())
            self.cancel_button = ttk.Button(self) 
            self.cancel_button["text"] = "Close"
            self.cancel_button.bind("<ButtonRelease>", lambda _: self.destroy())
            self.cancel_button.grid(row=4, column=0, padx=2, pady=2, sticky='e')

        def add_categories_to_list(self):
            self.category_list.delete(0, tk.END)
            for category in self.model.all_categories():
                self.category_list.insert(tk.END, category)

        def display_selected(self):
            self.switching = True
            selection = self.category_list.curselection()
            if selection:
                category = self.category_list.get(selection[0])
                self.selected_category_entry.delete(0, tk.END)
                self.selected_category_entry.config(state='normal')
                self.selected_category_entry.insert(0, category)
                self.abbreviation_entry.delete(0, tk.END)
                self.abbreviation_entry.config(state='normal')
                self.abbreviation_entry.insert(0, self.model.abbreviation(category))
                self.graded_check_button.config(state='normal')
                self.graded_check_var.set(category in self.model.graded())
                if category in self.model.graded():
                    self.graded_check_var.set(True)
            else:
                self.selected_category_entry.delete(0, tk.END)
                self.selected_category_entry.config(state='disabled')
                self.abbreviation_entry.delete(0, tk.END)
                self.abbreviation_entry.config(state='disabled')
                self.graded_check_button.config(state='disabled')
            self.switching = False          
            
    class MessageEditor(tk.Toplevel):
        def __init__(self, model, master=None):
            super().__init__(master)
            self.title("Edit Overall Feedback Messages")
            self.resizable(False, False)
            self.model = model
            if MAC:
                self['background'] = MAC_BG_COLOR
            self.perfect_label = ttk.Label(self, text='Perfect Score Message')
            self.perfect_label.grid(row=0, column=0, padx=2, pady=2, sticky='nw')
            self.perfect_text = tk.Text(self, height=8, width=50, wrap=tk.WORD)
            self.perfect_text.grid(row=0, column=1, padx=2, pady=2)
            def set_perfect():
                self.model.perfect = self.perfect_text.get("1.0", tk.END)
            self.perfect_text.insert("1.0", self.model.perfect)
            self.perfect_text.bind("<KeyRelease>", lambda _: set_perfect())
            self.poor_label = ttk.Label(self, text='Poor Score Message')
            self.poor_label.grid(row=1, column=0, padx=2, pady=2, sticky='nw')
            self.poor_text = tk.Text(self, height=8, width=50, wrap=tk.WORD)
            self.poor_text.grid(row=1, column=1, padx=2, pady=2)
            def set_poor():
                self.model.poor = self.poor_text.get("1.0", tk.END)
            self.poor_text.insert("1.0", self.model.poor)
            self.poor_text.bind("<KeyRelease>", lambda _: set_poor())
            self.general_var = tk.StringVar(self)
            self.general_chooser = None
            self.update_chooser()
            self.add_sentence_buttons = tk.Frame(self)
            self.add_sentence_buttons.grid(row=3, column=0, padx=2, pady=2, sticky='ne')
            self.add_sentence_button = ttk.Button(self.add_sentence_buttons) 
            self.add_sentence_button["text"] = "Add General Sentence"
            self.add_sentence_button.grid(row=0, column=0, padx=2, pady=2, sticky='ew')
            def add_general():
                index = simpledialog.askinteger("Add General Sentence", "Where would you like to add this sentence (e.g. sentence 1, 3, etc.)?")
                if index and index - 1 > 0:
                    self.model.general.insert(min(index - 1, len(self.model.general)), ['New sentence.'])
                    self.update_chooser()
                    self.add_sentences_to_list()
                self.attributes("-topmost", True)
                self.after_idle(self.attributes,"-topmost",False)
            self.add_sentence_button.bind("<Button>", lambda _: add_general())
            self.remove_sentence_button = ttk.Button(self.add_sentence_buttons) 
            self.remove_sentence_button["text"] = "Remove General Sentence"
            self.remove_sentence_button.grid(row=1, column=0, padx=2, pady=2, sticky='ew')
            def remove_general():
                if len(self.model.general) > 1:
                    confirmation = tk.messagebox.askquestion('Delete General Sentence',
                                "Permanently delete " + self.general_var.get() + "?", icon='warning')
                    if confirmation == 'yes':
                        index = self.general_sentences.index(self.general_var.get())
                        del self.model.general[index]
                        self.update_chooser()
                        self.add_sentences_to_list()
                    self.attributes("-topmost", True)
                    self.after_idle(self.attributes,"-topmost",False)
            self.remove_sentence_button.bind("<Button>", lambda _: remove_general())
            self.sentence_list = tk.Listbox(self, height=5, width=35, selectmode=tk.SINGLE)
            self.sentence_list.configure(exportselection=False)
            self.sentence_list.grid(row=2, rowspan=2, column=1, padx=2, pady=2, sticky='ew')
            self.add_sentences_to_list()
            self.general_var.trace('w', lambda *args: self.add_sentences_to_list())
            self.selected_sentence_text = tk.Text(self, height=5, width=50, wrap=tk.WORD)
            self.selected_sentence_text.grid(row=4, column=1, padx=2, pady=2, sticky='ew')
            def display_selected():
                index = self.general_sentences.index(self.general_var.get())
                selection = self.sentence_list.curselection()
                if selection:
                    self.selected_sentence_text.delete("1.0", tk.END)
                    self.selected_sentence_text.insert("1.0", self.model.general[index][selection[0]])
                else:
                    self.selected_sentence_text.delete("1.0", tk.END)
            self.sentence_list.bind("<ButtonRelease-1>", lambda _: display_selected())
            def update_selected():
                index = self.general_sentences.index(self.general_var.get())
                selection = self.sentence_list.curselection()
                if selection:
                    self.model.general[index][selection[0]] = self.selected_sentence_text.get("1.0", tk.END).strip()
                    self.add_sentences_to_list()
                    self.sentence_list.selection_set(selection[0])
            self.selected_sentence_text.bind("<KeyRelease>", lambda _: update_selected())
            self.add_sentence_option_buttons = tk.Frame(self)
            self.add_sentence_option_buttons.grid(row=5, column=1, padx=2, pady=2, sticky='ne')
            self.add_sentence_option_button = ttk.Button(self.add_sentence_option_buttons) 
            self.add_sentence_option_button["text"] = "+"
            self.add_sentence_option_button["width"] = 3
            self.add_sentence_option_button.grid(row=0, column=1, padx=2, pady=2)
            def add():
                index = self.general_sentences.index(self.general_var.get())
                self.model.general[index].append("New sentence.")
                self.add_sentences_to_list()
            self.add_sentence_option_button.bind("<Button>", lambda _: add())
            self.remove_sentence_option_button = ttk.Button(self.add_sentence_option_buttons) 
            self.remove_sentence_option_button["text"] = "-"
            self.remove_sentence_option_button["width"] = 3
            self.remove_sentence_option_button.grid(row=0, column=0, padx=2, pady=2)
            def remove():
                index = self.general_sentences.index(self.general_var.get())
                selection = self.sentence_list.curselection()
                if selection:
                    del self.model.general[index][selection[0]]
                    self.add_sentences_to_list()
            self.remove_sentence_option_button.bind("<Button>", lambda _: remove())
            self.exit_button = ttk.Button(self)
            self.exit_button["text"] = "Close"
            self.exit_button.grid(row=6, column=1, padx=2, pady=2, sticky='ne')
            self.exit_button.bind("<Button>", lambda _: self.destroy())
            #self.category_list.bind("<ButtonRelease-1>", lambda _: self.display_selected())

        def add_sentences_to_list(self):
            self.sentence_list.delete(0, tk.END)
            index = self.general_sentences.index(self.general_var.get())
            count = 1
            for sentence in self.model.general[index]:
                self.sentence_list.insert(tk.END, str(count) + ". " + sentence)
                count += 1

        def update_chooser(self):
            self.general_sentences = ['General Sentence ' + str(i + 1) for i in range(len(self.model.general))]
            if self.general_chooser:
                self.general_chooser.destroy()
            self.general_chooser = ttk.OptionMenu(self, self.general_var,
                self.general_sentences[0], *(self.general_sentences))
            # self.general_chooser.config(width=30)
            self.general_chooser.grid(row=2, column=0, padx=2, pady=2, sticky='ew')

    def __init__(self, model):
        """
        Initializes a new GradingAssistantView
        """
        self.window = tk.Tk()
        self.window.title("14X Grading Assistant")
        self.window.resizable(False, False)
        self.scoresheet = self.Scoresheet(model, master=self.window)
        self.scoresheet.grid(row=0, column=0, sticky='nesw')
        self.bank = self.AnnotationBank(model, self.scoresheet, master=self.window)
        self.bank.grid(row=1, column=0, sticky='nesw')
        self.model = model
        self.model.add_view(self)
        # menu bar and hotkeys
        self.category_editor = None
        self.message_editor = None
        self.menu_bar = tk.Menu(self.window)
        self.annotation_bank_bar = tk.Menu(self.menu_bar, tearoff=0)
        self.annotation_bank_bar.add_command(label="New", command=self.new_bank,
                accelerator="Ctrl+N")
        self.annotation_bank_bar.add_command(label="Save", command=self.save_bank,
                accelerator="Ctrl+S")
        self.annotation_bank_bar.add_command(label="Save as...", command=self.save_bank_as,
                accelerator="Ctrl+Shift+S")
        self.annotation_bank_bar.add_command(label="Open...", command=self.load_bank,
                accelerator="Ctrl+O")
        self.window.bind_all("<Control-n>", lambda _: self.new_bank())
        self.window.bind_all("<Control-s>", lambda _: self.save_bank())
        self.window.bind_all("<Control-Shift-KeyPress-S>", lambda _: self.save_bank_as())
        self.window.bind_all("<Control-o>", lambda _: self.load_bank())
        self.annotation_bank_bar.add_separator()
        self.annotation_bank_bar.add_command(label="Import...", command=self.import_bank)
        self.annotation_bank_bar.add_separator()
        self.annotation_bank_bar.add_command(label="Exit", command=self.window.quit,
                accelerator="Ctrl+Q")
        self.window.bind_all("<Control-Shift-KeyPress-Q>", lambda _: self.window.quit())
        self.menu_bar.add_cascade(label="File", menu=self.annotation_bank_bar)
        self.scoresheet_bar = tk.Menu(self.menu_bar, tearoff=0)
        self.scoresheet_bar.add_command(label="Reset Scoresheet",
                command=self.model.reset_scoresheet, accelerator="Ctrl+R")
        self.scoresheet_bar.add_command(label="Categories", command=self.edit_categories)
        self.scoresheet_bar.add_command(label="Feedback Messages", command=self.edit_messages)
        self.window.bind_all("<Control-r>", lambda _ : self.model.reset_scoresheet())
        self.menu_bar.add_cascade(label="Edit", menu=self.scoresheet_bar)
        self.window['menu'] = self.menu_bar
        self.window.mainloop()

    def new_bank(self):
        self.model.ta_email = "your_email@uw.edu"
        self.model.bank_filename = '' 
        self.model.assignments = []
        self.model.annotations = []
        self.model.mistakes = []
        self.model.perfect = DEFAULT_PERFECT
        self.model.poor = DEFAULT_POOR
        self.model.general = DEFAULT_GENERAL.copy()
        self.model.categories = DEFAULT_CATEGORIES.copy()
        self.model.not_graded_categories = DEFAULT_NOT_GRADED.copy()
        self.model.abbreviations = DEFAULT_ABBREVIATIONS.copy()
        self.model.reset_scoresheet()
        self.notify()

    def save_bank(self):
        if not self.model.bank_filename:
            self.save_bank_as()
        else:
            save_file = open(self.model.bank_filename, 'wb')
            pickle.dump((self.model.categories, self.model.not_graded_categories,
                    self.model.abbreviations, self.model.assignments, self.model.annotations,
                    self.model.perfect, self.model.poor, self.model.general), save_file)
            save_file.close()
            self.notify()

    def save_bank_as(self):
        filename = filedialog.asksaveasfilename(initialdir = ".", title = "Save As", 
                defaultextension=".abnk", filetypes =[("Annotation bank file", "*.abank")])
        if filename:
            save_file = open(filename, 'wb')
            pickle.dump((self.model.categories, self.model.not_graded_categories,
                    self.model.abbreviations, self.model.assignments, self.model.annotations,
                    self.model.perfect, self.model.poor, self.model.general), save_file)
            save_file.close()
            self.model.bank_filename = filename
            self.notify()

    def load_bank(self):
        filename = filedialog.askopenfilename(initialdir = ".", title = "Open Bank",
                filetypes =[("Annotation bank file", "*.abank")])
        if filename:
            load_file = open(filename, 'rb')
            self.model.categories, self.model.not_graded_categories, self.model.abbreviations, \
                    self.model.assignments, self.model.annotations, \
                    self.model.perfect, self.model.poor, self.model.general = pickle.load(load_file)
            self.model._calculate_grades()
            self.model.annotations.sort(key = lambda x : x[4])
            load_file.close()
            self.model.bank_filename = filename
            self.notify()

    def import_bank(self):
        filename = filedialog.askopenfilename(initialdir = ".", title = "Import Bank",
                filetypes =[("Annotation bank file", "*.abank")])
        if filename:
            load_file = open(filename, 'rb')
            categories, not_graded_categories, abbreviations, \
                    assignments, annotations, perfect, poor, \
                     general = pickle.load(load_file)
            # self.model.annotations = []
            # for assignment, notes, category, grade, desc, annotation in annotations:
            #     self.model.add_annotation(assignment, notes, category, grade, desc, annotation, '')
            for category in categories:
                if category not in self.model.categories:
                    self.model.categories.append(category)
            for category in not_graded_categories:
                if category not in self.model.not_graded_categories:
                    self.model.not_graded_categories.append(category)
            for abbreviation in abbreviations:
                if abbreviation not in self.model.abbreviations:
                    self.model.abbreviations[abbreviation] = abbreviations[abbreviation]
            for assignment in assignments:
                if assignment not in self.model.assignments:
                    self.model.assignments.append(assignment)
            for annotation in annotations:
                if annotation not in self.model.annotations:
                    self.model.annotations.append(annotation)
            self.model._calculate_grades()
            self.model.annotations.sort(key = lambda x : x[4])
            load_file.close()
            self.notify()

    def edit_categories(self):
        if self.category_editor:
            self.category_editor.destroy()
        self.category_editor = self.CategoryEditor(self.model)

    def edit_messages(self):
        if self.message_editor:
            self.message_editor.destroy()
        self.message_editor = self.MessageEditor(self.model)

    def notify(self):
        self.scoresheet.update()
        self.bank.update()


if __name__ == "__main__":
    model = GradingAssistantModel()
    view = GradingAssistantView(model)