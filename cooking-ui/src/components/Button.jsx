import styles from './Button.module.css'

export function Button({ 
  variant = 'primary', 
  size = 'large',
  icon,
  children, 
  onClick,
  disabled = false 
}) {
  const className = `${styles.button} ${styles[variant]} ${styles[size]}`
  
  return (
    <button 
      className={className}
      onClick={onClick}
      disabled={disabled}
    >
      {icon && <span className={styles.icon}>{icon}</span>}
      {children}
    </button>
  )
}
