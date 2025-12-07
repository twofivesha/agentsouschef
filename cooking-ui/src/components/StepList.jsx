import styles from './StepList.module.css'

export function StepList({ steps, currentStep, onStepToggle }) {
  return (
    <div className={styles.container}>
      <ul className={styles.list}>
        {steps.map((step, index) => {
          const isCompleted = index < currentStep
          const isCurrent = index === currentStep
          
          return (
            <li 
              key={index}
              className={`${styles.item} ${isCompleted ? styles.completed : ''} ${isCurrent ? styles.current : ''}`}
              onClick={() => onStepToggle(index)}
            >
              <span className={styles.number}>{index + 1}.</span>
              {isCurrent && <span className={styles.arrow}>➤</span>}
              <span className={styles.text}>{step}</span>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
