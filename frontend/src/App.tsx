import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import { clsx } from 'clsx';
import Dashboard from './pages/Dashboard';
import WeeklyPlanning from './pages/WeeklyPlanning';
import DailyPlanning from './pages/DailyPlanning';
import Employees from './pages/Employees';
import RoomStates from './pages/RoomStates';
import ImportCSV from './pages/ImportCSV';

const navItems = [
  { path: '/', label: 'Dashboard' },
  { path: '/weekly', label: 'Planning Semanal' },
  { path: '/daily', label: 'Planning Diario' },
  { path: '/employees', label: 'Personal' },
  { path: '/rooms', label: 'Habitaciones' },
  { path: '/import', label: 'Importar CSV' },
];

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-100">
        {/* Header */}
        <header className="bg-white shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex items-center">
                <h1 className="text-xl font-bold text-gray-900">
                  Housekeeping Planning
                </h1>
              </div>
            </div>
          </div>
        </header>

        {/* Navigation */}
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

export default App;
