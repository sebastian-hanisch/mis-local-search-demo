"""Konstanten: Regler-Grenzen, Rechengrenzen, feste Annahmen, Farben und Presets."""

N_MIN, N_MAX, DEFAULT_N = 6, 5072, 24
PAR_MIN, PAR_MAX, DEFAULT_PAR = 0, 60, 12                # Parameter (Bedeutung je Netztyp, siehe NET_HELP)
SEED_MAX, DEFAULT_SEED = 999999, 5
ITER_MIN, ITER_MAX, ITER_STEP, DEFAULT_ITER = 0, 50_000, 500, 5000
SWEEP_SEEDS = tuple(range(100000, 100005))               # feste Instanzen für Sweeps; die Suche selbst bekommt SEARCH_SEED
SEARCH_SEED = 1

# Netztypen
NET_TYPES = {
    "random": "Zufallsnetz (jedes Paar unabhängig)",
    "scalefree": "Skalenfrei (Barabási–Albert)",
    "regular": "Zufällig 3-regulär",
    "grid": "Gitter (Straßenraster, bipartit)",
    "tri": "Dreiecksgitter (Raster mit einer Diagonale)",
    "king": "King-Graph (Raster mit beiden Diagonalen)",
    "toronto": "Toronto (echte Straßen)",
}
DEFAULT_NET = "random"
NET_HELP = (
    "Der Parameter bedeutet je Netztyp etwas anderes. Zufallsnetz und skalenfrei: mittlerer Grad = 2 + Parameter / 4 (bei skalenfrei bringt jeder neue Knoten die Hälfte davon als Kanten mit). "
    "Zufällig 3-regulär: n Knoten (gerade Zahl), jeder mit genau drei Nachbarn; der Parameter sperrt so viele Prozent der Kanten. "
    "Gitter, Dreiecksgitter, King-Graph: ein Raster mit ungefähr n Knoten (Seitenlänge ⌊√n⌉), der Parameter sperrt so viele Prozent der Kanten. "
    "Toronto: die n Kreuzungen, die dem Mittelpunkt am nächsten liegen (OpenStreetMap, ODbL); der Parameter sperrt so viele Prozent der Kanten."
)
PAR_LABEL = "Parameter (Bedeutung je Netztyp)"

# Regelmengen (Auswahl in der Seitenleiste)
RULESETS = {
    "all": ("degree0", "degree1", "triangle", "fold", "domination"),
    "no_fold": ("degree0", "degree1", "triangle", "domination"),
    "no_domination": ("degree0", "degree1", "triangle", "fold"),
    "basic": ("degree0", "degree1"),
    "none": (),
}
RULESET_NAMES = {
    "all": "alle fünf Regeln",
    "no_fold": "ohne Faltung",
    "no_domination": "ohne Dominanz",
    "basic": "nur Grad 0 und 1",
    "none": "keine Regel",
}
RULESET_ORDER = ("all", "no_fold", "no_domination", "basic", "none")
DEFAULT_RULESET = "all"

# Rechengrenzen
EXACT_CELL_BUDGET = 3_000_000    # Vorhersage Σ 2^Beutel: darüber startet die DP nicht
ORDER_WIDTH_LIMIT = 24           # Min-Grad-Breite über dieser Grenze: gar nicht erst Min-Fill rechnen („zu breit“)
FULL_WIDTH_MAX_N = 6000          # größte Knotenzahl, für die die Breite des ganzen Graphen gerechnet wird
BRUTE_MAX_N = 18                 # größte Knotenzahl der Brute-Force-Probe
DRAW_MAX_N = 400                 # größte Knotenzahl, die gezeichnet wird
DRAW_LABEL_MAX_N = 60            # bis zu dieser Knotenzahl werden die Knoten beschriftet
LOG_ROWS = 40                    # so viele Schritte des Protokolls zeigt die Hauptansicht
CHECKPOINTS = (0, 10, 100, 1000, 5000, 20000)

# Experimente
FAMILY_SEED = 1
TORONTO_NS = (1000, 2000, 3000, 4000)
SEARCH_ITERATIONS = 20_000

# Farben
COLOR_CHOSEN = "#c0504d"
COLOR_FREE = "#9fb3c8"
COLOR_KERNEL = "#e0a030"
COLOR_EDGE = "rgba(150,150,150,0.35)"
COLOR_OK = "#2F6B65"
COLOR_BLUE = "#4c78a8"
COLOR_BAD = "#c0504d"
COLOR_PALETTE = ("#2F6B65", "#4c78a8", "#e0a030", "#c0504d", "#8e6bbf", "#d17b9e", "#6c9a3a", "#6a7b8b")

PRESETS = {
    "Lehrbeispiel (Zufallsnetz mit 24 Knoten)": {"net": "random", "n": 24, "par": 12, "seed": 5, "rules": "all", "iters": 5000},
    "Toronto: das ganze Netz": {"net": "toronto", "n": 5072, "par": 0, "seed": 5, "rules": "all", "iters": 5000},
    "Dünn: die Regeln lösen alles": {"net": "random", "n": 2000, "par": 4, "seed": 5, "rules": "all", "iters": 5000},
    "Raster: die Regeln tun nichts": {"net": "grid", "n": 1600, "par": 0, "seed": 5, "rules": "all", "iters": 5000},
    "Dreiecksgitter: die Suche braucht Zeit": {"net": "tri", "n": 900, "par": 0, "seed": 5, "rules": "all", "iters": 1000},
    "3-regulär: die Suche ohne Beweis": {"net": "regular", "n": 500, "par": 0, "seed": 5, "rules": "all", "iters": 20000},
    "King-Graph: nur die Dominanz": {"net": "king", "n": 400, "par": 0, "seed": 5, "rules": "no_domination", "iters": 5000},
}
PRESET_HELP = {
    "Lehrbeispiel (Zufallsnetz mit 24 Knoten)": "24 Knoten, 57 Kanten: Die Regeln legen 6 Knoten fest (Dreieck, Faltungen, Dominanz) und lassen einen Kern von 7; seine Zerlegung (Breite 3, 78 Zellen) löst ihn: α = 9, der Greedy findet 8. Gut zum Durchklicken des Protokolls.",
    "Toronto: das ganze Netz": "5 072 Kreuzungen, 7 621 Kanten: Der Kern hat 1 036 Knoten bei einem Offset von 1 996; seine Zerlegung (Breite 12, 223 388 Zellen) löst ihn exakt: α = 2 448. Greedy 2 308, Lokalsuche nach 5 000 Iterationen 2 428 (ganzes Netz) bzw. 2 445 (Kern).",
    "Dünn: die Regeln lösen alles": "2 000 Knoten, 2 955 Kanten (mittlerer Grad rund 3): Kein Kern bleibt, α = 1 073 steht durch die Regeln fest; der Greedy findet 1 026.",
    "Raster: die Regeln tun nichts": "Gitter 40×40 (3 120 Kanten): Der Kern hat 1 592 von 1 600 Knoten, die Zerlegung ist zu breit; α = 800 gibt der Satz von König (bipartit). Die Lokalsuche findet 800, der Greedy 762.",
    "Dreiecksgitter: die Suche braucht Zeit": "Dreiecksgitter 30×30 (2 581 Kanten): Der Kern hat 876 von 900 Knoten, die Zerlegung ist zu breit. Nach 1 000 Iterationen findet die Suche 283 (ganzes Netz) bzw. 290 (Kern), der Greedy 227; mit 5 000 Iterationen sind es 300 (Experiment 3), ein Beweis fehlt.",
    "3-regulär: die Suche ohne Beweis": "500 Knoten, 750 Kanten: Keine Regel greift (Kern 500), die Zerlegung ist zu breit. Greedy 188, Lokalsuche nach 20 000 Iterationen 222; das Optimum ist nicht bekannt.",
    "King-Graph: nur die Dominanz": "King-Graph 20×20 ohne die Dominanz: Kern 400 von 400 Knoten. Mit allen fünf Regeln ist der Kern leer und α = 100.",
}
