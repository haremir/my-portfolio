import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { portfolioData } from '../data/mock';
import { Menu, X } from 'lucide-react';

const Header = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const location = useLocation();

  const isActive = (path) => {
    return location.pathname === path;
  };

  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen);
  };

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-dark-primary border-b border-dark-border">
      <div className="max-w-7xl mx-auto px-6 lg:px-12">
        <div className="flex items-center justify-between h-20">
          {/* Logo */}
          <Link 
            to="/" 
            className="text-2xl font-bold text-brand-primary hover:text-brand-hover transition-colors duration-300"
          >
            {portfolioData.personal.name}
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center space-x-8">
            {portfolioData.navigation.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`text-lg font-medium transition-colors duration-300 ${
                  isActive(item.path)
                    ? 'text-brand-primary'
                    : 'text-text-muted hover:text-text-primary'
                }`}
              >
                {item.name}
              </Link>
            ))}
            
            {/* CTA Button */}
            <Link
              to="/iletisim"
              className="btn-primary"
            >
              İletişim
            </Link>
          </nav>

          {/* Mobile menu button */}
          <button
            onClick={toggleMenu}
            className="md:hidden text-text-primary hover:text-brand-primary transition-colors duration-300"
          >
            {isMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>

        {/* Mobile Navigation */}
        {isMenuOpen && (
          <div className="md:hidden absolute top-20 left-0 right-0 bg-dark-primary border-b border-dark-border">
            <nav className="px-6 py-4 space-y-4">
              {portfolioData.navigation.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setIsMenuOpen(false)}
                  className={`block text-lg font-medium transition-colors duration-300 ${
                    isActive(item.path)
                      ? 'text-brand-primary'
                      : 'text-text-muted hover:text-text-primary'
                  }`}
                >
                  {item.name}
                </Link>
              ))}
              <Link
                to="/iletisim"
                onClick={() => setIsMenuOpen(false)}
                className="btn-primary inline-block mt-4"
              >
                İletişim
              </Link>
            </nav>
          </div>
        )}
      </div>
    </header>
  );
};

export default Header;