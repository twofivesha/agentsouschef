import styles from './StatusView.module.css'

export function StatusView({ currentStep, steps, ingredients, strikes, substitutions }) {
  const currentStepText = steps[currentStep]
  
  return (
    <div className={styles.container}>
      <section className={styles.section}>
        <h2 className={styles.heading}>CURRENT STEP:</h2>
        <p className={styles.currentStep}>
          {currentStepText || 'All steps complete! 🎉'}
        </p>
      </section>
      
      <section className={styles.section}>
        <h2 className={styles.heading}>INGREDIENTS:</h2>
        <ul className={styles.ingredientList}>
          {ingredients.map((ingredient, index) => {
            const isStruck = strikes.includes(ingredient)
            const substitute = substitutions[ingredient]
            const displayText = substitute 
              ? `${substitute} (instead of ${ingredient})`
              : ingredient
            
            return (
              <li key={index} className={`${styles.ingredient} ${isStruck ? styles.struck : ''}`}>
                <span className={styles.checkbox}>{isStruck ? '☑' : '□'}</span>
                <span>{displayText}</span>
              </li>
            )
          })}
        </ul>
      </section>
    </div>
  )
}
