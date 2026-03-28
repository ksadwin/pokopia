import tkinter as tk
from tkinter import ttk
import sqlite3

DB_NAME = "pokopia.db"


def initialize_db():
    # if DB_NAME DNE
    if False:
        # todo: create new file so that I can open DB_NAME despite its not existing
        db = sqlite3.connect(DB_NAME)
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE "pokemon" (
                "name"  TEXT NOT NULL UNIQUE,
                "habitat"   TEXT,
                "location"  TEXT,
                "flavor"    TEXT,
                "discovered"    INTEGER NOT NULL DEFAULT 1,
                "houseid"   INTEGER,
                "satisfaction"  TEXT,
                PRIMARY KEY("name"),
                FOREIGN KEY("houseid") REFERENCES "house"("id")
            );
            ''')
        cursor.execute('''
            CREATE TABLE "skill" (
                "id"    INTEGER NOT NULL UNIQUE,
                "pokemon"   TEXT,
                "name"  TEXT,
                PRIMARY KEY("id" AUTOINCREMENT),
                FOREIGN KEY("pokemon") REFERENCES "pokemon"("name")
            );
            ''')
        cursor.execute('''
            CREATE TABLE "likes" (
                "id"    INTEGER NOT NULL UNIQUE,
                "pokemon"   TEXT,
                "name"  TEXT,
                PRIMARY KEY("id" AUTOINCREMENT),
                FOREIGN KEY("pokemon") REFERENCES "pokemon"("name")
            );
            ''')
        cursor.execute('''
            CREATE TABLE "house" (
                "id"    INTEGER NOT NULL UNIQUE,
                "location"  TEXT,
                "type"  TEXT,
                "ditto" INTEGER NOT NULL DEFAULT 0,
                "maxoccupancy"  INTEGER NOT NULL DEFAULT 1,
                PRIMARY KEY("id" AUTOINCREMENT)
            );
            ''')
        db.commit()
        db.close()


class Pokemon:
    def __init__(self, cool_dict):
        for k, v in cool_dict.items():
            setattr(self, k, v)

    def exists(self):
        db = sqlite3.connect(DB_NAME)
        db.row_factory = sqlite3.Row
        cursor = db.cursor()
        rs = cursor.execute("SELECT * FROM pokemon WHERE name=?", (self.name,)).fetchone() 
        if rs is None:
            db.close()
            return False
        self.fill_in_blanks(rs)
        db.close()
        return True

    def fill_in_blanks(self, rs):
        # rs is a sqlite3.Row returned by fetch one
        for columnname in rs.keys():
            if columnname in self.__dict__ and not self.__dict__[columnname]:
                self.__dict__[columnname] = rs[columnname]

    def write_to_db(self):
        if not self.exists():
            self.insert_new_pokemon()
        self.update_existing_pokemon()
        
    def insert_new_pokemon(self):
        db = sqlite3.connect(DB_NAME)
        cursor = db.cursor()
        cursor.execute("INSERT OR IGNORE INTO pokemon (name, habitat, location, flavor, discovered, satisfaction, houseid) VALUES (:name, :habitat, :location, :flavor, :discovered, :satisfaction, :houseid);", self.__dict__)
        db.commit()
        db.close()

    def update_existing_pokemon(self):
        db = sqlite3.connect(DB_NAME)
        cursor = db.cursor()
        cursor.execute("UPDATE pokemon SET habitat=:habitat, location=:location, flavor=:flavor, discovered=:discovered, satisfaction=:satisfaction, houseid=:houseid WHERE name=:name;", self.__dict__)
        db.commit()
        db.close()


def find_best_matches(name):
    db = sqlite3.connect(DB_NAME)
    db.row_factory = sqlite3.Row
    cursor = db.cursor()
    meaty_query = cursor.execute('''
        SELECT COUNT(*) as 'rating', p.name, p.location
        --     , h.type, h.id, (SELECT COUNT(*) FROM pokemon WHERE houseid = h.id) AS currct, h.maxcount
          FROM likes pl
         INNER JOIN pokemon p ON pl.pokemon = p.name
        --  INNER JOIN house h ON p.houseid = h.id
         WHERE p.name != ?
           AND p.habitat = (SELECT habitat FROM pokemon WHERE name = ?)
           AND pl.id    IN (SELECT id FROM likes WHERE pokemon = ?)
         GROUP BY p.name ORDER BY rating DESC;
        ''', (name, name, name))  # is there a better way to add these arguments...
    print("man i dont want to variablize this header row. Pokemon. its pikachu")
    for row in meaty_query.fetchall():
        print("\t".join(row[:]))
    db.close()

    
def get_house_info():
    # TODO: new tk window for house info intake
    houseid = 0
    return houseid

def add_attr(table, name, value):
    if value:
        db = sqlite3.connect(DB_NAME)
        cursor = db.cursor()
        cursor.execute("INSERT INTO %s (pokemon, name) VALUES (?, ?)" % table, (name, value))
        db.commit()
        db.close()


def route_input(*args):
    houseid = None
    if house_var.get():
        houseid = get_house_info()

    pkmndict = {
        "name": name_var.get(),
        "habitat": habitat_var.get(),
        "location": location_var.get(),
        "flavor": flavor_var.get(),
        "discovered": int(location_var.get()!=''),
        "satisfaction": satisfaction_var.get(),
        "houseid": houseid
        }

    pkmn = Pokemon(pkmndict)
    pkmn.write_to_db()

    for skill in skills_var_list:  # this requires the main window code to be "global" in order to access this variable - that might be true of all tkinter code I've ever written, but still
        add_attr("skill", pkmn.name, skill.get())
    for likes in likes_var_list:
        add_attr("likes", pkmn.name, likes.get())

    find_best_matches(pkmn.name)


def get_existing(table):
    db = sqlite3.connect(DB_NAME)
    cursor = db.cursor()
    existing_items = [x[0] for x in cursor.execute("SELECT DISTINCT name FROM %s;" % table).fetchall()]
    db.close()
    return existing_items
    

if __name__=="__main__":
    root = tk.Tk()
    root.title("Pokopia Habitat Harmonizer")

    # Variables
    name_var         = tk.StringVar()
    location_var     = tk.StringVar()
    habitat_var      = tk.StringVar()
    skills_var_list  = [tk.StringVar(), tk.StringVar()]
    likes_var_list   = [tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.StringVar()]
    flavor_var       = tk.StringVar()
    satisfaction_var = tk.StringVar()
    house_var        = tk.BooleanVar(value=False)

    # Dropdown contents
    location_options     = ["Fuschia", "Vermillion", "Pewter", "Saffron", "Palette"]
    habitat_options      = ["Humid", "Dry", "Warm", "Cold", "Bright", "Dark"]
    flavor_options       = ["Sweet","Sour","Bitter","Dry"]
    satisfaction_options = ["Iffy","Average","Nice","Great","Awesome"]

    likes_suggestions    = get_existing("likes")
    skill_suggestions    = get_existing("skill")

    # Row 0: Name | TEXTBOX | Discovered | CHECKBOX
    tk.Label(root, text="Name").grid(row=0, column=0, sticky="w")
    tk.Entry(root, textvariable=name_var).grid(row=0, column=1, sticky="ew")

    # Row 1: Location | DROPDOWN | Habitat | DROPDOWN
    tk.Label(root, text="Location").grid(row=1, column=0, sticky="w")
    ttk.Combobox(root, textvariable=location_var,
                 values=location_options, state="readonly").grid(row=1, column=1, sticky="ew")
    tk.Label(root, text="Habitat").grid(row=1, column=2, sticky="w")
    ttk.Combobox(root, textvariable=habitat_var,
                 values=habitat_options, state="readonly").grid(row=1, column=3, sticky="ew")

    # Row 2: Skill 1 | DROPDOWN | Skill 2 | DROPDOWN
    tk.Label(root, text="Skill 1").grid(row=2, column=0, sticky="w")
    ttk.Combobox(root, textvariable=skills_var_list[0],
                 values=skill_suggestions, state="normal").grid(row=2, column=1, sticky="ew")
    tk.Label(root, text="Skill 2").grid(row=2, column=2, sticky="w")
    ttk.Combobox(root, textvariable=skills_var_list[1],
                 values=skill_suggestions, state="normal").grid(row=2, column=3, sticky="ew")

    # Row 3: Likes | TEXTBOX | TEXTBOX | TEXTBOX
    tk.Label(root, text="Likes").grid(row=3, column=0, sticky="w")
    ttk.Combobox(root, textvariable=likes_var_list[0],
                 values=likes_suggestions, state="normal").grid(row=3, column=1, sticky="ew")
    ttk.Combobox(root, textvariable=likes_var_list[1],
                 values=likes_suggestions, state="normal").grid(row=3, column=2, sticky="ew")
    ttk.Combobox(root, textvariable=likes_var_list[2],
                 values=likes_suggestions, state="normal").grid(row=3, column=3, sticky="ew")

    # Row 4: (empty) | TEXTBOX | TEXTBOX | DROPDOWN
    ttk.Combobox(root, textvariable=likes_var_list[3],
                 values=likes_suggestions, state="normal").grid(row=4, column=1, sticky="ew")
    ttk.Combobox(root, textvariable=likes_var_list[4],
                 values=likes_suggestions, state="normal").grid(row=4, column=2, sticky="ew")
    ttk.Combobox(root, textvariable=flavor_var,
                 values=flavor_options, state="readonly").grid(row=4, column=3, sticky="ew")

    # Row 5: Satisfaction | DROPDOWN | House | CHECKBOX
    tk.Label(root, text="Satisfaction").grid(row=5, column=0, sticky="w")
    ttk.Combobox(root, textvariable=satisfaction_var,
                 values=satisfaction_options, state="readonly").grid(row=5, column=1, sticky="ew")
    tk.Label(root, text="House").grid(row=5, column=2, sticky="w")
    tk.Checkbutton(root, variable=house_var).grid(row=5, column=3, sticky="w")

    # Row 6: (empty) | (empty) | (empty) | BUTTON
    tk.Button(root, text="Submit", command=route_input).grid(row=6, column=3, sticky="ew")

    # Run
    root.mainloop()