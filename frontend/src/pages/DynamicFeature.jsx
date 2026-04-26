import { useParams, Link } from "react-router-dom";
import { User, Database, BarChart2, Activity, ChevronRight, GitCompare } from "lucide-react";
import ProfileView from "../components/ProfileView";
import RepositoryView from "../components/RepositoryView";
import ComparisonView from "../components/ComparisonView";

export default function DynamicFeature() {
  const { category, username } = useParams();

  // Map category to the active viewing component
  const renderCategory = () => {
    switch (category) {
      case "profile":
        return <ProfileView username={username} />;
      case "repositories":
        return <RepositoryView username={username} />;
      case "compare":
        return <ComparisonView />;
      default:
        return (
          <div className="glass-panel text-center" style={{ padding: '4rem 2rem' }}>
            <Activity size={48} className="muted mb-4" style={{ margin: '0 auto' }} />
            <h2 className="muted">Unknown Module: {category}</h2>
            <p className="muted">Select an active module from the sidebar.</p>
          </div>
        );
    }
  };

  const menuItems = [
    { title: "Profile Analysis", icon: User, path: "profile" },
    { title: "Repository Data", icon: Database, path: "repositories" },
    { title: "Head-to-Head Compare", icon: GitCompare, path: "compare" }
  ];

  return (
    <div className="container animate-fade-in" style={{ display: 'grid', gridTemplateColumns: '250px 1fr', gap: '2rem', minHeight: '80vh' }}>
      
      {/* Sidebar Navigation */}
      <aside>
        <div className="glass-panel" style={{ position: 'sticky', top: '6rem' }}>
          <h3 style={{ marginBottom: '1.5rem', fontSize: '1rem', textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--text-muted)' }}>
            Modules
          </h3>
          <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {menuItems.map((item) => {
              const active = category === item.path;
              const linkPath = username ? `/app/${item.path}/${username}` : `/app/${item.path}`;
              
              return (
                <Link 
                  key={item.path} 
                  to={linkPath}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '0.8rem 1rem',
                    borderRadius: '8px',
                    background: active ? 'rgba(239, 68, 68, 0.1)' : 'transparent',
                    borderLeft: active ? '3px solid var(--accent-1)' : '3px solid transparent',
                    color: active ? 'var(--accent-1)' : 'var(--text-muted)',
                    fontWeight: active ? 600 : 400,
                    transition: 'all 0.2s ease'
                  }}
                >
                  <div className="flex-row gap-2">
                    <item.icon size={18} />
                    {item.title}
                  </div>
                  {active && <ChevronRight size={16} />}
                </Link>
              );
            })}
          </nav>
        </div>
      </aside>

      {/* Main Dynamic Content Area */}
      <main>
        {renderCategory()}
      </main>

    </div>
  );
}
