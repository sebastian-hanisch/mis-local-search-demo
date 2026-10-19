# Unabhängige Menge im großen Maßstab: Reduktionen und Lokalsuche – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-mis-local-search-demo.streamlit.app/)** -->

Achtes Stück der **Härte-und-Struktur-Reihe** der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“ und der **Zusammenfluss der Stücke 3 und 6 mit einer Lokalsuche**. Die exakten Verfahren der Stücke 2, 3 und 6 ([max-clique-demo](https://github.com/sebastian-hanisch/max-clique-demo), [vertex-cover-demo](https://github.com/sebastian-hanisch/vertex-cover-demo), [tree-decomposition-dp-demo](https://github.com/sebastian-hanisch/tree-decomposition-dp-demo)) scheitern auf **großen, breiten** Graphen. Hier kommen **Reduktionsregeln** dazu (sie verkleinern den Graphen exakt) und eine **Lokalsuche** (der (1,2)-Tausch mit Plateausuche nach Andrade, Resende und Werneck), und die Frage lautet: **Wie viel löst die Vorverarbeitung, wie nah kommt die Suche an das Optimum, und wann reicht beides zusammen sogar für ein exaktes Ergebnis?**

```
Bron–Kerbosch: alle maximalen Cliquen (Wurzel)
 ├─ Größte Clique: Färbungsschranke und Kernzahl
 ├─ Knotenüberdeckung: Approximation, Kernbildung, Verzweigen
 ├─ Chordale und perfekte Graphen
 │    └─ Baumweite: Eliminationsordnung und Baumzerlegung
 │         └─ Dynamische Programmierung auf der Baumzerlegung
 ├─ Kantenclique-Überdeckung und Kernbildung
 └─ Unabhängige Menge im großen Maßstab: Reduktionen und Lokalsuche     [DIESES STÜCK]
```

## Warum dieses Problem

Der naheliegende Titel wäre „Reduktionen und Lokalsuche lösen große Graphen“. **Das stimmt nur dort, wo die Graphen dünn und unregelmäßig sind.** Die Messungen zeigen: Auf Zufallsnetzen mit mittlerem Grad 3, skalenfreien Netzen und dem King-Graphen **lösen die Regeln die Aufgabe vollständig** (Kern leer), auf dem Straßennetz bleiben 20,4 %, auf **Rastern und 3-regulären Graphen so gut wie alles**. Die Lokalsuche kommt nach 20 000 Iterationen bis auf 0,5 % an das Optimum und trifft es bei sechs von acht Netzen mit bewiesenem Optimum genau. Und es gibt ein überraschendes Ergebnis: **Reduktion + Zerlegung löst das ganze Toronto-Netz exakt** – die Breite sinkt von 50 auf 12, eine Aufgabe, an der die Zerlegung aus Stück 6 allein scheiterte.

Abgrenzung: Die Trajektorien-Metaheuristiken (`hill-climbing-`, `simulated-annealing-`, `iterated-local-search-`, `tabu-search-`, `guided-local-search-demo`) arbeiten auf einer **Rundtour** mit Tausch und 2-opt; keine kennt die unabhängige Menge, einen Tauschzug mit Plateau oder Reduktionsregeln. Die Störung der iterierten Lokalsuche dort (Doppelbrücke) entspricht dem Erzwingen eines Knotens hier. Stück 3 hat die Grad-1-Regel und den LP-Kern, aber keine Faltung, keine Dominanz und keine Lokalsuche.

## Modell

Ungerichteter Konfliktgraph G = (V, E): eine Kante heißt „diese beiden Sendungen dürfen nicht zusammen verladen werden“. Gesucht ist die größte Fuhre ohne Konflikt, also eine **größte unabhängige Menge** (Größe α). Netztypen (der Parameter bedeutet je Typ etwas anderes, die Hilfe der App nennt es): **Zufallsnetz** und **skalenfrei** (Barabási–Albert) mit dem mittleren Grad 2 + Parameter / 4; **zufällig 3-regulär** (Paarungsmodell mit Wiederholung), **Gitter**, **Dreiecksgitter** und **King-Graph** mit ungefähr n Knoten, bei denen der Parameter so viele Prozent der Kanten sperrt; **Toronto** (die n Kreuzungen, die dem Mittelpunkt des OpenStreetMap-Ausschnitts am nächsten liegen; Daten wie in `bfs-demo`, ODbL; bei Toronto sperrt der Parameter ebenfalls Kanten). Ungewichtet. Der Zufall kommt immer aus `random.Random(Zufalls-Seed)`.

**Daten und Lizenz:** Kartendaten © [OpenStreetMap-Mitwirkende](https://www.openstreetmap.org/copyright), Open Database License (ODbL) Version 1.0. `data/toronto_campus.json` ist derselbe Auszug wie in der Demo zur Breitensuche (5 072 Knoten, 7 621 ungerichtete Kanten) und steht deshalb ebenfalls unter der ODbL – siehe [data/LICENSE-ODbL.md](data/LICENSE-ODbL.md).

## Methodik

| Verfahren | Idee |
|---|---|
| **Grad 0 und Grad 1** | Ein Knoten ohne oder mit nur einem Nachbarn kommt in die Lösung, sein Nachbar raus (α(G) = α(G − N[v]) + 1). |
| **Dreieck** | Ein Knoten mit zwei verbundenen Nachbarn (simplizial) kommt in die Lösung, beide Nachbarn raus. |
| **Faltung** | Ein Knoten v mit zwei nicht benachbarten Nachbarn u, w wird mit ihnen zu einem neuen Knoten x verschmolzen, dessen Nachbarn die von u und w sind. α(G) = α(G') + 1; im Rücklift ersetzt x in der Lösung die Knoten u und w, sonst kommt v hinzu. |
| **Dominanz** | Gilt N[v] ⊆ N[u] für benachbarte u, v, entfällt u. |
| **Kern, Offset, Rücklift** | Die Regeln laufen bis zum Fixpunkt (die einfachste anwendbare Regel zuerst, Gleichstand: kleinster Knoten). α(G) = Offset + α(Kern); aus einer Lösung des Kerns wird in umgekehrter Reihenfolge eine des Originals. |
| **Greedy** | Knoten nach kleinstem Grad, jeder freie Knoten kommt hinein. |
| **Lokalsuche (vereinfachte ARW)** | Start beim Greedy; (1,2)-Tausch: einen Lösungsknoten entfernen und zwei nicht benachbarte Nachbarn einfügen, die nur ihn als Lösungsnachbarn haben; Störung: ein zufälliger Nichtlösungsknoten wird erzwungen, seine Lösungsnachbarn gehen, freie Knoten rücken nach, dann Abstieg; ein gleich gutes oder besseres Ergebnis wird angenommen, ein schlechteres mit der Wahrscheinlichkeit 1 / (1 + Abstand zur aktuellen · Abstand zur besten Größe), sonst über ein Protokoll rückgängig gemacht. |
| **Exakt über die Zerlegung** | Min-Fill-Ordnung des Kerns (nur wenn die Min-Grad-Elimination mit höchstens 25 Knoten je Beutel auskommt) und die DP aus Stück 6 mit Zellbudget 3 000 000 (gekürzte Kopie `mls_exact.py`). |
| **Satz von König** | Bei bipartiten Graphen ist α = n − ν (größtes Matching, Hopcroft–Karp); gibt für Raster einen exakten Vergleichswert, wenn die Zerlegung zu breit ist. |

Aufwand wird in **Knoten, Adjazenzzugriffen und Zellen** gezählt, nie in Sekunden; Laufzeiten stehen in keiner Zahl dieser README. Die App hat drei Tabs („Reduzieren“, „Suchen“, „Exakt?“), eine Kernfrage mit live berechnetem Verdikt und fünf Experimente. Die Suche bekommt immer dasselbe Zufalls-Seed (1).

## Befunde (gemessen, keine Behauptungen)

Jede Zahl steht in `tests/test_claims.py`. Alle Werte sind ganzzahlig und plattformunabhängig exakt; die Experimente laufen auf festen Instanzen, nie auf einem einzelnen Seed. Regeln: alle fünf.

| Frage | Befund |
|---|---|
| Standardfall (Zufallsnetz, 24 Knoten, Seed 5)? | 57 Kanten. Die Regeln legen 6 Knoten fest (1 Dreieck, 5 Faltungen) und streichen 4 dominierte Knoten; **Kern 7 Knoten (29,2 %)**. Seine Zerlegung (Breite 3, 78 Zellen) löst ihn: **α = 9**, Greedy 8. |
| Wie viel lösen die Regeln (Experiment 1, 10 Netze)? | **Kein Kern bei 4 von 10**: Zufall mit mittlerem Grad 3 (2 000 Knoten, 3 008 Kanten: Offset 1 076), skalenfrei mit 2 und mit 3 Kanten je Knoten (1 156 bzw. 1 004), King-Graph 20×20 (100). **Toronto ganz: Kern 1 036 von 5 072 Knoten (20,4 %)**, Offset 1 996; Toronto mit 2 000 Kreuzungen: 52 (2,6 %). Zufall mit Grad 4,5: 1 172 (58,6 %). **Gitter 40×40: 1 592 (99,5 %)**, Dreiecksgitter 30×30: 876 (97,3 %), **3-regulär n = 500: 500 (100 %)**. Die Faltung greift in diesen Netzen zusammen 1 680-mal. |
| Reduktion + Zerlegung auf Toronto (Experiment 2)? | Breite des ganzen Ausschnitts gegen die des Kerns: 1 000 Kreuzungen **17 → 3**, 2 000: **24 → 5**, 3 000: **34 → 10**, 4 000: **46 → 10**, ganz (5 072): **50 → 12**. Das ganze Netz wird **exakt gelöst**: Kern 1 036, 223 388 Zellen, **α = 2 448**. |
| Wie nah kommt die Lokalsuche (Experiment 3, 20 000 Iterationen)? | Gegen den bewiesenen Wert: Toronto ganz **2 435 gegen 2 448 (0,5 % darunter)**, Toronto 2 000: 989 gegen 991; Zufall Grad 3: 1 076 = α; skalenfrei: 1 156 = α und 1 004 = α; King: 100 = α; Gitter: 800 = α (König); Dreiecksgitter 12×12: 48 = α. **Sechs von acht bewiesenen Netzen trifft sie genau.** Greedy zum Vergleich: bis **24,3 % darunter** (Dreiecksgitter 30×30: 227 gegen 300). Ohne Beweis: Zufall Grad 4,5: 916 (bester gefundener Wert 918), Dreiecksgitter 30×30: 300, 3-regulär: 222. |
| Wie schnell? | Toronto ganz: 2 369 nach dem ersten Abstieg, 2 375 nach 100, 2 402 nach 1 000, 2 428 nach 5 000, 2 435 nach 20 000 Iterationen. Dreiecksgitter 30×30: 227 (Greedy), 245 nach 100, 283 nach 1 000, **300 nach 5 000**. Aufwand für 20 000 Iterationen auf Toronto: 2 650 138 Adjazenzzugriffe. |
| Lohnt die Reduktion vor der Suche (Experiment 4)? | Auf dem Kern erreicht die Suche bei **3 von 7 Netzen mehr** als auf dem ganzen Netz, bei keinem weniger: Toronto ganz **2 446 gegen 2 435** (α = 2 448), Toronto 2 000: 991 gegen 989, Zufall Grad 4,5: 918 gegen 916. Wo die Regeln nichts verkleinern (Gitter, 3-regulär, Dreiecksgitter), sind beide gleich. |
| Welche Regel trägt wie viel (Experiment 5)? | Kern in Knoten, alle fünf / ohne Faltung / ohne Dominanz: **Toronto 2 000: 52 / 897 / 154**; Zufall Grad 3: 0 / 21 / 0; **skalenfrei: 0 / 1 970 / 2 000**; **King-Graph: 0 / 0 / 400** (nur die Dominanz wirkt); Zufall Grad 4,5: 1 172 / 1 718 / 1 172. **Grad 1 und Dreieck sind Sonderfälle der Dominanz:** Ohne sie ändert sich mit der Dominanz nichts (5 von 5 Netzen); ohne die Dominanz wächst der Kern von Toronto 2 000 ohne Grad 1 von 154 auf **1 743**, ohne Dreieck auf **524**. Nur Grad 0 und 1: 1 036. |
| Presets? | **Lehrbeispiel**: α = 9, Kern 7. **Toronto ganz**: Greedy 2 308, Lokalsuche nach 5 000 Iterationen 2 428 (ganz) bzw. 2 445 (Kern), α = 2 448. **Dünn** (2 000 Knoten, 2 955 Kanten): Kern 0, α = 1 073, Greedy 1 026. **Raster** (Gitter 40×40, 3 120 Kanten): Kern 1 592, α = 800 nach König, Greedy 762. **Dreiecksgitter 30×30** nach 1 000 Iterationen: 283 (ganz), 290 (Kern), Greedy 227. **3-regulär** n = 500 (750 Kanten): Kern 500, Greedy 188, Lokalsuche 222. **King-Graph** ohne Dominanz: Kern 400. |

### Hypothesen aus dem Einzelplan

| Hypothese | Ergebnis |
|---|---|
| **H1** Die Reduktionen sind exakt (Offset + α(Kern) = α, Rücklift unabhängig) | ✅ Gleich `scipy.optimize.milp` auf 300 Zufallsgraphen für jede der fünf Regelmengen und auf 150 je Regel allein; gleich Brute Force auf 80 Graphen; der Rücklift ist jedes Mal unabhängig und genau so groß. |
| **H2** Auf dünnen Graphen lösen die Regeln fast alles | ✅ Kern 0 bei Zufall Grad 3, skalenfrei und King; Toronto ganz 20,4 %; ⚠ **Raster und 3-regulär: 97 bis 100 % Kern**, Zufall mit Grad 4,5 noch 58,6 %. |
| **H3** Die Faltung ist die wichtigste Regel, die Dominanz fängt Sonderfälle | ⚠ **Teilweise**: Ohne Faltung wird der Kern bei 4 von 5 Netzen größer, ohne Dominanz bei 3; **der King-Graph und die skalenfreien Netze brauchen die Dominanz**, Grad 1 und Dreieck sind ihre Sonderfälle. |
| **H4** Greedy liegt deutlich unter dem Optimum | ✅ 2,9 bis 5,7 % auf dünnen Netzen, **24,3 % auf dem Dreiecksgitter 30×30**. |
| **H5** Die ARW-Lokalsuche kommt schnell nah heran | ✅ Bis 0,5 % unter dem Optimum nach 20 000 Iterationen; exakt bei sechs von acht bewiesenen Netzen; ohne Beweis erreicht sie 300 (Dreiecksgitter) nach 5 000 Iterationen. |
| **H6** Reduktion verbessert die Lokalsuche | ✅ bei 3 von 7 Netzen, nie schlechter (Toronto 2 446 gegen 2 435). |
| **H7** Reduktion macht die Zerlegung auf großen Straßennetzen möglich | ✅ Breite 50 → 12, ganz Toronto exakt (α = 2 448). |
| **H8** Die Lokalsuche ist billig | ✅ 20 000 Iterationen kosten auf Toronto 2,65 Mio. Adjazenzzugriffe (nur Operationen werden festgeschrieben, keine Zeiten). |

## Befunde und Korrekturen gegenüber dem Plan

- **Die Kerngrößen der Vormessung wurden reproduziert** (Toronto ganz 1 036 und mit 2 000 Kreuzungen 52, Zufall Grad 3: 0 und Grad 4,5: 1 172, skalenfrei 0, Gitter 1 592, Dreiecksgitter 876, 3-regulär 500). Die **Regelzähler weichen ab**, weil hier nach jeder Anwendung die einfachste Regel wieder zuerst läuft (Toronto ganz: 740 Faltungen statt 933 in der Vormessung); Kern und α hängen davon nicht ab.
- **Grad 1 und Dreieck sind überflüssig, sobald die Dominanz läuft.** Das ist eine mathematische Folge (ein Blatt v mit Nachbar u erfüllt N[v] ⊆ N[u]; ein Knoten mit verbundenen Nachbarn erfüllt N[v] ⊆ N[u] für beide), und die Ablation bestätigt es. Sie bleiben, weil die einfachste Regel zuerst läuft und das Protokoll lesbar bleibt.
- **Bipartite Netze löst der Satz von König**, wie im Einzelplan als Referenz für Gitter vorgesehen; umgesetzt mit Hopcroft–Karp, gegen `networkx` und `milp` geprüft. Sonst müsste die Zerlegung des Gitters (Breite 40) gerechnet werden.
- **Kein Satz „die Lokalsuche schlägt `milp`“.** `milp` mit Zeitlimit ist auf dichten Instanzen nicht reproduzierbar (die Vormessung sah beim 3-regulären Graphen zwei verschiedene Werte, 221 und 223); die Demo vergleicht die Lokalsuche nur mit **bewiesenen** Werten oder nennt den Vergleichswert „bester gefundener Wert“.
- **Toronto kappt bei 5 072 Kreuzungen:** größere n gelten für die anderen Netztypen.

## Ehrliche Grenzen

- **Vereinfachte Lokalsuche.** Iterierte (1,2)-Suche nach Andrade, Resende und Werneck ohne ihre Neustarts, ohne (2,3)-Tausch und ohne inkrementelle Kandidatenlisten; die Ergebnisse gelten für diese Fassung.
- **Stand der Technik nur als Einordnung:** Branch-and-Reduce-Löser (Akiba und Iwata), evolutionäre Verfahren mit Kernbildung (ReduMIS, Lamm u. a.) und Reduktionen mit linearer Laufzeit (Chang, Li, Zhang) sind stärker und nicht nachgebaut; ebenso NuMVC.
- **Kein Beweis der Lokalsuche.** Ohne exakten Wert ist „bester gefundener Wert“ nur eine Untergrenze; auf dem 3-regulären Netz, dem Dreiecksgitter 30×30 und dem Zufallsnetz mit Grad 4,5 ist das Optimum hier nicht bekannt.
- **Exakt nur bei schmalem Kern.** Die Zerlegung rechnet bis etwa Breite 18 bis 19 (Zellbudget 3 000 000); bipartite Netze löst der Satz von König trotzdem.
- **Ungewichtet; Aufwand in Zugriffen und Zellen, nicht in Zeit; synthetische Netze** außer dem Toronto-Ausschnitt.

## Verifikation

- **Kern:** jede Einheit (jede Regel einzeln, Rücklift, Greedy, (1,2)-Tausch, Rückgängigmachen der Störung, Zweifärbung, Hopcroft–Karp, die kopierte Zerlegung und DP) gegen Handrechnung auf den Mini-Instanzen (Pfad P4: α = 2, Dreieck mit Pendel: 2, Stern: 3, K3: 1, Fünfeck: 2, K4: 1, Petersen-Graph: 4, Gitter 3×3: 5); die Faltung am Fünfeck (Knoten 0, neuer Knoten 5, danach ein Dreieck, Rücklift zu {0, 2}) ist auf Papier nachgerechnet.
- **Orakel (`tests/test_oracle_mis_local_search.py`):** Offset + α(Kern) gleich `scipy.optimize.milp` auf **300 festen Zufallsinstanzen** für jede der fünf Regelmengen, jede Regel allein auf 150 Instanzen, Brute Force (80 Graphen), acht größere Strukturgraphen und Toronto-Ausschnitte (60 bis 600 Kreuzungen); der Rücklift ist unabhängig; die Lokalsuche ist immer unabhängig, nie über α, nie unter dem Greedy, auf kleinen Graphen (40 Instanzen) gleich α; Satz von König gegen `networkx` und `milp`.
- **Zweige (`tests/test_branches.py`):** jede Regel greift, jede Ablation vergrößert den Kern (Grad 1 und Dreieck erst ohne Dominanz), jeder Status der exakten Stufe kommt vor, jeder Zweig des Verdikts.
- **Mutationsprüfung** (`tools/oracle_mutation.py`, 40 Mutanten, mit ganzer Suite): Rate 74 %. Von den zehn Überlebenden sind neun äquivalent (Sortierreihenfolgen, Schleifengrenzen, die den letzten Index überspringen, ohne dass etwas fehlt, die Schwelle für „ungültig“ in der kopierten DP, die Zahl der Versuche bei der Störung); für den zehnten (die Prüfung unabhängiger Mengen in der kopierten Datei) wurde danach ein Test ergänzt.
- **Zahlen:** `tests/test_claims.py` rechnet jede Zahl dieser README über dieselben Auswertungsfunktionen wie die App nach; `tests/test_verdicts.py` prüft jeden Verdikt-Text an handgesetzten Werten.
- **Oberfläche:** AppTest-Rauchtest (jeder Button, jeder Regler an Minimum und Maximum, jeder Netztyp, jede Regelmenge, Extrem-Seeds, Permalink, Preset-Hervorhebung, fester Kopf) und Footer-Test.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App: drei Tabs, Kernfrage, fünf Experimente, Brücken, Grenzen, Mathematik |
| `data/LICENSE-ODbL.md` | Lizenz der OpenStreetMap-Daten |
| `data/toronto_campus.json` | der Toronto-Ausschnitt (5 072 Knoten) aus `bfs-demo` |
| `mls_bipartite.py` | Zweifärbung, Hopcroft–Karp, α bipartiter Graphen |
| `mls_constants.py` | Regler-Grenzen, Rechengrenzen, Regelmengen, Farben, Presets |
| `mls_evaluation.py` | Einstellungen, Analyse, exakte Stufe (Regeln, Zerlegung, König) und Verdikt der Hauptansicht |
| `mls_exact.py` | gekürzte, unveränderte Kopie aus Stück 5 und 6: Eliminationsordnung, Zerlegung, DP |
| `mls_experiments.py` | die fünf Experimente mit ihren Verdikten |
| `mls_layout.py` | fester Kopf (Gerüst aus `new_demo.py`) |
| `mls_presets.py` | Permalink (Begrenzen), Presets in der Seitenleiste mit Hervorhebung, Zufalls-Seed-Button |
| `mls_reductions.py` | die fünf Regeln, Fixpunkt, Rücklift |
| `mls_scenario.py` | Netze und feste Vergleichsgraphen |
| `mls_search.py` | Greedy und Lokalsuche (iterierter (1,2)-Tausch) |
| `mls_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `requirements-dev.txt` | Laufzeit plus pytest, networkx und scipy (nur für die Gegenproben) |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt; kein scipy und kein networkx zur Laufzeit) |
| `tests/` | Regeln, Suche, Zerlegung, Bipartit, Orakel, Zweige, Szenarien, Zahlen, Verdikte, Figuren, Presets, Layout, AppTest, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **NuMVC, ReduMIS, Branch-and-Reduce:** der Stand der Technik, hier nur Einordnung.
- **Gewichtete Varianten** (gewichtet: Stück 6).
- **Weitere Regeln** (Zwillinge, LP, Unconfined): nicht gebaut.
- **PDF-Export:** die Demo zeigt ein Verfahren und Messungen, keine Planungsunterlage.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

## Literatur

- Andrade, D. V., Resende, M. G. C., & Werneck, R. F. (2012). *Fast local search for the maximum independent set problem.* Journal of Heuristics 18(4), 525–547.
- Akiba, T., & Iwata, Y. (2016). *Branch-and-reduce exponential/FPT algorithms in practice: A case study of vertex cover.* Theoretical Computer Science 609, 211–225.
- Lamm, S., Sanders, P., Schulz, C., Strash, D., & Werneck, R. F. (2017). *Finding near-optimal independent sets at scale.* Journal of Heuristics 23(4), 207–229.
- Chang, L., Li, W., & Zhang, W. (2017). *Computing a near-maximum independent set in linear time by reducing-peeling.* Proceedings of SIGMOD 2017.

Gebaut mit Streamlit, Plotly und pandas.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
