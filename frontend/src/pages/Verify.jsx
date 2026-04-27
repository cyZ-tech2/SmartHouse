import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import API from "../api";

export default function Verify() {
  const { token } = useParams();
  const [status, setStatus] = useState("loading"); // loading | success | error | already
  const [msg, setMsg] = useState("");

  useEffect(() => {
    API.get(`/verify/${token}/`)
      .then((r) => {
        setMsg(r.data.detail);
        setStatus(r.data.already ? "already" : "success");
      })
      .catch((err) => {
        setMsg(err.response?.data?.detail || "Erreur de validation.");
        setStatus("error");
      });
  }, [token]);

  return (
    <main className="container" id="main">
      <div className="form" style={{ textAlign: "center" }}>
        {status === "loading" && (
          <>
            <h2>Validation en cours…</h2>
            <p>⏳ Veuillez patienter…</p>
          </>
        )}
        {status === "success" && (
          <>
            <h2>✔ Compte activé !</h2>
            <div className="alert success">{msg}</div>
            <p>Vous pouvez maintenant vous connecter.</p>
            <Link to="/login" className="btn">Se connecter</Link>
          </>
        )}
        {status === "already" && (
          <>
            <h2>ℹ Email déjà validé</h2>
            <div className="alert info">{msg}</div>
            <Link to="/login" className="btn">Se connecter</Link>
          </>
        )}
        {status === "error" && (
          <>
            <h2>✖ Erreur</h2>
            <div className="alert error">{msg}</div>
            <Link to="/" className="btn ghost">Retour à l'accueil</Link>
          </>
        )}
      </div>
    </main>
  );
}
