import { Routes, Route } from 'react-router-dom';
import { HomePage } from './pages/HomePage';
import { GraphPage } from './pages/GraphPage';
import { ChatPage } from './pages/ChatPage';

function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/chart/:symbol" element={<GraphPage />} />
      <Route path="/graph/:symbol" element={<GraphPage />} />
      <Route path="/chat" element={<ChatPage />} />
    </Routes>
  );
}

export default App;
