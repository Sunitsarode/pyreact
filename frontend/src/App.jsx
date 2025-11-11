import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import SymbolPage from './pages/SymbolPage';
import NotFound from './pages/NotFound';
import IndicatorsDashboard from './pages/IndicatorsDashboard';
import AllIndicatorsScorePage from './pages/AllIndicatorsScorePage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/indicators-dashboard" element={<IndicatorsDashboard />} />
        <Route path="/all-indicators-score/:symbol" element={<AllIndicatorsScorePage />} />
        <Route path="/:symbol" element={<SymbolPage />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;