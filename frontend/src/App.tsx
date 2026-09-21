import { Route, Routes } from "react-router-dom";
import { MarketingHome } from "./pages/MarketingHome";
import { LoginPlaceholder } from "./pages/LoginPlaceholder";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<MarketingHome />} />
      <Route path="/login" element={<LoginPlaceholder />} />
    </Routes>
  );
}
