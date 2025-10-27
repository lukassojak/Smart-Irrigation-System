import { useState } from 'react'
import IrrigationControl from "./components/IrrigationControl"
import NodeList from './components/NodeList'
import './App.css'

function App() {
  const [count, setCount] = useState(0)
  return (
    <main className="p-6 w-full max-w-6xl mx-auto overflow-x-hidden">
      <h1 className="text-2xl font-semibold mb-4">Smart Irrigation Dashboard</h1>
      <IrrigationControl />
      <NodeList />
    </main>
  )
}

export default App
