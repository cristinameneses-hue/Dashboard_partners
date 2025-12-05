import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Ecommerce from './pages/Ecommerce'
import Shortage from './pages/Shortage'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Ecommerce />} />
        <Route path="/shortage" element={<Shortage />} />
      </Routes>
    </Layout>
  )
}

export default App
