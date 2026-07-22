import { BrowserRouter, Routes, Route } from "react-router-dom";

import Landing from "../pages/Landing";

function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
      </Routes>
    </BrowserRouter>
  );
}

export default AppRouter;