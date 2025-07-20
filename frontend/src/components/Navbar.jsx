import React from 'react';
import { Link } from 'react-router-dom';

export default function Navbar() {
  return (
    <nav>
      <Link to="/">Home</Link>
      <Link to="/compare">Compare</Link>
      <Link to="/news">News</Link>
      <Link to="/about">About</Link>
    </nav>
  );
}