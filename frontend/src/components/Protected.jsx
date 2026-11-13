import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../auth";
import Loading from "./Loading";

export default function Protected({ roles, children }) {
  const { user, ready } = useAuth();
  const loc = useLocation();
  if (!ready) return <Loading />;
  if (!user) return <Navigate to={`/login?next=${encodeURIComponent(loc.pathname + loc.search)}`} replace />;
  if (roles && !roles.includes(user.role))
    return (
      <div className="container">
        <p className="notice">This page is only for landlord/caretaker accounts. Sign up with a landlord account to post houses.</p>
      </div>
    );
  return children;
}
