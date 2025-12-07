import { useState, useEffect } from 'react'
import styles from './App.module.css'
import { TabNavigation } from './components/TabNavigation'
import { StepList } from './components/StepList'
import { IngredientList } from './components/IngredientList'
import { StatusView } from './components/StatusView'
import { Button } from './components/Button'
import { RecipePicker } from './components/RecipePicker'

const API_BASE = window.location.hostname === 'localhost'
  ? 'http://localhost:8000'
  : `http://${window.location.hostname}:8000`

function App() {
  const [activeTab, setActiveTab] = useState('steps')
  const [sessionId, setSessionId] = useState(null)
  const [recipe, setRecipe] = useState(null)
  const [currentStep, setCurrentStep] = useState(0)
  const [strikes, setStrikes] = useState([])
  const [substitutions, setSubstitutions] = useState({})
  const [isListening, setIsListening] = useState(false)
  const [recipeKey, setRecipeKey] = useState('crispy_salt_and_pepper_potatoes')

  // Initialize session when recipe changes
  useEffect(() => {
    if (recipeKey) {
      startSession(recipeKey)
    }
  }, [recipeKey])

  async function startSession(key) {  // <- Add 'key' parameter
    try {
      const response = await fetch(`${API_BASE}/session/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ recipe_key: key })  // <- Use 'key' not hardcoded
      })
      const data = await response.json()
      setSessionId(data.session_id)
      fetchRecipe(key)  // <- Use 'key' not hardcoded

      // Reset state for new recipe
      setCurrentStep(0)
      setStrikes([])
      setSubstitutions({})
      setActiveTab('steps')
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

  function handleRecipeSelect(newRecipeKey) {
    setRecipeKey(newRecipeKey)
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
        <RecipePicker
          onRecipeSelect={handleRecipeSelect}
          currentRecipeKey={recipeKey}
        />
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
