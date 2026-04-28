import { useState, useEffect, useRef } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { isLoggedIn, getUser, clearAuth, isAdvanced, isAdmin, refreshUser } from "../api";

export default function Navbar() {
  const nav = useNavigate();
  const location = useLocation();
  const [openMenu, setOpenMenu] = useState(null);
  const [user, setUser] = useState(getUser());
  const ref = useRef(null);

  const logged = isLoggedIn();
  const advanced = isAdvanced();
  const admin = isAdmin();

  useEffect(() => {
    if (logged) {
      refreshUser().then(setUser).catch(() => {});
    }
    setOpenMenu(null);
  }, [location.pathname]);

  useEffect(() => {
    const handler = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpenMenu(null);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const logout = () => { clearAuth(); nav("/login"); };
  const toggle = (name) => setOpenMenu(openMenu === name ? null : name);

  return (
    <nav className="navbar" aria-label="Navigation principale" ref={ref}>
      <Link to="/" className="brand">🏠 SmartHouse</Link>

      <div className="links">
        <Link to="/">Accueil</Link>

        {/* Catégorie : Explorer */}
        <div className="dropdown">
          <button className="dropdown-btn" onClick={() => toggle("explore")}
                  aria-expanded={openMenu === "explore"}>
            Explorer ▾
          </button>
          {openMenu === "explore" && (
            <div className="dropdown-menu">
              <Link to="/devices">🔌 Objets connectés</Link>
              <Link to="/services">🔧 Services</Link>
            </div>
          )}
        </div>

        {/* Mon espace (connecté, sauf admin pour Mes demandes) */}
        {logged && (
          <div className="dropdown">
            <button className="dropdown-btn" onClick={() => toggle("space")}
                    aria-expanded={openMenu === "space"}>
              Mon espace ▾
            </button>
            {openMenu === "space" && (
              <div className="dropdown-menu">
                <Link to="/dashboard">📊 Tableau de bord</Link>
                <Link to="/profile">👤 Profil</Link>
                <Link to="/level">🏆 Niveau</Link>
                {/* Admin n'envoie pas de demandes → pas d'onglet "Mes demandes" */}
                {!admin && <Link to="/my-requests">📩 Mes demandes</Link>}
              </div>
            )}
          </div>
        )}

        {/* Gestion (avancé/expert + pas enfant) */}
        {logged && advanced && (
          <div className="dropdown">
            <button className="dropdown-btn" onClick={() => toggle("manage")}
                    aria-expanded={openMenu === "manage"}>
              Gestion ▾
            </button>
            {openMenu === "manage" && (
              <div className="dropdown-menu">
                <Link to="/devices/add">➕ Ajouter un objet</Link>
                <Link to="/maintenance">🛠 Maintenance</Link>
                <Link to="/history">📜 Historique</Link>
                <Link to="/stats">📈 Statistiques</Link>
                {admin && <Link to="/admin-requests">🛡 Gérer demandes</Link>}
              </div>
            )}
          </div>
        )}

        {!logged && <Link to="/login">Connexion</Link>}
        {!logged && <Link to="/register">Inscription</Link>}
        {logged && (
          <a href="#" className="logout-link"
             onClick={(e) => { e.preventDefault(); logout(); }}>
            Déconnexion ({user?.username})
          </a>
        )}
      </div>
    </nav>
  );
}
