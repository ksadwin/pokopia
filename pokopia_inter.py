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
            if columnname not in self.__dict__ or not self.__dict__[columnname]:
                self.__dict__[columnname] = rs[columnname]

    def write_to_db(self):
        if not self.exists():
            self.insert_new_pokemon()
        self.update_existing_pokemon()
        
    def insert_new_pokemon(self):
        if self.houseid == 0:
            self.houseid = None
        db = sqlite3.connect(DB_NAME)
        cursor = db.cursor()
        cursor.execute("INSERT OR IGNORE INTO pokemon (name, habitat, location, flavor, discovered, satisfaction, houseid) VALUES (:name, :habitat, :location, :flavor, :discovered, :satisfaction, :houseid);", self.__dict__)
        db.commit()
        print("Wrote to database")
        db.close()

    def update_existing_pokemon(self):
        if self.houseid == 0:
            self.houseid = None
        db = sqlite3.connect(DB_NAME)
        cursor = db.cursor()
        cursor.execute("UPDATE pokemon SET habitat=:habitat, location=:location, flavor=:flavor, discovered=:discovered, satisfaction=:satisfaction, houseid=:houseid WHERE name=:name;", self.__dict__)
        db.commit()
        print("Wrote to database")
        db.close()


def update_comfort_levels(comfort_level, str_namelist):
    global location_var

    new_pkmn = []

    for name in str_namelist.split(","):
        pkmn = Pokemon({"name": name.strip(), "location": location_var.get(), "satisfaction": comfort_level})
        if pkmn.exists():
            pkmn.write_to_db()
        else:
            new_pkmn.append(pkmn)

    return new_pkmn


def set_comfort_levels():
    global root, location_var, awesome_var, great_var, nice_var, average_var, iffy_var

    root.destroy()

    new_pkmn = []

    if awesome_var.get():
        new_pkmn.extend(update_comfort_levels("Awesome", awesome_var.get()))
    if great_var.get():
        new_pkmn.extend(update_comfort_levels("Great", great_var.get()))
    if nice_var.get():
        new_pkmn.extend(update_comfort_levels("Nice", nice_var.get()))
    if average_var.get():
        new_pkmn.extend(update_comfort_levels("Average", average_var.get()))
    if iffy_var.get():
        new_pkmn.extend(update_comfort_levels("Iffy", iffy_var.get()))

    for p in new_pkmn:
        pokemon_window(auto_name=p.name, auto_location=p.location, auto_satisfaction=p.satisfaction)


def find_best_matches(name):
    db = sqlite3.connect(DB_NAME)
    db.row_factory = sqlite3.Row
    cursor = db.cursor()
    meaty_query = cursor.execute('''
        SELECT p.name, p.location, p.satisfaction, COUNT(*) as 'rating', GROUP_CONCAT(pl.name, ', ')
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
        print("%-12s %-12s %-12s" % (row[:3]) + "\t".join(str(c) for c in row[3:]))
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
    global root, type_var, size_var, floor_var, location_var, houseid

    root.destroy()

    get_house_if_exists()

    if not houseid:
        int_occupancy = 1
        str_type = type_var.get()
        str_size = size_var.get()
        if floor_var.get():
            int_occupancy = 2
        elif str_type in ["Pink", "Orange", "Gray", "Yellow", "Minecraft"] or (str_size in ["House", "Office"] and str_type != "Poke Ball"):
            int_occupancy = 4
        elif str_size == "Cottage":
            int_occupancy = 2

        desc = str_type + " " + str_size
        if floor_var.get():
            desc += " " + floor_var.get()
        insert_new_house(desc, int_occupancy)


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
            ''', (skill,)).fetchall()
        if len(load_bearing_query) > 1:
            print("The %s skill might be needed in:" % skill)
            for row in load_bearing_query:
                print("\t".join(str(c) for c in row[:]))


def get_existing(table):
    db = sqlite3.connect(DB_NAME)
    cursor = db.cursor()
    existing_items = [x[0] for x in cursor.execute("SELECT DISTINCT name FROM %s;" % table).fetchall()]
    db.close()
    return existing_items


def rehome_by_name():
    global root, name_var

    root.destroy()

    pkmn = Pokemon({"name": name_var.get()})
    if not pkmn.exists():
        pokemon_window(auto_name=name_var.get())
    else:
        db = sqlite3.connect(DB_NAME)
        cursor = db.cursor()
        rs = cursor.execute("SELECT name FROM skill WHERE pokemon = ? ;", (pkmn.name,)).fetchall()
        db.close()
        for row in rs: 
            find_balanced_location(row[0])
        find_best_matches(pkmn.name)


def skill_lookup_wrapper():
    global root, skill_var

    root.destroy()

    skill_s = skill_var.get()
    if skill_s:
        for skill in skill_s.split(","):
            find_balanced_location(skill)
    else:
        for skill in get_existing("skill"):
            find_balanced_location(skill)


def route_input(*args):
    global root, name_var, location_var, habitat_var, skills_var_list, likes_var_list, flavor_var, satisfaction_var, house_var, houseid, roomies_var_list

    root.destroy()

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
        pass


def too_bad():
    global root

    print("well too bad because i ain't coded that yet")

    root.destroy()


def house_info_window():
    global root, type_var, size_var, floor_var, roomies_var_list, ditto_var
    
    try:
        root.destroy()
    except tk.TclError:
        pass

    root = tk.Tk()
    root.title("A house, you say?")
    type_var = tk.StringVar()
    size_var = tk.StringVar()
    floor_var = tk.StringVar()
    ditto_var = tk.BooleanVar(value=False)
    roomies_var_list = [tk.StringVar(),tk.StringVar(),tk.StringVar()]

    type_options = ["Leaf", "Sand", "Stone", "City", "Pink", "Orange", "Gray", "Yellow", "Poke Ball", "Minecraft"]
    size_options = ["Den", "Hut", "Cottage", "House", "Office"]
    floor_options = ["Floor 1", "Floor 2"]

    # Row 1
    tk.Label(root, text="House info").grid(row=0, column=0, sticky="w")
    ttk.Combobox(root, textvariable=type_var, values=type_options, state="readonly").grid(row=0, column=1, sticky="ew")
    ttk.Combobox(root, textvariable=size_var, values=size_options, state="readonly").grid(row=0, column=2, sticky="ew")
    ttk.Combobox(root, textvariable=floor_var, values=floor_options, state="readonly").grid(row=0, column=3, sticky="ew")

    # Row 2
    tk.Label(root, text="Roomies (?)").grid(row=1, column=0, sticky="w")
    for i in range(len(roomies_var_list)):
        tk.Entry(root, textvariable=roomies_var_list[i]).grid(row=1, column=1+i, sticky="ew")

    # Row 3
    tk.Label(root, text="And Ditto?").grid(row=2, column=0, sticky="w")
    tk.Checkbutton(root, variable=ditto_var).grid(row=2, column=1, sticky="w")
    tk.Button(root, text="Submit", command=get_house_info).grid(row=2, column=3, sticky="ew")

    root.mainloop()


def pokemon_window(auto_name='', auto_location='', auto_houseid=0, auto_satisfaction=''):
    global root, name_var, location_var, habitat_var, skills_var_list, likes_var_list, flavor_var, satisfaction_var, house_var, houseid

    try:
        root.destroy()
    except tk.TclError:
        pass
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
    satisfaction_var = tk.StringVar(value=auto_satisfaction)
    house_var        = tk.BooleanVar(value=houseid!=0)

    # Dropdown contents
    location_options     = ["Fuchsia", "Vermillion", "Pewter", "Saffron", "Palette"]
    habitat_options      = ["Humid", "Dry", "Warm", "Cool", "Bright", "Dark"]
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

#########################################################################################

def comfort_levels_window():
    global root, location_var, awesome_var, great_var, nice_var, average_var, iffy_var

    location_options = ["Fuchsia", "Vermillion", "Pewter", "Saffron", "Palette"]

    try:
        root.destroy()
    except tk.TclError:
        pass

    root = tk.Tk()
    root.title("Mass comfort updater")

    location_var = tk.StringVar()
    awesome_var = tk.StringVar()
    great_var = tk.StringVar()
    nice_var = tk.StringVar()
    average_var = tk.StringVar()
    iffy_var = tk.StringVar()

    tk.Label(root, text="Location").grid(row=0, column=0, sticky="w")
    ttk.Combobox(root, textvariable=location_var,
                 values=location_options, state="readonly").grid(row=0, column=1, sticky="ew")

    tk.Label(root, text="Enter comma-separated list of Pokemon names").grid(row=1, column=1, sticky="w")

    tk.Label(root, text="Awesome").grid(row=2, column=0, sticky="w")
    tk.Entry(root, textvariable=awesome_var).grid(row=2, column=1, sticky="ew")

    tk.Label(root, text="Great").grid(row=3, column=0, sticky="w")
    tk.Entry(root, textvariable=great_var).grid(row=3, column=1, sticky="ew")

    tk.Label(root, text="Nice").grid(row=4, column=0, sticky="w")
    tk.Entry(root, textvariable=nice_var).grid(row=4, column=1, sticky="ew")
    
    tk.Label(root, text="Average").grid(row=5, column=0, sticky="w")
    tk.Entry(root, textvariable=average_var).grid(row=5, column=1, sticky="ew")

    tk.Label(root, text="Iffy/No Home").grid(row=6, column=0, sticky="w")
    tk.Entry(root, textvariable=iffy_var).grid(row=6, column=1, sticky="ew")

    tk.Button(root, text="Submit", command=set_comfort_levels).grid(row=7, column=0, sticky="ew")

    root.mainloop()


def rehome_window():
    global root, name_var

    try:
        root.destroy()
    except tk.TclError:
        pass

    root = tk.Tk()
    root.title("Which Pokemon do you want to rehome?")

    name_var = tk.StringVar()

    tk.Label(root, text="Name").grid(row=0, column=0, sticky="w")
    tk.Entry(root, textvariable=name_var).grid(row=0, column=1, sticky="ew")

    tk.Button(root, text="Look for roommates", command=rehome_by_name).grid(row=1, column=1, sticky="ew")

    root.mainloop()


def skill_window():
    global root, skill_var

    try:
        root.destroy()
    except tk.TclError:
        pass

    root = tk.Tk()
    root.title("Check skill occurrence across locations")

    skill_var = tk.StringVar()
    tk.Label(root, text="Skill").grid(row=0, column=0, sticky="w")
    tk.Entry(root, textvariable=skill_var).grid(row=0, column=1, sticky="ew")

    tk.Label(root, text="(Leave blank to check all levels)").grid(row=1,column=1, sticky="w")
    tk.Button(root, text="Submit", command=skill_lookup_wrapper).grid(row=2, column=1, sticky="ew")

    root.mainloop()


def choose_a_window():
    global root

    try:
        root.destroy()
    except NameError:
        print("Welcome to the Pokopia Habitat Harmonizer! Output shows up here.")
    except tk.TclError:
        pass

    root = tk.Tk()
    root.title("Pokopia Habitat Harmonizer")
    tk.Label(root, text="What do you want to do?").grid(row=0, column=0, sticky="w")
    tk.Button(root, text="Quit", command=exit).grid(row=0, column=3, sticky="ew")

    tk.Button(root, text="Add new Pokemon", command=pokemon_window).grid(row=1, column=0, sticky="ew")
    tk.Button(root, text="Rehome a Pokemon", command=rehome_window).grid(row=1, column=1, sticky="ew")
    tk.Button(root, text="Set comfort levels", command=comfort_levels_window).grid(row=1, column=2, sticky="ew")
    tk.Button(root, text="Check skill spread", command=skill_window).grid(row=1,column=3, sticky="ew")


    root.mainloop()


if __name__=="__main__":
    if False:
        rename = {"Polywrath": "Poliwrath", "NInetales": "Ninetales", "Toxicitry (Amped)": "Toxicitry (amped)"}
        db = sqlite3.connect(DB_NAME)
        cursor = db.cursor()
        for k, v in rename.items():
            cursor.execute("UPDATE pokemon SET name = ? WHERE name = ?;", (v,k))
            print("Wrote to database")
        db.commit()
        db.close()

    while True:
        choose_a_window()
    