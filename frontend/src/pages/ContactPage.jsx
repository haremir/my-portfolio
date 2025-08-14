import React, { useState } from 'react';
import { portfolioData } from '../data/mock';
import { Send, Mail, Phone, MapPin, Clock, CheckCircle, Github, Linkedin, Twitter } from 'lucide-react';
import { useToast } from '../hooks/use-toast';

const ContactPage = () => {
  const { contact, personal } = portfolioData;
  const { toast } = useToast();
  
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    subject: '',
    message: ''
  });

  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);

    // Simulate form submission
    setTimeout(() => {
      setIsSubmitting(false);
      toast({
        title: "Mesaj Gönderildi!",
        description: "En kısa sürede size dönüş yapacağım.",
      });
      
      // Reset form
      setFormData({
        name: '',
        email: '',
        subject: '',
        message: ''
      });
    }, 2000);
  };

  const getSocialIcon = (iconName) => {
    const icons = {
      github: Github,
      linkedin: Linkedin,
      twitter: Twitter,
      behance: Github
    };
    return icons[iconName] || Github;
  };

  return (
    <div className="min-h-screen py-20 px-6 lg:px-12">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center space-y-6 mb-16">
          <h1 className="display-large text-text-primary">İletişim</h1>
          <p className="body-large text-text-secondary max-w-3xl mx-auto">
            Bir projeyi birlikte gerçekleştirmek veya danışmanlık almak istiyorsanız, 
            benimle iletişime geçmekten çekinmeyin. Her mesajı özenle değerlendiriyorum.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
          {/* Contact Form */}
          <div className="bg-dark-secondary border border-dark-border rounded-lg p-8">
            <h2 className="heading-2 text-text-primary mb-6">Mesaj Gönderin</h2>
            
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label htmlFor="name" className="block text-sm font-medium text-text-primary mb-2">
                    İsim *
                  </label>
                  <input
                    type="text"
                    id="name"
                    name="name"
                    value={formData.name}
                    onChange={handleInputChange}
                    required
                    className="w-full px-4 py-3 bg-dark-primary border border-dark-border rounded-none text-text-primary placeholder-text-muted focus:outline-none focus:border-brand-primary transition-colors"
                    placeholder="İsminizi yazın"
                  />
                </div>
                
                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-text-primary mb-2">
                    E-posta *
                  </label>
                  <input
                    type="email"
                    id="email"
                    name="email"
                    value={formData.email}
                    onChange={handleInputChange}
                    required
                    className="w-full px-4 py-3 bg-dark-primary border border-dark-border rounded-none text-text-primary placeholder-text-muted focus:outline-none focus:border-brand-primary transition-colors"
                    placeholder="email@example.com"
                  />
                </div>
              </div>
              
              <div>
                <label htmlFor="subject" className="block text-sm font-medium text-text-primary mb-2">
                  Konu *
                </label>
                <input
                  type="text"
                  id="subject"
                  name="subject"
                  value={formData.subject}
                  onChange={handleInputChange}
                  required
                  className="w-full px-4 py-3 bg-dark-primary border border-dark-border rounded-none text-text-primary placeholder-text-muted focus:outline-none focus:border-brand-primary transition-colors"
                  placeholder="Proje danışmanlığı, web geliştirme..."
                />
              </div>
              
              <div>
                <label htmlFor="message" className="block text-sm font-medium text-text-primary mb-2">
                  Mesaj *
                </label>
                <textarea
                  id="message"
                  name="message"
                  value={formData.message}
                  onChange={handleInputChange}
                  required
                  rows={6}
                  className="w-full px-4 py-3 bg-dark-primary border border-dark-border rounded-none text-text-primary placeholder-text-muted focus:outline-none focus:border-brand-primary transition-colors resize-vertical"
                  placeholder="Projeniz veya ihtiyaçlarınız hakkında detaylı bilgi verebilir misiniz?"
                />
              </div>
              
              <button
                type="submit"
                disabled={isSubmitting}
                className={`btn-primary w-full ${isSubmitting ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                {isSubmitting ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-2 border-dark-primary border-t-transparent"></div>
                    Gönderiliyor...
                  </>
                ) : (
                  <>
                    <Send size={20} />
                    Mesaj Gönder
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Contact Information */}
          <div className="space-y-8">
            {/* Contact Details */}
            <div className="bg-dark-secondary border border-dark-border rounded-lg p-8">
              <h2 className="heading-2 text-text-primary mb-6">İletişim Bilgileri</h2>
              
              <div className="space-y-6">
                <div className="flex items-start space-x-4">
                  <div className="flex-shrink-0 w-12 h-12 bg-brand-primary/20 rounded-lg flex items-center justify-center">
                    <Mail className="text-brand-primary" size={24} />
                  </div>
                  <div>
                    <h3 className="text-text-primary font-medium mb-1">E-posta</h3>
                    <a 
                      href={`mailto:${contact.email}`}
                      className="text-text-secondary hover:text-brand-primary transition-colors"
                    >
                      {contact.email}
                    </a>
                  </div>
                </div>
                
                <div className="flex items-start space-x-4">
                  <div className="flex-shrink-0 w-12 h-12 bg-brand-primary/20 rounded-lg flex items-center justify-center">
                    <Phone className="text-brand-primary" size={24} />
                  </div>
                  <div>
                    <h3 className="text-text-primary font-medium mb-1">Telefon</h3>
                    <a 
                      href={`tel:${contact.phone}`}
                      className="text-text-secondary hover:text-brand-primary transition-colors"
                    >
                      {contact.phone}
                    </a>
                  </div>
                </div>
                
                <div className="flex items-start space-x-4">
                  <div className="flex-shrink-0 w-12 h-12 bg-brand-primary/20 rounded-lg flex items-center justify-center">
                    <MapPin className="text-brand-primary" size={24} />
                  </div>
                  <div>
                    <h3 className="text-text-primary font-medium mb-1">Konum</h3>
                    <p className="text-text-secondary">{contact.location}</p>
                  </div>
                </div>
                
                <div className="flex items-start space-x-4">
                  <div className="flex-shrink-0 w-12 h-12 bg-brand-primary/20 rounded-lg flex items-center justify-center">
                    <Clock className="text-brand-primary" size={24} />
                  </div>
                  <div>
                    <h3 className="text-text-primary font-medium mb-1">Müsaitlik</h3>
                    <p className="text-text-secondary">{contact.availability}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Social Media */}
            <div className="bg-dark-secondary border border-dark-border rounded-lg p-8">
              <h2 className="heading-2 text-text-primary mb-6">Sosyal Medya</h2>
              
              <div className="grid grid-cols-2 gap-4">
                {contact.social.map((social, index) => {
                  const IconComponent = getSocialIcon(social.icon);
                  return (
                    <a
                      key={index}
                      href={social.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center space-x-3 p-4 bg-dark-primary border border-dark-border rounded-lg hover:border-brand-primary/50 hover:bg-brand-primary/5 transition-all duration-300 group"
                    >
                      <IconComponent className="text-brand-primary group-hover:scale-110 transition-transform" size={24} />
                      <span className="text-text-secondary group-hover:text-text-primary transition-colors">
                        {social.name}
                      </span>
                    </a>
                  );
                })}
              </div>
            </div>

            {/* Services */}
            <div className="bg-dark-secondary border border-dark-border rounded-lg p-8">
              <h2 className="heading-2 text-text-primary mb-6">Sunduğum Hizmetler</h2>
              
              <div className="space-y-4">
                {contact.services.map((service, index) => (
                  <div key={index} className="flex items-start space-x-3">
                    <CheckCircle className="flex-shrink-0 text-brand-primary mt-1" size={20} />
                    <div>
                      <h3 className="text-text-primary font-medium mb-1">{service.title}</h3>
                      <p className="text-text-secondary text-sm">{service.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ContactPage;