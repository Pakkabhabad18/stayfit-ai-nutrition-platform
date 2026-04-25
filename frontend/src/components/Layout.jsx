import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useMeals } from '../context/MealContext';
import { LayoutDashboard, Camera, BarChart3, Lightbulb, User, LogOut } from 'lucide-react';
import toast, { Toaster } from 'react-hot-toast';
import { useEffect } from 'react';

export default function Layout() {
  const { user, logoutUser } = useAuth();
  const { fetchLatestAnalysis } = useMeals();
  const navigate = useNavigate();

  const handleLogout = () => {
    logoutUser();
    navigate('/login');
  };

  useEffect(() => {
    if (!user) return;
    
    // Connect to Notifications Microservice via SSE
    const token = localStorage.getItem('token');
    const eventSource = new EventSource(`http://localhost:5000/api/notifications/stream?token=${token}`);
    
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'ping') return;

        // Filter by user_id for security
        if (String(data.user_id) !== String(user.id)) return;

        if (data.type === 'calorie_alert') {
          toast(data.message, {
            duration: 6000,
            icon: '⚠️',
            style: {
              background: 'var(--bg-card)',
              color: 'var(--text-primary)',
              border: '1px solid var(--accent-red)'
            }
          });
        } else if (data.type === 'meal_analysis') {
          // Signal-based Observer: Fetch the actual data now that we know it's ready
          fetchLatestAnalysis(data.meal_id, data.task_id);
        }
      } catch (e) {
        console.error("Failed to parse SSE message:", e);
      }
    };

    eventSource.onerror = (err) => {
      console.error("SSE Connection Error:", err);
      eventSource.close();
      // In a real app, you might want to dispatch a "SSE_OFFLINE" event here
    };

    return () => {
      eventSource.close();
    };
  }, [user, fetchLatestAnalysis]);

  const navItems = [
    { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/log-meal', icon: Camera, label: 'Log Meal' },
    { to: '/analytics', icon: BarChart3, label: 'Analytics' },
    { to: '/recommendations', icon: Lightbulb, label: 'Recommendations' },
  ];

  return (
    <div className="app-layout">
      <Toaster />
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <div className="sidebar-logo-icon">🍎</div>
          <h1>StayFit</h1>
        </div>

        <nav className="sidebar-nav">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
            >
              <item.icon size={20} />
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-user">
          <div className="sidebar-user-info">
            <div className="sidebar-avatar">
              {user?.name?.charAt(0)?.toUpperCase() || 'U'}
            </div>
            <div>
              <div className="sidebar-user-name">{user?.name || 'User'}</div>
              <div className="sidebar-user-email">{user?.email || ''}</div>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <NavLink
              to="/profile"
              className="sidebar-link"
              style={{ flex: 1, justifyContent: 'center', padding: '8px' }}
            >
              <User size={16} />
              Profile
            </NavLink>
            <button
              onClick={handleLogout}
              className="sidebar-link"
              style={{ flex: 1, justifyContent: 'center', padding: '8px', color: 'var(--accent-red)' }}
            >
              <LogOut size={16} />
              Logout
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
