import React, { useState } from 'react';
import { portfolioData } from '../data/mock';
import { ExternalLink, Github, Filter } from 'lucide-react';

const ProjectsPage = () => {
  const [selectedCategory, setSelectedCategory] = useState('Tümü');
  
  // Get unique categories
  const categories = ['Tümü', ...new Set(portfolioData.projects.map(project => project.category))];
  
  // Filter projects based on selected category
  const filteredProjects = selectedCategory === 'Tümü' 
    ? portfolioData.projects 
    : portfolioData.projects.filter(project => project.category === selectedCategory);

  const getStatusColor = (status) => {
    switch (status) {
      case 'Tamamlandı':
        return 'bg-green-500/20 text-green-400';
      case 'Geliştirme aşamasında':
        return 'bg-yellow-500/20 text-yellow-400';
      default:
        return 'bg-brand-primary/20 text-brand-primary';
    }
  };

  return (
    <div className="min-h-screen py-20 px-6 lg:px-12">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center space-y-6 mb-16">
          <h1 className="display-large text-text-primary">Projelerim</h1>
          <p className="body-large text-text-secondary max-w-3xl mx-auto">
            Modern teknolojiler kullanarak geliştirdiğim web uygulamaları, mobil projeler ve açık kaynak çalışmalarım
          </p>
        </div>

        {/* Filter Tabs */}
        <div className="flex flex-wrap items-center justify-center gap-4 mb-12">
          <div className="flex items-center gap-2 text-text-muted">
            <Filter size={20} />
            <span>Filtrele:</span>
          </div>
          {categories.map((category) => (
            <button
              key={category}
              onClick={() => setSelectedCategory(category)}
              className={`px-4 py-2 rounded-full text-sm font-medium transition-all duration-300 ${
                selectedCategory === category
                  ? 'bg-brand-primary text-dark-primary'
                  : 'bg-dark-secondary text-text-muted hover:text-text-primary hover:bg-dark-border'
              }`}
            >
              {category}
            </button>
          ))}
        </div>

        {/* Projects Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {filteredProjects.map((project) => (
            <div 
              key={project.id} 
              className="group bg-dark-secondary border border-dark-border rounded-lg overflow-hidden hover:border-brand-primary/50 transition-all duration-500 hover:transform hover:scale-[1.02]"
            >
              {/* Project Image */}
              <div className="aspect-video overflow-hidden relative">
                <img 
                  src={project.image} 
                  alt={project.title}
                  className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                />
                <div className="absolute top-4 right-4">
                  <span className={`px-3 py-1 text-xs rounded-full ${getStatusColor(project.status)}`}>
                    {project.status}
                  </span>
                </div>
                {project.featured && (
                  <div className="absolute top-4 left-4">
                    <span className="px-3 py-1 text-xs bg-brand-primary/20 text-brand-primary rounded-full">
                      Öne Çıkan
                    </span>
                  </div>
                )}
              </div>
              
              {/* Project Details */}
              <div className="p-6 space-y-4">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <h3 className="heading-3 text-text-primary group-hover:text-brand-primary transition-colors">
                      {project.title}
                    </h3>
                    <span className="text-xs text-text-muted bg-dark-border px-2 py-1 rounded">
                      {project.category}
                    </span>
                  </div>
                  
                  <p className="body-small text-text-secondary line-clamp-3">
                    {project.description}
                  </p>
                </div>
                
                {/* Technologies */}
                <div className="flex flex-wrap gap-2">
                  {project.technologies.map((tech, index) => (
                    <span 
                      key={index}
                      className="px-3 py-1 text-xs bg-brand-primary/20 text-brand-primary rounded-full"
                    >
                      {tech}
                    </span>
                  ))}
                </div>
                
                {/* Action Buttons */}
                <div className="flex items-center justify-between pt-4 border-t border-dark-border">
                  <a 
                    href={project.demoUrl} 
                    className="inline-flex items-center space-x-2 text-brand-primary hover:text-brand-hover transition-colors"
                  >
                    <ExternalLink size={16} />
                    <span>Canlı Demo</span>
                  </a>
                  <a 
                    href={project.codeUrl} 
                    className="inline-flex items-center space-x-2 text-text-muted hover:text-text-primary transition-colors"
                  >
                    <Github size={16} />
                    <span>Kaynak Kod</span>
                  </a>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Empty State */}
        {filteredProjects.length === 0 && (
          <div className="text-center py-16">
            <div className="w-24 h-24 mx-auto mb-6 bg-dark-secondary rounded-full flex items-center justify-center">
              <Filter className="text-text-muted" size={32} />
            </div>
            <h3 className="heading-2 text-text-primary mb-2">Bu kategoride proje bulunamadı</h3>
            <p className="text-text-muted">Başka bir kategori seçmeyi deneyin</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProjectsPage;