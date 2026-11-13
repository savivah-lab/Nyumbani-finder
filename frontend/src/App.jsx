import { Route, Routes, useLocation } from "react-router-dom";
import { useEffect } from "react";
import Header from "./components/Header";
import Footer from "./components/Footer";
import Protected from "./components/Protected";
import Home from "./pages/Home";
import Search from "./pages/Search";
import ListingDetail from "./pages/ListingDetail";
import { Login, Register } from "./pages/AuthPages";
import Dashboard from "./pages/Dashboard";
import PostListing from "./pages/PostListing";
import Admin from "./pages/Admin";

function ScrollTop() {
  const { pathname } = useLocation();
  useEffect(() => { window.scrollTo(0, 0); }, [pathname]);
  return null;
}

export default function App() {
  return (
    <>
      <ScrollTop />
      <Header />
      <main className="page">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/search" element={<Search />} />
          <Route path="/listing/:id" element={<ListingDetail />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/dashboard" element={<Protected roles={["landlord", "admin"]}><Dashboard /></Protected>} />
          <Route path="/post" element={<Protected roles={["landlord", "admin"]}><PostListing /></Protected>} />
          <Route path="/admin" element={<Protected roles={["admin"]}><Admin /></Protected>} />
          <Route path="*" element={<div className="container center"><h2>Page not found</h2><a href="/">Back home</a></div>} />
        </Routes>
      </main>
      <Footer />
    </>
  );
}
