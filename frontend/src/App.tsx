import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Ecommerce from './pages/Ecommerce'
import Shortage from './pages/Shortage'
import LudaMind from './pages/LudaMind'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Ecommerce />} />
        <Route path="/shortage" element={<Shortage />} />
        <Route path="/luda-mind" element={<LudaMind />} />
      </Routes>
    </Layout>
  )
}

export default App
