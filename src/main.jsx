import React, { useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const stations = [
  "Pont de Neuilly",
  "La Defense",
  "Charles de Gaulle - Etoile",
  "Chatelet",
  "Gare de Lyon",
  "Bercy",
  "Place d'Italie",
  "Villejuif - Louis Aragon",
];

const routeSteps = [
  { line: "M1", label: "Pont de Neuilly", detail: "Direction Chateau de Vincennes", color: "#ffcd00" },
  { line: "M1", label: "Chatelet", detail: "Correspondance courte estimee a 4 min", color: "#ffcd00" },
  { line: "M7", label: "Place d'Italie", detail: "Direction Villejuif - Louis Aragon", color: "#f59bbb" },
  { line: "M7", label: "Villejuif - Louis Aragon", detail: "Arrivee prevue a 08:43", color: "#f59bbb" },
];

const buildItems = [
  ["Parser GTFS", "done"],
  ["Filtrer metro et RER", "done"],
  ["Charger trips et calendriers", "done"],
<<<<<<< HEAD
  ["Construire le graphe horaire", "done"],
  ["Dijkstra et correspondances", "active"],
=======
  ["Construire le graphe horaire", "active"],
  ["Dijkstra et correspondances", "next"],
>>>>>>> 2d99fea7656d838f1d4ecfd24e4ba00f847f835f
  ["Carte interactive finale", "next"],
];

function App() {
  const [from, setFrom] = useState("Pont de Neuilly");
  const [to, setTo] = useState("Villejuif - Louis Aragon");
  const [mode, setMode] = useState("route");

  const summary = useMemo(() => {
    const transferCount = from.includes("Pont") && to.includes("Villejuif") ? 1 : 2;
    return {
      duration: transferCount === 1 ? "38 min" : "44 min",
      transfers: transferCount,
      confidence: transferCount === 1 ? "Donnees GTFS en cours d'integration" : "",
    };
  }, [from, to]);

  return (
    <main className="app-shell">
      <aside className="sidebar" aria-label="Panneau de recherche">
        <div className="brand">
          <span className="brand-mark">M</span>
          <div>
            <h1>Metro Efrei Dodo</h1>
          </div>
        </div>

        <section className="panel-section">
          <div className="section-title">
            <span>Itineraire</span>
            <strong>Preview</strong>
          </div>
          <label>
            Depart
            <select value={from} onChange={(event) => setFrom(event.target.value)}>
              {stations.map((station) => (
                <option key={station}>{station}</option>
              ))}
            </select>
          </label>
          <label>
            Arrivee
            <select value={to} onChange={(event) => setTo(event.target.value)}>
              {stations.map((station) => (
                <option key={station}>{station}</option>
              ))}
            </select>
          </label>
          <div className="field-grid">
            <label>
              Date
              <input type="date" defaultValue="2024-02-27" />
            </label>
            <label>
              Heure
              <input type="time" defaultValue="08:05" />
            </label>
          </div>
          <button className="primary-button" type="button">Afficher le trajet</button>
        </section>

        <section className="panel-section compact">
          <div className="section-title">
            <span>Algorithmes</span>
            <strong>En cours</strong>
          </div>
          <div className="tool-row">
            <button type="button" aria-pressed={mode === "route"} onClick={() => setMode("route")}>Trajet</button>
            <button type="button" aria-pressed={mode === "mst"} onClick={() => setMode("mst")}>Kruskal</button>
            <button type="button" aria-pressed={mode === "connect"} onClick={() => setMode("connect")}>Connexite</button>
          </div>
        </section>

        <section className="panel-section compact">
          <div className="section-title">
            <span>Avancement</span>
            <strong>2 / 6</strong>
          </div>
          <ol className="progress-list">
            {buildItems.map(([label, state]) => (
              <li key={label} data-state={state}>
                <span />
                {label}
              </li>
            ))}
          </ol>
        </section>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            {mode !== "route" && (
              <h2>{mode === "mst" ? "Arbre couvrant minimum" : "Test de connexite du reseau"}</h2>
            )}
          </div>
        </header>

        <div className="content-grid">
          <section className="map-board" aria-label="Plan metro preview">
            <MetroMap mode={mode} from={from} to={to} />
          </section>

          <aside className="result-panel" aria-label="Resultat simule">
            <div className="route-summary">
              <span>{summary.duration}</span>
              <div>
                <strong>{from}</strong>
                <small>vers {to}</small>
              </div>
            </div>
            <div className="metric-grid">
              <div>
                <strong>{summary.transfers}</strong>
                <span>correspondance</span>
              </div>
              <div>
                <strong>14</strong>
                <span>stations</span>
              </div>
              <div>
                <strong>92%</strong>
                <span>reseau pret</span>
              </div>
            </div>
            {summary.confidence && <p className="hint">{summary.confidence}</p>}
            <div className="timeline">
              {routeSteps.map((step) => (
                <article key={`${step.line}-${step.label}`} className="step">
                  <span className="line-badge" style={{ background: step.color }}>{step.line}</span>
                  <div>
                    <strong>{step.label}</strong>
                    <p>{step.detail}</p>
                  </div>
                </article>
              ))}
            </div>
          </aside>
        </div>
      </section>
    </main>
  );
}

function MetroMap({ mode, from, to }) {
  return (
    <div className={`metro-map metro-map-${mode}`}>
      <svg viewBox="0 0 900 620" role="img" aria-label={`Trajet preview de ${from} a ${to}`}>
        <defs>
          <filter id="softShadow" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="10" stdDeviation="12" floodColor="#223047" floodOpacity="0.18" />
          </filter>
        </defs>
        <path className="river" d="M-20 370 C 140 300, 230 420, 380 350 S 650 270, 920 340" />
        <path className="line line-yellow" d="M95 245 H260 C330 245 340 315 410 315 H765" />
        <path className="line line-pink" d="M420 120 V245 C420 300 485 315 485 375 V535" />
        <path className="line line-blue" d="M165 470 C230 385 330 410 390 315 C440 240 550 250 710 160" />
        <path className="line line-green ghost" d="M140 150 C245 190 275 300 360 330 S590 420 790 445" />
        <path className="route-glow" d="M95 245 H260 C330 245 340 315 410 315 H485 V535" />
        {[
          [95, 245, "Pont de Neuilly"],
          [260, 245, "La Defense"],
          [410, 315, "Chatelet"],
          [565, 315, "Gare de Lyon"],
          [485, 375, "Place d'Italie"],
          [485, 535, "Villejuif"],
          [710, 160, "Etoile"],
          [790, 445, "Bercy"],
        ].map(([x, y, label], index) => (
          <g className="station" key={label} transform={`translate(${x} ${y})`}>
            <circle r={index === 0 || index === 5 ? 15 : 11} />
            <text x="18" y={index % 2 ? 28 : -18}>{label}</text>
          </g>
        ))}
        <g className="floating-card" filter="url(#softShadow)">
          <rect x="580" y="42" width="238" height="92" rx="8" />
          <text x="604" y="78">Simulation Dijkstra</text>
          <text x="604" y="108">cout horaire + transferts</text>
        </g>
      </svg>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);
