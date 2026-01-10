import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import { clsx } from 'clsx';
import { LanguageProvider, useLanguage, Language } from './i18n';
import Dashboard from './pages/Dashboard';
import WeeklyPlanning from './pages/WeeklyPlanning';
import DailyPlanning from './pages/DailyPlanning';
import Employees from './pages/Employees';
import RoomStates from './pages/RoomStates';
import ImportCSV from './pages/ImportCSV';

function LanguageSelector() {
  const { language, setLanguage } = useLanguage();

  return (
    <div className="flex items-center gap-1 bg-gray-100 rounded-lg p-1">
      <button
        onClick={() => setLanguage('es')}
        className={clsx(
          'px-3 py-1 rounded text-sm font-medium transition-colors',
          language === 'es'
            ? 'bg-white text-gray-900 shadow-sm'
            : 'text-gray-500 hover:text-gray-700'
        )}
      >
        ES
      </button>
      <button
        onClick={() => setLanguage('fr')}
        className={clsx(
          'px-3 py-1 rounded text-sm font-medium transition-colors',
          language === 'fr'
            ? 'bg-white text-gray-900 shadow-sm'
            : 'text-gray-500 hover:text-gray-700'
        )}
      >
        FR
      </button>
    </div>
  );
}

function Navigation() {
  const { t } = useLanguage();

  const navItems = [
    { path: '/', label: t.nav.dashboard },
    { path: '/weekly', label: t.nav.weeklyPlanning },
    { path: '/daily', label: t.nav.dailyPlanning },
    { path: '/employees', label: t.nav.employees },
    { path: '/rooms', label: t.nav.rooms },
    { path: '/import', label: t.nav.importCsv },
  ];

  return (
    <nav className="bg-white border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex space-x-8">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                clsx(
                  'inline-flex items-center px-1 pt-1 pb-2 border-b-2 text-sm font-medium',
                  isActive
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                )
              }
            >
              {item.label}
            </NavLink>
          ))}
        </div>
      </div>
    </nav>
  );
}

function AppContent() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-100">
        {/* Header */}
        <header className="bg-white shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex items-center">
                <h1 className="text-xl font-bold text-gray-900">
                  Le Kaila - Housekeeping
                </h1>
              </div>
              <div className="flex items-center">
                <LanguageSelector />
              </div>
            </div>
          </div>
        </header>

        {/* Navigation */}
        <Navigation />

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/weekly" element={<WeeklyPlanning />} />
            <Route path="/daily" element={<DailyPlanning />} />
            <Route path="/employees" element={<Employees />} />
            <Route path="/rooms" element={<RoomStates />} />
            <Route path="/import" element={<ImportCSV />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

function App() {
  return (
    <LanguageProvider>
      <AppContent />
    </LanguageProvider>
  );
}

export default App;
