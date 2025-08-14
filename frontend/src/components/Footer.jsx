import React from 'react';
import { portfolioData } from '../data/mock';
import { Github, Linkedin, Twitter, Mail, MapPin, Phone } from 'lucide-react';

const Footer = () => {
  const getIcon = (iconName) => {
    const icons = {
      github: Github,
      linkedin: Linkedin,
      twitter: Twitter,
      behance: Github // Using Github as placeholder for Behance
    };
    return icons[iconName] || Github;
  };

  return (
    <footer className="bg-dark-secondary border-t border-dark-border">
      <div className="max-w-7xl mx-auto px-6 lg:px-12 py-12">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Personal Info */}
          <div className="space-y-4">
            <h3 className="text-2xl font-bold text-brand-primary">
              {portfolioData.personal.name}
            </h3>
            <p className="text-text-secondary text-lg">
              {portfolioData.personal.title}
            </p>
            <p className="text-text-muted">
              {portfolioData.personal.bio}
            </p>
          </div>

          {/* Contact Info */}
          <div className="space-y-4">
            <h4 className="text-xl font-semibold text-text-primary">İletişim</h4>
            <div className="space-y-3">
              <div className="flex items-center space-x-3">
                <Mail size={20} className="text-brand-primary" />
                <a 
                  href={`mailto:${portfolioData.contact.email}`}
                  className="text-text-secondary hover:text-brand-primary transition-colors"
                >
                  {portfolioData.contact.email}
                </a>
              </div>
              <div className="flex items-center space-x-3">
                <Phone size={20} className="text-brand-primary" />
                <a 
                  href={`tel:${portfolioData.contact.phone}`}
                  className="text-text-secondary hover:text-brand-primary transition-colors"
                >
                  {portfolioData.contact.phone}
                </a>
              </div>
              <div className="flex items-center space-x-3">
                <MapPin size={20} className="text-brand-primary" />
                <span className="text-text-secondary">
                  {portfolioData.contact.location}
                </span>
              </div>
            </div>
          </div>

          {/* Social Links */}
          <div className="space-y-4">
            <h4 className="text-xl font-semibold text-text-primary">Sosyal Medya</h4>
            <div className="flex space-x-4">
              {portfolioData.contact.social.map((social, index) => {
                const IconComponent = getIcon(social.icon);
                return (
                  <a
                    key={index}
                    href={social.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-text-muted hover:text-brand-primary transition-colors duration-300"
                    aria-label={social.name}
                  >
                    <IconComponent size={24} />
                  </a>
                );
              })}
            </div>
            <p className="text-text-muted text-sm">
              {portfolioData.contact.availability}
            </p>
          </div>
        </div>

        <div className="border-t border-dark-border mt-12 pt-8 text-center">
          <p className="text-text-muted">
            © 2024 {portfolioData.personal.name}. Tüm hakları saklıdır.
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;