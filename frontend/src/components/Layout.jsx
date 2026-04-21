import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { LayoutDashboard, Camera, BarChart3, Lightbulb, User, LogOut } from 'lucide-react';
import toast, { Toaster } from 'react-hot-toast';
import { useEffect } from 'react';

export default function Layout() {
  const { user, logoutUser } = useAuth();
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
        
        // Render beautiful toast from Postgres Pub/Sub!
        toast.success(data.message, {
          duration: 6000,
          position: 'top-right',
          style: {
            border: '1px solid var(--accent-red)',
            padding: '16px',
            color: 'var(--text-primary)',
            background: 'var(--bg-card)'
          },
          icon: '🔔',
        });
      } catch (err) {
        console.error("Failed to parse notification:", err);
      }
    };

    eventSource.onerror = (err) => {
      console.error("SSE Connection Error:", err);
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, [user]);

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
