import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import API, { isLoggedIn } from "../api";

const TYPES = [
  ["energie", "Consommation énergétique"],
  ["securite", "Sécurité"],
  ["confort", "Confort"],
  ["divertissement", "Divertissement"],
  ["sante", "Santé & bien-être"],
];

const ICONS = {
  energie: "⚡", securite: "🔒", confort: "🛋", divertissement: "📺", sante: "❤",
};

export default function Services() {
  const nav = useNavigate();
  const [services, setServices] = useState([]);
  const [filters, setFilters] = useState({ type: "", active: "", q: "" });
  const logged = isLoggedIn();

  useEffect(() => {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([k, v]) => v !== "" && params.append(k, v));
    API.get("/services/?" + params.toString()).then((r) => setServices(r.data));
  }, [filters]);

  const set = (k, v) => setFilters({ ...filters, [k]: v });

  const handleClick = (id) => {
    if (logged) nav(`/services/${id}`);
    else nav("/login");
  };

  return (
    <main className="container" id="main">
      <h1>Services & outils SmartHouse</h1>
      <p>Services variés : consommation énergétique, sécurité, confort, divertissement…</p>

      {!logged && (
        <div className="alert info">
          🔒 Vous êtes en mode visiteur. <Link to="/login">Connectez-vous</Link> pour consulter les détails.
        </div>
      )}

      <section aria-label="Filtres">
        <div className="filters">
          <input placeholder="🔎 Recherche nom ou description…" value={filters.q}
                 onChange={(e) => set("q", e.target.value)}
                 aria-label="Recherche texte" />
          <select value={filters.type} onChange={(e) => set("type", e.target.value)} aria-label="Type">
            <option value="">Tous les types</option>
            {TYPES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>
          <select value={filters.active} onChange={(e) => set("active", e.target.value)} aria-label="Statut">
            <option value="">Tous les statuts</option>
            <option value="true">Actifs</option>
            <option value="false">Inactifs</option>
          </select>
        </div>
      </section>

      <p><strong>{services.length}</strong> service(s) trouvé(s)</p>

      <div className="cards">
        {services.map((s) => (
          <article key={s.id} className="card"
                   role="button" tabIndex={0}
                   style={{ cursor: "pointer" }}
                   onClick={() => handleClick(s.id)}
                   onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && handleClick(s.id)}
                   aria-label={`Voir ${s.name}`}>
            <p className="icon" aria-hidden="true">{ICONS[s.type] || "🔧"}</p>
            <h3>{s.name}</h3>
            <p>{s.description.slice(0, 100)}{s.description.length > 100 ? "…" : ""}</p>
            <p><strong>Type :</strong> {s.type_display}</p>
            {s.related_device_name && (
              <p><strong>Objet lié :</strong> {s.related_device_name}</p>
            )}
            <span className={"badge " + (s.active ? "on" : "off")}>
              {s.active ? "Actif" : "Inactif"}
            </span>
          </article>
        ))}
      </div>
    </main>
  );
}
