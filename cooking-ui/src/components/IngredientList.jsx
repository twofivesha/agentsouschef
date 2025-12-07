import styles from './IngredientList.module.css'

export function IngredientList({ ingredients, strikes, substitutions, onIngredientToggle }) {
  return (
    <div className={styles.container}>
      <ul className={styles.list}>
        {ingredients.map((ingredient, index) => {
          const isStruck = strikes.includes(ingredient)
          const substitute = substitutions[ingredient]
          const displayText = substitute 
            ? `${substitute} (instead of ${ingredient})`
            : ingredient
          
          return (
            <li 
              key={index}
              className={`${styles.item} ${isStruck ? styles.struck : ''}`}
              onClick={() => onIngredientToggle(ingredient)}
            >
              <span className={styles.checkbox}>
                {isStruck ? '☑' : '□'}
              </span>
              <span className={styles.text}>{displayText}</span>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
