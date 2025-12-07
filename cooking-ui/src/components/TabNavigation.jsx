import styles from './TabNavigation.module.css'

export function TabNavigation({ activeTab, onTabChange }) {
  const tabs = [
    { id: 'steps', label: '📋 STEPS' },
    { id: 'ingredients', label: '🥘 INGREDIENTS' },
    { id: 'status', label: '❓ STATUS' }
  ]
  
  return (
    <nav className={styles.navigation}>
      {tabs.map(tab => (
        <button
          key={tab.id}
          className={`${styles.tab} ${activeTab === tab.id ? styles.active : ''}`}
          onClick={() => onTabChange(tab.id)}
        >
          {tab.label}
        </button>
      ))}
    </nav>
  )
}
