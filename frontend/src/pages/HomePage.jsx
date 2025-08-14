import React from 'react';
import { Link } from 'react-router-dom';
import { portfolioData } from '../data/mock';
import { ArrowRight, ExternalLink, Github, Code, Zap, Users } from 'lucide-react';

const HomePage = () => {
  const { personal, featuredProjects } = portfolioData;

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="min-h-screen flex items-center justify-center px-6 lg:px-12">
        <div className="max-w-7xl mx-auto">
          <div className="text-center space-y-8">
            <div className="space-y-6">
              <h1 className="display-huge text-text-primary">
                {personal.name}
              </h1>
              <h2 className="display-medium text-brand-primary">
                {personal.title}
              </h2>
              <p className="body-large text-text-secondary max-w-3xl mx-auto">
                {personal.subtitle}
              </p>
            </div>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-6">
              <Link to="/projeler" className="btn-primary">
                Projelerimi İncele
                <ArrowRight size={20} />
              </Link>
              <Link to="/iletisim" className="btn-secondary">
                İletişime Geç
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-20 px-6 lg:px-12 bg-dark-secondary">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center space-y-4">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-brand-primary/20 rounded-lg">
                <Code className="text-brand-primary" size={32} />
              </div>
              <h3 className="heading-1 text-text-primary">50+</h3>
              <p className="body-medium text-text-secondary">Tamamlanan Proje</p>
            </div>
            <div className="text-center space-y-4">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-brand-primary/20 rounded-lg">
                <Users className="text-brand-primary" size={32} />
              </div>
              <h3 className="heading-1 text-text-primary">25+</h3>
              <p className="body-medium text-text-secondary">Mutlu Müşteri</p>
            </div>
            <div className="text-center space-y-4">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-brand-primary/20 rounded-lg">
                <Zap className="text-brand-primary" size={32} />
              </div>
              <h3 className="heading-1 text-text-primary">5+</h3>
              <p className="body-medium text-text-secondary">Yıl Deneyim</p>
            </div>
          </div>
        </div>
      </section>

      {/* Featured Projects */}
      <section className="py-20 px-6 lg:px-12">
        <div className="max-w-7xl mx-auto">
          <div className="text-center space-y-4 mb-16">
            <h2 className="display-large text-text-primary">Öne Çıkan Projeler</h2>
            <p className="body-large text-text-secondary max-w-2xl mx-auto">
              Son dönemde üzerinde çalıştığım ve gurur duyduğum projelerden bazıları
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {featuredProjects.map((project) => (
              <div 
                key={project.id} 
                className="group bg-dark-secondary border border-dark-border rounded-lg overflow-hidden hover:border-brand-primary/50 transition-all duration-500 hover:transform hover:scale-[1.02]"
              >
                <div className="aspect-video overflow-hidden">
                  <img 
                    src={project.image} 
                    alt={project.title}
                    className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                  />
                </div>
                
                <div className="p-6 space-y-4">
                  <h3 className="heading-3 text-text-primary group-hover:text-brand-primary transition-colors">
                    {project.title}
                  </h3>
                  
                  <p className="body-small text-text-secondary line-clamp-3">
                    {project.description}
                  </p>
                  
                  <div className="flex flex-wrap gap-2">
                    {project.technologies.slice(0, 3).map((tech, index) => (
                      <span 
                        key={index}
                        className="px-3 py-1 text-sm bg-brand-primary/20 text-brand-primary rounded-full"
                      >
                        {tech}
                      </span>
                    ))}
                    {project.technologies.length > 3 && (
                      <span className="px-3 py-1 text-sm bg-dark-border text-text-muted rounded-full">
                        +{project.technologies.length - 3}
                      </span>
                    )}
                  </div>
                  
                  <div className="flex items-center justify-between pt-4 border-t border-dark-border">
                    <a 
                      href={project.demoUrl} 
                      className="inline-flex items-center space-x-2 text-brand-primary hover:text-brand-hover transition-colors"
                    >
                      <ExternalLink size={16} />
                      <span>Demo</span>
                    </a>
                    <a 
                      href={project.codeUrl} 
                      className="inline-flex items-center space-x-2 text-text-muted hover:text-text-primary transition-colors"
                    >
                      <Github size={16} />
                      <span>Kod</span>
                    </a>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="text-center mt-12">
            <Link to="/projeler" className="btn-secondary">
              Tüm Projeleri Görüntüle
              <ArrowRight size={20} />
            </Link>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-6 lg:px-12 bg-dark-secondary">
        <div className="max-w-4xl mx-auto text-center space-y-8">
          <h2 className="display-medium text-text-primary">
            Bir Proje Üzerinde Birlikte Çalışalım
          </h2>
          <p className="body-large text-text-secondary">
            Modern teknolojilerle hayalinizdeki projeyi gerçeğe dönüştürmek için buradayım. 
            Hemen iletişime geçin ve fikirlerinizi konuşalım.
          </p>
          <Link to="/iletisim" className="btn-primary">
            Hemen Başlayalım
            <ArrowRight size={20} />
          </Link>
        </div>
      </section>
    </div>
  );
};

export default HomePage;