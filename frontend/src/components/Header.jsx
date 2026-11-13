import { useState } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../auth";

export default function Header() {
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const nav = useNavigate();
  const close = () => setOpen(false);

  return (
    <header className="hdr">
      <div className="container hdr-in">
        <Link to="/" className="brand" onClick={close}>
          <img src="/icon-256.png" alt="Savivah Netcore" />
          <span><b>Nyumbani Finder</b><small>by Savivah Netcore</small></span>
        </Link>
        <button className="burger" aria-label="Menu" onClick={() => setOpen(!open)}>{open ? "✕" : "☰"}</button>
        <nav className={"nav" + (open ? " open" : "")} onClick={close}>
          <NavLink to="/search">Find a house</NavLink>
          {user && ["landlord", "admin"].includes(user.role) && <NavLink to="/post">Post a house</NavLink>}
          {user && ["landlord", "admin"].includes(user.role) && <NavLink to="/dashboard">My listings</NavLink>}
          {user?.role === "admin" && <NavLink to="/admin">Admin</NavLink>}
          {user ? (
            <button className="link" onClick={() => { logout(); nav("/"); }}>Log out ({user.full_name.split(" ")[0]})</button>
          ) : (
            <>
              <NavLink to="/login">Log in</NavLink>
              <Link to="/register" className="btn sm">Sign up</Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
