import { useState } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import About from './about/about'
import Home from './home/home'
import Dashboard from './dashboard/dashboard'
import './assets/styles.css'
import Signup from './signup/signup';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/about" element={<About />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/signup" element={<Signup />} />
        {/* Add more routes as needed */}
      </Routes>
    </BrowserRouter> 
  );
}
export default App
