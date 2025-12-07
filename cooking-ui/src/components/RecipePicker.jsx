// src/components/RecipePicker.jsx
import { useState, useEffect } from 'react'
import styles from './RecipePicker.module.css'

export function RecipePicker({ onRecipeSelect, currentRecipeKey }) {
  const [recipes, setRecipes] = useState([])
  const [searchTerm, setSearchTerm] = useState('')
  const [isOpen, setIsOpen] = useState(false)

  useEffect(() => {
    fetchRecipes()
  }, [])

  async function fetchRecipes() {
    try {
      const API_BASE = window.location.hostname === 'localhost' 
        ? 'http://localhost:8000' 
        : `http://${window.location.hostname}:8000`
      
      const response = await fetch(`${API_BASE}/recipes`)
      const data = await response.json()
      setRecipes(data)
    } catch (error) {
      console.error('Failed to fetch recipes:', error)
    }
  }

  const filteredRecipes = recipes.filter(recipe =>
    recipe.name.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const currentRecipe = recipes.find(r => r.key === currentRecipeKey)

  function handleSelect(recipeKey) {
    onRecipeSelect(recipeKey)
    setIsOpen(false)
    setSearchTerm('')
  }

  return (
    <div className={styles.container}>
      <button 
        className={styles.currentRecipe}
        onClick={() => setIsOpen(!isOpen)}
      >
        <span className={styles.recipeName}>
          {currentRecipe?.name || 'Select Recipe'}
        </span>
        <span className={styles.arrow}>{isOpen ? '▲' : '▼'}</span>
      </button>

      {isOpen && (
        <div className={styles.dropdown}>
          <input
            type="text"
            className={styles.search}
            placeholder="Search recipes..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            autoFocus
          />
          
          <div className={styles.list}>
            {filteredRecipes.length === 0 ? (
              <div className={styles.noResults}>No recipes found</div>
            ) : (
              filteredRecipes.slice(0, 50).map(recipe => (
                <button
                  key={recipe.key}
                  className={`${styles.item} ${recipe.key === currentRecipeKey ? styles.active : ''}`}
                  onClick={() => handleSelect(recipe.key)}
                >
                  <div className={styles.itemName}>{recipe.name}</div>
                  {recipe.description && (
                    <div className={styles.itemDesc}>{recipe.description}</div>
                  )}
                </button>
              ))
            )}
            {filteredRecipes.length > 50 && (
              <div className={styles.moreResults}>
                Showing first 50 of {filteredRecipes.length} results. Keep typing to narrow down...
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}