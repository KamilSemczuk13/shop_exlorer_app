# Types of errors that generator can insert into data
ERR_NULL="NULL values"
ERR_FAKE_NULL='Fake NULLs ("null", "none", "")'
ERR_INCONSISTENT='Inconsistent spellings ("polska" / "PL" / "Polonia")'
ERR_OUT_OF_RANGE="Out of range values (Quantity <= 0, negative price)"
ERR_BAD_DATE="Impossible dates (2024-06-32, 2024-13-05)"

# Data that generator uses to create clean records (no apostrophes, names are used in sql filters)
FIRST_NAMES=[
    # Polish
    "Anna", "Piotr", "Marta", "Jan", "Ewa", "Tomasz", "Karolina", "Kamil", "Natalia", "Adam",
    "Michał", "Zofia", "Paweł", "Ola", "Katarzyna", "Krzysztof", "Agnieszka", "Andrzej", "Magdalena", "Marcin",
    "Joanna", "Łukasz", "Aleksandra", "Grzegorz", "Monika", "Jakub", "Dorota", "Mateusz", "Barbara", "Bartosz",
    "Justyna", "Dawid", "Beata", "Rafał", "Weronika", "Szymon", "Alicja", "Wojciech", "Julia", "Sebastian",
    "Patrycja", "Mariusz", "Izabela", "Damian", "Paulina", "Robert", "Emilia", "Przemysław", "Hanna", "Filip",
    "Lena", "Dariusz", "Iwona", "Artur", "Kinga", "Maciej", "Sylwia", "Wiktor", "Gabriela", "Hubert",
    "Oliwia", "Igor", "Martyna", "Kacper", "Klaudia", "Oskar", "Ewelina", "Norbert", "Daria", "Jacek",
    # English
    "John", "Jane", "Michael", "Emily", "David", "Sarah", "James", "Jessica", "Richard", "Ashley",
    "William", "Olivia", "Daniel", "Emma", "Matthew", "Sophia", "Christopher", "Madison", "Andrew", "Abigail",
    "Joshua", "Elizabeth", "Ryan", "Chloe", "Brandon", "Grace", "Tyler", "Hannah", "Kevin", "Megan",
    "Jason", "Rachel", "Eric", "Lauren", "Brian", "Samantha", "Justin", "Natalie", "Steven", "Victoria",
    "Nathan", "Amanda", "Patrick", "Nicole", "Gregory", "Stephanie", "Aaron", "Rebecca", "Sean", "Heather",
    # German
    "Hans", "Lukas", "Leon", "Felix", "Jonas", "Maximilian", "Paul", "Moritz", "Tobias", "Florian",
    "Sabine", "Ursula", "Petra", "Heike", "Greta", "Lea", "Mia", "Johanna", "Frieda", "Klara",
    # French
    "Marie", "Pierre", "Louis", "Camille", "Antoine", "Juliette", "Nicolas", "Manon", "Hugo", "Chloé",
    "Mathieu", "Amélie", "Théo", "Céline", "Julien", "Élodie", "Baptiste", "Margaux", "Clément", "Inès",
    # Spanish
    "Luis", "Carlos", "Javier", "Sofía", "Lucía", "Diego", "Pablo", "Carmen", "Alejandro", "Isabel",
    "Miguel", "Elena", "Sergio", "Paula", "Raúl", "Rocío", "Álvaro", "Nuria", "Adrián", "Pilar",
    # Chinese
    "Zhang", "Wei", "Li", "Ming", "Jing", "Hui", "Xiao", "Lei", "Yan", "Fang",
    "Hao", "Ling", "Jun", "Mei", "Tao", "Xin", "Bo", "Qing", "Yu", "Chen",
]

LAST_NAMES=[
    # Polish
    "Nowak", "Kowalski", "Zielińska", "Kowal", "Lewandowski", "Wiśniewska", "Mazur", "Kaczmarek", "Wójcik", "Kamińska",
    "Szymański", "Woźniak", "Dąbrowski", "Kozłowska", "Jankowski", "Wojciechowska", "Kwiatkowski", "Krawczyk", "Piotrowski", "Grabowska",
    "Nowakowski", "Pawłowska", "Michalski", "Nowicka", "Adamczyk", "Dudek", "Zając", "Wieczorek", "Jabłoński", "Król",
    "Majewska", "Olszewski", "Jaworska", "Wróbel", "Malinowski", "Pawlak", "Witkowska", "Walczak", "Stępień", "Górski",
    "Rutkowska", "Michalak", "Sikora", "Ostrowski", "Baran", "Duda", "Szewczyk", "Tomaszewska", "Pietrzak", "Marciniak",
    "Wróblewski", "Zalewska", "Jakubowski", "Jasiński", "Zawadzka", "Sadowski", "Bąk", "Chmielewska", "Włodarczyk", "Borkowski",
    "Czarnecka", "Sawicki", "Sokołowska", "Urbański", "Kubiak", "Maciejewska", "Szczepański", "Kucharska", "Wilk", "Kalinowski",
    # English
    "Smith", "Doe", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis", "Wilson", "Anderson",
    "Taylor", "Thomas", "Moore", "Jackson", "Martin", "Lee", "Thompson", "White", "Harris", "Clark",
    "Lewis", "Robinson", "Walker", "Young", "Allen", "King", "Wright", "Scott", "Green", "Baker",
    "Adams", "Nelson", "Hill", "Campbell", "Mitchell", "Roberts", "Carter", "Phillips", "Evans", "Turner",
    "Parker", "Collins", "Edwards", "Stewart", "Morris", "Murphy", "Cook", "Rogers", "Morgan", "Cooper",
    # German
    "Müller", "Schmidt", "Schneider", "Fischer", "Weber", "Meyer", "Wagner", "Becker", "Schulz", "Hoffmann",
    "Schäfer", "Koch", "Bauer", "Richter", "Klein", "Wolf", "Schröder", "Neumann", "Schwarz", "Zimmermann",
    # French
    "Dubois", "Durand", "Lefebvre", "Moreau", "Laurent", "Simon", "Michel", "Leroy", "Roux", "David",
    "Bertrand", "Morel", "Fournier", "Girard", "Bonnet", "Dupont", "Lambert", "Fontaine", "Rousseau", "Vincent",
    # Spanish
    "García", "Fernández", "González", "Rodríguez", "López", "Martínez", "Sánchez", "Pérez", "Gómez", "Ruiz",
    "Hernández", "Jiménez", "Díaz", "Moreno", "Muñoz", "Álvarez", "Romero", "Navarro", "Torres", "Domínguez",
    # Chinese
    "Wang", "Zhang", "Liu", "Chen", "Yang", "Huang", "Zhao", "Wu", "Zhou", "Xu",
    "Sun", "Ma", "Zhu", "Hu", "Guo", "He", "Gao", "Lin", "Luo", "Zheng",
]

# Product names and price range of category (min, max), first products are like in original db
PRODUCTS_BY_CATEGORY={
    "Electronics":([
        "Laptop 13\"", "Laptop 14\"", "Laptop 15\"", "Laptop 16\"", "Laptop 17\"",
        "Smartphone X", "Smartphone Y", "Smartphone Z", "Smartphone Mini", "Smartphone Ultra",
        "Monitor 24", "Monitor 27", "Monitor 32\"", "Monitor Curved 34\"", "Gaming Laptop",
        "Desktop PC", "Mini PC", "All-in-One PC", "Game Console", "Smart TV 55\"",
    ], 1099, 4199),
    "Audio":([
        "Headphones", "Earbuds", "Speaker", "Speaker Max", "Headphones Pro",
        "Earbuds Pro", "Speaker Mini", "Soundbar", "Soundbar Pro", "Studio Monitors",
        "Gaming Headset", "Wireless Microphone", "Turntable", "Portable Radio", "Party Speaker",
    ], 199.9, 599),
    "Photo":([
        "Camera", "Camera Pro", "Mirrorless Camera", "Action Camera", "Instant Camera",
        "Compact Camera", "Lens 50mm", "Lens 24-70mm", "Camera Drone", "Gimbal",
    ], 1999, 2499),
    "Tablets":([
        "Tablet Mini", "Tablet Pro", "Tablet Air", "Tablet 10\"", "Tablet 12\"",
        "Tablet Kids", "Drawing Tablet", "E-Reader", "Tablet Pro Max", "Tablet Lite",
    ], 2299, 2499),
    "Wearables":([
        "Smart Watch", "Smart Watch Pro", "Smart Watch Sport", "Fitness Band", "Smart Ring",
        "Smart Glasses", "Kids Watch", "GPS Watch", "Sleep Tracker", "Smart Watch Mini",
    ], 899, 899),
}
