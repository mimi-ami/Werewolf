import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'

function App() {
  const [count, setCount] = useState(0)

  return (
    <>
      <div>
        <a href="https://vite.dev" target="_blank">
          <img src={viteLogo} className="logo" alt="Vite 标志" />
        </a>
        <a href="https://react.dev" target="_blank">
          <img src={reactLogo} className="logo react" alt="React 标志" />
        </a>
      </div>
      <h1>Vite + React 示例</h1>
      <div className="card">
        <button onClick={() => setCount((count) => count + 1)}>
          计数：{count}
        </button>
        <p>
          编辑 <code>src/App.jsx</code> 并保存以测试 HMR
        </p>
      </div>
      <p className="read-the-docs">
        点击 Vite 与 React 标志了解更多
      </p>
    </>
  )
}

export default App
