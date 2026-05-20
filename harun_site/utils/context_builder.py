from harun_site.utils.data_manager import load_projects, load_experience, load_education
from harun_site.utils.markdown_parser import get_all_posts


def build_context() -> str:
    sections = []

    # KİŞİSEL
    sections.append(
        """## Kişisel Bilgiler
- Ad Soyad: Harun Emirhan Bostancı
- Konum: Erzurum, Türkiye
- Durum: Bilgisayar Mühendisliği mezunu, ProudSec'te AI Engineer
- Unvan: AI & Backend Engineer"""
    )

    # DENEYİM
    experiences = load_experience()
    if experiences:
        exp_text = "## İş Deneyimi\n"
        for exp in experiences:
            exp_text += f"""
### {exp.get('company', '')} — {exp.get('role', '')}
- Dönem: {exp.get('start_date', '')} – {exp.get('end_date', '')}
- Açıklama: {exp.get('description', '')}
- Teknolojiler: {', '.join(exp.get('tags', []))}
"""
        sections.append(exp_text)

    # EĞİTİM
    education = load_education()
    if education:
        edu_text = "## Eğitim\n"
        for edu in education:
            edu_text += f"""
### {edu.get('school', '')} — {edu.get('department', '')}
- Derece: {edu.get('degree', '')}
- Dönem: {edu.get('start_year', '')} – {edu.get('end_year', '')}
- Açıklama: {edu.get('description', '')}
"""
        sections.append(edu_text)

    # PROJELER
    projects = load_projects()
    if projects:
        proj_text = "## Projeler\n"
        for proj in projects:
            slug = proj.get('slug', '')
            has_case_study = bool(proj.get("case_study"))
            # Canonical case study URL — always /projects/<slug>
            cs_url = f"/projects/{slug}" if slug and has_case_study else ""
            proj_text += f"""
### {proj.get('name', '')}
- Açıklama: {proj.get('desc', '')}
- Teknolojiler: {', '.join(proj.get('tags', []))}
- Slug: {slug}
- Case Study: {'var' if has_case_study else 'yok'}
"""
            if cs_url:
                proj_text += f"- Case Study URL: {cs_url}\n"
        sections.append(proj_text)

    # BLOG YAZILARI
    try:
        posts = get_all_posts()
        if posts:
            blog_text = "## Blog Yazıları\n"
            for post in posts:
                blog_text += f"""
### {post.title} ({post.date})
- Açıklama: {post.description}
- Etiketler: {', '.join(post.tags)}
- İçerik özeti: {post.content[:300]}...
"""
            sections.append(blog_text)
    except Exception:
        pass

    return "\n\n".join(sections)
