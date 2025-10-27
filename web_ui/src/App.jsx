import { useState } from 'react'
import NodeList from './components/NodeList'
import './App.css'

function App() {
  const [count, setCount] = useState(0)
  return (
    <main className="p-6 max-w-5xl mx-auto">
      <h1 className="text-2xl font-semibold mb-4">Smart Irrigation Dashboard</h1>
      <NodeList />
    </main>
  )
}

export default App
