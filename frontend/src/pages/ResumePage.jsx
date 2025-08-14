import React from 'react';
import { portfolioData } from '../data/mock';
import { Download, MapPin, Mail, Phone, Calendar, Award } from 'lucide-react';

const ResumePage = () => {
  const { resume, personal, contact } = portfolioData;

  return (
    <div className="min-h-screen py-20 px-6 lg:px-12">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center space-y-6 mb-16">
          <h1 className="display-large text-text-primary">Özgeçmişim</h1>
          <p className="body-large text-text-secondary max-w-3xl mx-auto">
            Profesyonel deneyimim, eğitim geçmişim ve teknik becerilerim hakkında detaylı bilgiler
          </p>
          <button className="btn-primary">
            <Download size={20} />
            CV İndir (PDF)
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
          {/* Left Column - Personal Info & Contact */}
          <div className="lg:col-span-1 space-y-8">
            {/* Personal Info */}
            <div className="bg-dark-secondary border border-dark-border rounded-lg p-6">
              <h2 className="heading-2 text-text-primary mb-6">Kişisel Bilgiler</h2>
              <div className="space-y-4">
                <div className="flex items-center space-x-3">
                  <Mail className="text-brand-primary" size={20} />
                  <div>
                    <p className="text-sm text-text-muted">E-posta</p>
                    <p className="text-text-secondary">{contact.email}</p>
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  <Phone className="text-brand-primary" size={20} />
                  <div>
                    <p className="text-sm text-text-muted">Telefon</p>
                    <p className="text-text-secondary">{contact.phone}</p>
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  <MapPin className="text-brand-primary" size={20} />
                  <div>
                    <p className="text-sm text-text-muted">Konum</p>
                    <p className="text-text-secondary">{contact.location}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Skills */}
            <div className="bg-dark-secondary border border-dark-border rounded-lg p-6">
              <h2 className="heading-2 text-text-primary mb-6">Teknik Beceriler</h2>
              <div className="space-y-4">
                {resume.skills.technical.map((skill, index) => (
                  <div key={index} className="space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-text-secondary">{skill.name}</span>
                      <span className="text-brand-primary text-sm">{skill.level}%</span>
                    </div>
                    <div className="w-full bg-dark-primary rounded-full h-2">
                      <div 
                        className="bg-brand-primary rounded-full h-2 transition-all duration-1000"
                        style={{ width: `${skill.level}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Languages */}
            <div className="bg-dark-secondary border border-dark-border rounded-lg p-6">
              <h2 className="heading-2 text-text-primary mb-6">Diller</h2>
              <div className="space-y-3">
                {resume.languages.map((language, index) => (
                  <div key={index} className="flex justify-between items-center">
                    <span className="text-text-secondary">{language.name}</span>
                    <span className="text-brand-primary text-sm">{language.level}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Soft Skills */}
            <div className="bg-dark-secondary border border-dark-border rounded-lg p-6">
              <h2 className="heading-2 text-text-primary mb-6">Kişisel Beceriler</h2>
              <div className="flex flex-wrap gap-2">
                {resume.skills.soft.map((skill, index) => (
                  <span 
                    key={index}
                    className="px-3 py-1 text-sm bg-brand-primary/20 text-brand-primary rounded-full"
                  >
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* Right Column - Experience & Education */}
          <div className="lg:col-span-2 space-y-8">
            {/* About */}
            <div className="bg-dark-secondary border border-dark-border rounded-lg p-6">
              <h2 className="heading-2 text-text-primary mb-4">Hakkımda</h2>
              <p className="text-text-secondary leading-relaxed">{personal.bio}</p>
            </div>

            {/* Experience */}
            <div className="bg-dark-secondary border border-dark-border rounded-lg p-6">
              <h2 className="heading-2 text-text-primary mb-6 flex items-center gap-3">
                <Award className="text-brand-primary" size={24} />
                İş Deneyimi
              </h2>
              <div className="space-y-8">
                {resume.experience.map((job, index) => (
                  <div key={job.id} className="relative">
                    {index !== resume.experience.length - 1 && (
                      <div className="absolute left-0 top-12 w-px h-full bg-dark-border"></div>
                    )}
                    <div className="flex">
                      <div className="flex-shrink-0 w-3 h-3 bg-brand-primary rounded-full mt-2"></div>
                      <div className="ml-6">
                        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-2">
                          <h3 className="heading-3 text-text-primary">{job.position}</h3>
                          <div className="flex items-center text-brand-primary text-sm">
                            <Calendar size={16} className="mr-1" />
                            {job.duration}
                          </div>
                        </div>
                        <p className="text-text-muted mb-3">{job.company}</p>
                        <p className="text-text-secondary mb-4">{job.description}</p>
                        <div className="space-y-2">
                          <h4 className="text-sm font-medium text-text-primary">Başarılar:</h4>
                          <ul className="space-y-1">
                            {job.achievements.map((achievement, achievementIndex) => (
                              <li 
                                key={achievementIndex}
                                className="text-text-secondary text-sm flex items-start"
                              >
                                <span className="text-brand-primary mr-2">•</span>
                                {achievement}
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Education */}
            <div className="bg-dark-secondary border border-dark-border rounded-lg p-6">
              <h2 className="heading-2 text-text-primary mb-6 flex items-center gap-3">
                <Award className="text-brand-primary" size={24} />
                Eğitim
              </h2>
              <div className="space-y-6">
                {resume.education.map((education, index) => (
                  <div key={education.id} className="relative">
                    {index !== resume.education.length - 1 && (
                      <div className="absolute left-0 top-12 w-px h-full bg-dark-border"></div>
                    )}
                    <div className="flex">
                      <div className="flex-shrink-0 w-3 h-3 bg-brand-primary rounded-full mt-2"></div>
                      <div className="ml-6">
                        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-2">
                          <h3 className="heading-3 text-text-primary">{education.degree}</h3>
                          <div className="flex items-center text-brand-primary text-sm">
                            <Calendar size={16} className="mr-1" />
                            {education.duration}
                          </div>
                        </div>
                        <p className="text-text-muted mb-2">{education.school}</p>
                        {education.gpa && (
                          <p className="text-text-secondary text-sm">GPA: {education.gpa}</p>
                        )}
                      </div>
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

export default ResumePage;