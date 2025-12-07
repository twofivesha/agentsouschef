#!/bin/bash

# Agent Sous Chef UI - Automated Setup Script
# This creates the complete React PWA structure

set -e  # Exit on any error

echo "🚀 Setting up Agent Sous Chef UI..."
echo ""

# Create directory structure
echo "📁 Creating directories..."
mkdir -p cooking-ui/src/components
mkdir -p cooking-ui/src/styles
mkdir -p cooking-ui/public

# package.json
echo "📦 Creating package.json..."
cat > cooking-ui/package.json << 'EOF'
{
  "name": "agent-sous-chef-ui",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "devDependencies": {
    "@types/react": "^18.3.12",
    "@types/react-dom": "^18.3.1",
    "@vitejs/plugin-react": "^4.3.4",
    "vite": "^6.0.1",
    "vite-plugin-pwa": "^0.20.5"
  }
}
EOF

# vite.config.js
echo "⚙️  Creating vite.config.js..."
cat > cooking-ui/vite.config.js << 'EOF'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['icon.png'],
      manifest: {
        name: 'Agent Sous Chef',
        short_name: 'Sous Chef',
        description: 'Your AI cooking assistant',
        theme_color: '#4CAF50',
        background_color: '#ffffff',
        display: 'standalone',
        icons: [
          {
            src: 'icon.png',
            sizes: '512x512',
            type: 'image/png'
          }
        ]
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg}']
      }
    })
  ],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
})
EOF

# index.html
echo "📄 Creating index.html..."
cat > cooking-ui/index.html << 'EOF'
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/png" href="/icon.png" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
    <meta name="theme-color" content="#4CAF50" />
    <meta name="description" content="Your AI cooking assistant" />
    <link rel="apple-touch-icon" href="/icon.png" />
    <link rel="manifest" href="/manifest.json" />
    <title>Agent Sous Chef</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
EOF

# src/main.jsx
echo "🔧 Creating src/main.jsx..."
cat > cooking-ui/src/main.jsx << 'EOF'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './styles/variables.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
EOF

# src/styles/variables.css
echo "🎨 Creating src/styles/variables.css..."
cat > cooking-ui/src/styles/variables.css << 'EOF'
/* Design System Variables */

:root {
  /* Colors */
  --color-primary: #4CAF50;
  --color-primary-hover: #45a049;
  --color-primary-active: #3d8b40;
  
  --color-grey: #888888;
  --color-grey-light: #e0e0e0;
  --color-text: #212121;
  --color-text-light: #666666;
  --color-background: #ffffff;
  
  --color-highlight: #FFF9C4;
  --color-highlight-border: #F9A825;
  
  /* Spacing */
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  --spacing-xl: 32px;
  
  /* Button Heights */
  --button-height-large: 60px;
  --button-height-medium: 50px;
  --button-height-small: 44px;
  
  /* Typography */
  --font-size-header: 24px;
  --font-size-tab: 18px;
  --font-size-step: 16px;
  --font-size-button: 18px;
  --font-size-small: 14px;
  
  --font-weight-normal: 400;
  --font-weight-semibold: 600;
  --font-weight-bold: 700;
  
  /* Border Radius */
  --radius-small: 4px;
  --radius-medium: 8px;
  --radius-large: 12px;
  
  /* Transitions */
  --transition-fast: 150ms ease;
  --transition-normal: 250ms ease;
  
  /* Shadows */
  --shadow-small: 0 1px 3px rgba(0, 0, 0, 0.12);
  --shadow-medium: 0 2px 8px rgba(0, 0, 0, 0.15);
  
  /* Layout */
  --max-width: 800px;
  --header-height: 60px;
  --tab-height: 50px;
}

/* Reset & Base Styles */
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: var(--color-text);
  background: var(--color-background);
}

button {
  font-family: inherit;
  cursor: pointer;
}

/* Accessibility */
button:focus-visible {
  outline: 3px solid var(--color-primary);
  outline-offset: 2px;
}
EOF

# src/App.jsx
echo "⚛️  Creating src/App.jsx..."
cat > cooking-ui/src/App.jsx << 'EOF'
import { useState, useEffect } from 'react'
import styles from './App.module.css'
import { TabNavigation } from './components/TabNavigation'
import { StepList } from './components/StepList'
import { IngredientList } from './components/IngredientList'
import { StatusView } from './components/StatusView'
import { Button } from './components/Button'

const API_BASE = import.meta.env.DEV ? '/api' : 'http://localhost:8000'

function App() {
  const [activeTab, setActiveTab] = useState('steps')
  const [sessionId, setSessionId] = useState(null)
  const [recipe, setRecipe] = useState(null)
  const [currentStep, setCurrentStep] = useState(0)
  const [strikes, setStrikes] = useState([])
  const [substitutions, setSubstitutions] = useState({})
  const [isListening, setIsListening] = useState(false)

  // Initialize session on mount
  useEffect(() => {
    startSession()
  }, [])

  async function startSession() {
    try {
      const response = await fetch(`${API_BASE}/session/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ recipe_key: 'garlic_pasta' })
      })
      const data = await response.json()
      setSessionId(data.session_id)
      fetchRecipe('garlic_pasta')
    } catch (error) {
      console.error('Failed to start session:', error)
    }
  }

  async function fetchRecipe(recipeKey) {
    try {
      const response = await fetch(`${API_BASE}/recipes/${recipeKey}`)
      const data = await response.json()
      setRecipe(data)
    } catch (error) {
      console.error('Failed to fetch recipe:', error)
    }
  }

  async function sendMessage(message) {
    if (!sessionId) return
    
    try {
      const response = await fetch(`${API_BASE}/session/${sessionId}/message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message })
      })
      const data = await response.json()
      
      // Update state from API response
      setCurrentStep(data.current_step)
      setStrikes(data.strikes)
      setSubstitutions(data.substitutions)
    } catch (error) {
      console.error('Failed to send message:', error)
    }
  }

  function handleDone() {
    sendMessage('k')
  }

  function handleStepToggle(index) {
    sendMessage(`x ${index + 1}`)
  }

  function handleIngredientToggle(ingredient) {
    sendMessage(`x ${ingredient}`)
  }

  function handleVoice() {
    if (!('webkitSpeechRecognition' in window)) {
      alert('Voice recognition not supported in this browser')
      return
    }

    const recognition = new webkitSpeechRecognition()
    recognition.continuous = false
    recognition.interimResults = false

    recognition.onstart = () => setIsListening(true)
    recognition.onend = () => setIsListening(false)

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript
      sendMessage(transcript)
    }

    recognition.start()
  }

  if (!recipe) {
    return <div className={styles.loading}>Loading...</div>
  }

  return (
    <div className={styles.app}>
      <header className={styles.header}>
        <h1 className={styles.title}>🍳 {recipe.name}</h1>
      </header>

      <TabNavigation 
        activeTab={activeTab} 
        onTabChange={setActiveTab} 
      />

      <main className={styles.content}>
        {activeTab === 'steps' && (
          <StepList 
            steps={recipe.steps}
            currentStep={currentStep}
            onStepToggle={handleStepToggle}
          />
        )}
        
        {activeTab === 'ingredients' && (
          <IngredientList 
            ingredients={recipe.ingredients}
            strikes={strikes}
            substitutions={substitutions}
            onIngredientToggle={handleIngredientToggle}
          />
        )}
        
        {activeTab === 'status' && (
          <StatusView 
            currentStep={currentStep}
            steps={recipe.steps}
            ingredients={recipe.ingredients}
            strikes={strikes}
            substitutions={substitutions}
          />
        )}
      </main>

      <footer className={styles.footer}>
        <Button onClick={handleDone}>
          ✓ DONE / NEXT
        </Button>
        
        <Button 
          variant="secondary" 
          onClick={handleVoice}
          disabled={isListening}
        >
          🎤 {isListening ? 'LISTENING...' : 'VOICE'}
        </Button>
      </footer>
    </div>
  )
}

export default App
EOF

# src/App.module.css
echo "🎨 Creating src/App.module.css..."
cat > cooking-ui/src/App.module.css << 'EOF'
.app {
  display: flex;
  flex-direction: column;
  height: 100vh;
  max-width: var(--max-width);
  margin: 0 auto;
  background: var(--color-background);
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md) var(--spacing-lg);
  background: var(--color-background);
  border-bottom: 2px solid var(--color-grey-light);
  min-height: var(--header-height);
}

.title {
  font-size: var(--font-size-header);
  font-weight: var(--font-weight-bold);
  color: var(--color-text);
}

.content {
  flex: 1;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}

.footer {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  background: var(--color-background);
  border-top: 2px solid var(--color-grey-light);
  box-shadow: var(--shadow-medium);
}

.loading {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100vh;
  font-size: var(--font-size-header);
  color: var(--color-text-light);
}
EOF

# Components - Button
echo "🔘 Creating Button component..."
cat > cooking-ui/src/components/Button.jsx << 'EOF'
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
EOF

cat > cooking-ui/src/components/Button.module.css << 'EOF'
.button {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
  width: 100%;
  border: none;
  border-radius: var(--radius-medium);
  font-weight: var(--font-weight-bold);
  transition: all var(--transition-fast);
  touch-action: manipulation;
  user-select: none;
}

.button:active {
  transform: scale(0.98);
}

.button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.primary {
  background: var(--color-primary);
  color: white;
  font-size: var(--font-size-button);
}

.primary:hover:not(:disabled) {
  background: var(--color-primary-hover);
}

.primary:active:not(:disabled) {
  background: var(--color-primary-active);
}

.secondary {
  background: var(--color-background);
  color: var(--color-text);
  border: 2px solid var(--color-grey-light);
  font-size: var(--font-size-button);
}

.secondary:hover:not(:disabled) {
  background: var(--color-grey-light);
}

.large {
  height: var(--button-height-large);
  padding: 0 var(--spacing-lg);
}

.medium {
  height: var(--button-height-medium);
  padding: 0 var(--spacing-md);
}

.small {
  height: var(--button-height-small);
  padding: 0 var(--spacing-md);
  font-size: var(--font-size-step);
}

.icon {
  font-size: 24px;
  display: flex;
  align-items: center;
}
EOF

# Components - TabNavigation
echo "📑 Creating TabNavigation component..."
cat > cooking-ui/src/components/TabNavigation.jsx << 'EOF'
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
EOF

cat > cooking-ui/src/components/TabNavigation.module.css << 'EOF'
.navigation {
  display: flex;
  gap: var(--spacing-sm);
  padding: var(--spacing-md);
  background: var(--color-background);
  border-bottom: 2px solid var(--color-grey-light);
}

.tab {
  flex: 1;
  height: var(--button-height-medium);
  background: var(--color-background);
  border: 2px solid var(--color-grey-light);
  border-radius: var(--radius-medium);
  font-size: var(--font-size-tab);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-light);
  transition: all var(--transition-fast);
  touch-action: manipulation;
}

.tab:hover {
  background: var(--color-grey-light);
}

.tab.active {
  background: var(--color-primary);
  color: white;
  border-color: var(--color-primary);
  font-weight: var(--font-weight-bold);
}

.tab:active {
  transform: scale(0.98);
}
EOF

# Components - StepList
echo "📋 Creating StepList component..."
cat > cooking-ui/src/components/StepList.jsx << 'EOF'
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
EOF

cat > cooking-ui/src/components/StepList.module.css << 'EOF'
.container {
  padding: var(--spacing-md);
}

.list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.item {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-sm);
  padding: var(--spacing-md);
  border-radius: var(--radius-medium);
  font-size: var(--font-size-step);
  line-height: 1.5;
  cursor: pointer;
  transition: background var(--transition-fast);
  min-height: var(--button-height-small);
  touch-action: manipulation;
  user-select: none;
}

.item:hover {
  background: var(--color-grey-light);
}

.item:active {
  transform: scale(0.99);
}

.number {
  font-weight: var(--font-weight-semibold);
  flex-shrink: 0;
}

.arrow {
  flex-shrink: 0;
  color: var(--color-primary);
  font-weight: var(--font-weight-bold);
}

.text {
  flex: 1;
}

.item.completed {
  color: var(--color-grey);
}

.item.completed .text {
  text-decoration: line-through;
}

.item.current {
  background: var(--color-highlight);
  border: 2px solid var(--color-highlight-border);
  font-weight: var(--font-weight-semibold);
}

.item.current:hover {
  background: var(--color-highlight);
}
EOF

# Components - IngredientList
echo "🥘 Creating IngredientList component..."
cat > cooking-ui/src/components/IngredientList.jsx << 'EOF'
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
EOF

cat > cooking-ui/src/components/IngredientList.module.css << 'EOF'
.container {
  padding: var(--spacing-md);
}

.list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.item {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  border-radius: var(--radius-medium);
  font-size: var(--font-size-step);
  cursor: pointer;
  transition: background var(--transition-fast);
  min-height: var(--button-height-small);
  touch-action: manipulation;
  user-select: none;
}

.item:hover {
  background: var(--color-grey-light);
}

.item:active {
  transform: scale(0.99);
}

.checkbox {
  font-size: 24px;
  flex-shrink: 0;
  line-height: 1;
}

.text {
  flex: 1;
  line-height: 1.5;
}

.item.struck {
  color: var(--color-grey);
}

.item.struck .text {
  text-decoration: line-through;
}
EOF

# Components - StatusView
echo "❓ Creating StatusView component..."
cat > cooking-ui/src/components/StatusView.jsx << 'EOF'
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
EOF

cat > cooking-ui/src/components/StatusView.module.css << 'EOF'
.container {
  padding: var(--spacing-md);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xl);
}

.section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.heading {
  font-size: var(--font-size-tab);
  font-weight: var(--font-weight-bold);
  color: var(--color-text);
}

.currentStep {
  font-size: 20px;
  line-height: 1.6;
  font-weight: var(--font-weight-semibold);
  padding: var(--spacing-lg);
  background: var(--color-highlight);
  border: 2px solid var(--color-highlight-border);
  border-radius: var(--radius-medium);
}

.ingredientList {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.ingredient {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-sm);
  font-size: var(--font-size-step);
  line-height: 1.5;
}

.checkbox {
  font-size: 20px;
  flex-shrink: 0;
}

.ingredient.struck {
  color: var(--color-grey);
  text-decoration: line-through;
}
EOF

# Create placeholder icon
echo "🖼️  Creating placeholder icon..."
cat > cooking-ui/public/icon.png.txt << 'EOF'
NOTE: You need a real 512x512 PNG icon here.
Download a chef/cooking icon from:
- https://www.flaticon.com/
- https://icons8.com/
- Or create your own

Name it: icon.png
Delete this .txt file
EOF

echo ""
echo "✅ All files created!"
echo ""
echo "📋 Next steps:"
echo ""
echo "1. cd cooking-ui"
echo "2. Download a 512x512 PNG icon and save as public/icon.png"
echo "3. npm install"
echo "4. npm run dev"
echo ""
echo "🎉 Your React PWA is ready!"
