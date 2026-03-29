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
        print("Wrote to database")
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
        self.fill_in_blanks_from_db(rs)
        db.close()
        return True

    def fill_in_blanks_from_db(self, rs):
        # rs is a sqlite3.Row returned by fetchone
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
        print("Wrote to database")
        db.close()

    def update_existing_pokemon(self):
        db = sqlite3.connect(DB_NAME)
        cursor = db.cursor()
        cursor.execute("UPDATE pokemon SET habitat=:habitat, location=:location, flavor=:flavor, discovered=:discovered, satisfaction=:satisfaction, houseid=:houseid WHERE name=:name;", self.__dict__)
        db.commit()
        print("Wrote to database")
        db.close()


def find_best_matches(name):
    db = sqlite3.connect(DB_NAME)
    db.row_factory = sqlite3.Row
    cursor = db.cursor()
    meaty_query = cursor.execute('''
        SELECT COUNT(*) as 'rating', p.name, p.location, p.satisfaction
--          , h.type, h.id, (SELECT COUNT(*) FROM pokemon WHERE houseid = h.id) AS currct, h.maxcount
          FROM likes pl
         INNER JOIN pokemon p ON pl.pokemon = p.name
--        INNER JOIN house h ON p.houseid = h.id
         WHERE p.name != ?
           AND p.habitat = (SELECT habitat FROM pokemon WHERE name = ?)
           AND pl.name  IN (SELECT DISTINCT name FROM likes WHERE pokemon = ?)
         GROUP BY p.name ORDER BY rating DESC;
        ''', (name, name, name))  # is there a better way to add these arguments...
    print("Your most compatible roommates:")
    for row in meaty_query.fetchall():
        print("\t".join(str(c) for c in row[:]))
    db.close()


def get_house_if_exists():
    global roomies_var_list, houseid

    db = sqlite3.connect(DB_NAME)
    cursor = db.cursor()
    rs = cursor.execute("SELECT DISTINCT houseid FROM pokemon WHERE name IN (?,?,?);", tuple(rv.get() for rv in roomies_var_list)).fetchone()
    if rs:
        houseid = rs[0]
        print("Found an existing house id %s with those roommates" % houseid)
    else:
        houseid = None
    db.close()
    return houseid


def insert_new_house(desc, maxoccupancy):
    global location_var, houseid, ditto_var

    db = sqlite3.connect(DB_NAME)
    cursor = db.cursor()
    cursor.execute("INSERT INTO house (location, type, ditto, maxoccupancy) VALUES (?,?,?,?);",
                   (location_var.get(), desc, int(ditto_var.get()), maxoccupancy))
    rs = cursor.execute("SELECT last_insert_rowid();").fetchone()
    if rs:
        houseid = rs[0]
    db.commit()
    print("Wrote to database")
    db.close()
    return houseid


def get_house_info():
    global root, type_var, size_var, location_var, houseid

    get_house_if_exists()

    if not houseid:
        int_occupancy = 1
        str_type = type_var.get()
        str_size = size_var.get()
        if str_type in ["Pink", "Orange", "Gray", "Yellow", "Minecraft"] or (str_size in ["House", "Office"] and str_type != "Poke Ball"):
            int_occupancy = 4
        elif str_size == "Cottage":
            int_occupancy = 2

        insert_new_house(str_type + " " + str_size, int_occupancy)

    root.destroy()


def add_attr(table, name, value):
    if value:
        db = sqlite3.connect(DB_NAME)
        cursor = db.cursor()
        cursor.execute("INSERT INTO %s (pokemon, name) VALUES (?, ?)" % table, (name, value))
        db.commit()
        print("Wrote to database")
        db.close()


def find_balanced_location(skill):
    if skill:
        db = sqlite3.connect(DB_NAME)
        cursor = db.cursor()
        load_bearing_query = cursor.execute('''
            SELECT COUNT(*) as 'count', p.location, s.name
              FROM pokemon p
             INNER JOIN skill s ON s.pokemon = p.name
             WHERE s.name = ?
               AND p.location != ''
             GROUP BY p.location
             ORDER BY count;
            ''', (skill,))
        print("Your %s skill might be needed in: " % skill)
        for row in load_bearing_query:
            print("\t".join(str(c) for c in row[:]))


def get_existing(table):
    db = sqlite3.connect(DB_NAME)
    cursor = db.cursor()
    existing_items = [x[0] for x in cursor.execute("SELECT DISTINCT name FROM %s;" % table).fetchall()]
    db.close()
    return existing_items


def route_input(*args):
    global root, name_var, location_var, habitat_var, skills_var_list, likes_var_list, flavor_var, satisfaction_var, house_var, houseid, roomies_var_list

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
    if not pkmn.exists():
        if house_var.get() and not houseid:
            house_info_window()
        pkmn.houseid = houseid
        pkmn.insert_new_pokemon()
        for skill in skills_var_list:
            add_attr("skill", pkmn.name, skill.get())
        for likes in likes_var_list:
            add_attr("likes", pkmn.name, likes.get())
    else:
        print("This Pokemon already exists in the database!")
        if house_var.get() and not pkmn.houseid:
            house_info_window()
            pkmn.houseid = houseid
        pkmn.update_existing_pokemon()

    if not pkmn.discovered:
        for skill in skills_var_list:
            find_balanced_location(skill.get())
    else:
        find_best_matches(pkmn.name)

    try:
        for rv in roomies_var_list:
            if rv.get():
                tmp_pkmn = Pokemon({"name":rv.get()})
                if not tmp_pkmn.exists():
                    print("Autosuggesting a new Pokemon...")
                    pokemon_window(auto_name=tmp_pkmn.name, auto_houseid=houseid, auto_location=location_var.get())
    except NameError:
        print("some lazy code just executed")

    pokemon_window()


def house_info_window():
    global root, type_var, size_var, roomies_var_list, ditto_var
    
    print("A house, you say?")
    root.destroy()
    root = tk.Tk()
    type_var = tk.StringVar()
    size_var = tk.StringVar()
    ditto_var = tk.BooleanVar(value=False)
    roomies_var_list = [tk.StringVar(),tk.StringVar(),tk.StringVar()]

    type_options = ["Leaf", "Sand", "Stone", "City", "Pink", "Orange", "Gray", "Yellow", "Poke Ball", "Minecraft"]
    size_options = ["Den", "Hut", "Cottage", "House", "Office"]

    # Row 1
    tk.Label(root, text="House info").grid(row=0, column=0, sticky="w")
    ttk.Combobox(root, textvariable=type_var, values=type_options, state="readonly").grid(row=0, column=1, sticky="ew")
    ttk.Combobox(root, textvariable=size_var, values=size_options, state="readonly").grid(row=0, column=2, sticky="ew")

    # Row 2
    tk.Label(root, text="Roomies (?)").grid(row=1, column=0, sticky="w")
    for i in range(len(roomies_var_list)):
        tk.Entry(root, textvariable=roomies_var_list[i]).grid(row=1, column=1+i, sticky="ew")

    # Row 3
    tk.Label(root, text="And Ditto?").grid(row=2, column=0, sticky="w")
    tk.Checkbutton(root, variable=ditto_var).grid(row=2, column=1, sticky="w")
    tk.Button(root, text="Submit", command=get_house_info).grid(row=2, column=3, sticky="ew")

    root.mainloop()


def pokemon_window(auto_name='', auto_location='', auto_houseid=0):
    global root, name_var, location_var, habitat_var, skills_var_list, likes_var_list, flavor_var, satisfaction_var, house_var, houseid

    try:
        root.destroy()
        print("Enter another Pokemon!")
    except NameError:
        print("Welcome to the Pokopia Habitat Harmonizer! Output shows up here.")
    except tk.TclError:
        print("Enter another Pokemon (code did something weird edition)")
    root = tk.Tk()
    root.title("Pokopia Habitat Harmonizer")
    
    houseid = auto_houseid

    # Variables
    name_var         = tk.StringVar(value=auto_name)
    location_var     = tk.StringVar(value=auto_location)
    habitat_var      = tk.StringVar()
    skills_var_list  = [tk.StringVar(), tk.StringVar()]
    likes_var_list   = [tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.StringVar()]
    flavor_var       = tk.StringVar()
    satisfaction_var = tk.StringVar()
    house_var        = tk.BooleanVar(value=houseid!=0)

    # Dropdown contents
    location_options     = ["Fuchsia", "Vermillion", "Pewter", "Saffron", "Palette"]
    habitat_options      = ["Humid", "Dry", "Warm", "Cold", "Bright", "Dark"]
    flavor_options       = ["Sweet", "Sour", "Bitter", "Dry", "Spicy"]
    satisfaction_options = ["Iffy", "Average", "Nice", "Great", "Awesome"]

    likes_suggestions    = get_existing("likes")
    likes_suggestions.sort()
    skill_suggestions    = get_existing("skill")
    skill_suggestions.sort()

    # Row 0
    tk.Label(root, text="Name").grid(row=0, column=0, sticky="w")
    tk.Entry(root, textvariable=name_var).grid(row=0, column=1, sticky="ew")

    # Row 1
    tk.Label(root, text="Location").grid(row=1, column=0, sticky="w")
    ttk.Combobox(root, textvariable=location_var,
                 values=location_options, state="readonly").grid(row=1, column=1, sticky="ew")
    tk.Label(root, text="Habitat").grid(row=1, column=2, sticky="w")
    ttk.Combobox(root, textvariable=habitat_var,
                 values=habitat_options, state="readonly").grid(row=1, column=3, sticky="ew")

    # Row 2
    tk.Label(root, text="Skill 1").grid(row=2, column=0, sticky="w")
    ttk.Combobox(root, textvariable=skills_var_list[0],
                 values=skill_suggestions, state="normal").grid(row=2, column=1, sticky="ew")
    tk.Label(root, text="Skill 2").grid(row=2, column=2, sticky="w")
    ttk.Combobox(root, textvariable=skills_var_list[1],
                 values=skill_suggestions, state="normal").grid(row=2, column=3, sticky="ew")

    # Row 3
    tk.Label(root, text="Likes").grid(row=3, column=0, sticky="w")
    ttk.Combobox(root, textvariable=likes_var_list[0],
                 values=likes_suggestions, state="normal").grid(row=3, column=1, sticky="ew")
    ttk.Combobox(root, textvariable=likes_var_list[1],
                 values=likes_suggestions, state="normal").grid(row=3, column=2, sticky="ew")
    ttk.Combobox(root, textvariable=likes_var_list[2],
                 values=likes_suggestions, state="normal").grid(row=3, column=3, sticky="ew")

    # Row 4
    ttk.Combobox(root, textvariable=likes_var_list[3],
                 values=likes_suggestions, state="normal").grid(row=4, column=1, sticky="ew")
    ttk.Combobox(root, textvariable=likes_var_list[4],
                 values=likes_suggestions, state="normal").grid(row=4, column=2, sticky="ew")
    ttk.Combobox(root, textvariable=flavor_var,
                 values=flavor_options, state="readonly").grid(row=4, column=3, sticky="ew")

    # Row 5
    tk.Label(root, text="Satisfaction").grid(row=5, column=0, sticky="w")
    ttk.Combobox(root, textvariable=satisfaction_var,
                 values=satisfaction_options, state="readonly").grid(row=5, column=1, sticky="ew")
    tk.Label(root, text="House").grid(row=5, column=2, sticky="w")
    tk.Checkbutton(root, variable=house_var).grid(row=5, column=3, sticky="w")

    # Row 6
    tk.Button(root, text="Submit", command=route_input).grid(row=6, column=3, sticky="ew")

    # Run
    root.mainloop()
    

if __name__=="__main__":
    if False:
        db = sqlite3.connect(DB_NAME)
        cursor = db.cursor()
        cursor.execute("DELETE FROM house WHERE id = 3;")
        db.commit()
        print("Wrote to database")
        db.close()
        print("got rid of them")
    pokemon_window()
    