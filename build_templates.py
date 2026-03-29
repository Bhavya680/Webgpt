import re
import os

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

hero_html = read_file('stitch_tmp/hero.html')
how_it_works_html = read_file('stitch_tmp/how_it_works.html')
features_html = read_file('stitch_tmp/features.html')
cta_html = read_file('stitch_tmp/cta.html')
footer_html = read_file('stitch_tmp/footer.html')

# Extract head and config from hero.html
head_match = re.search(r'<head>.*?</head>', hero_html, re.DOTALL)
head = head_match.group(0) if head_match else ""

# Extract nav from hero.html
nav_match = re.search(r'<nav.*?</nav>', hero_html, re.DOTALL)
nav = nav_match.group(0) if nav_match else ""
# Replace Login and Get Started buttons with Django URLs in Nav
nav = re.sub(r'<button([^>]*)>Login</button>', r'<a href="{% url \'login\' %}"\1>Login</a>', nav)
nav = re.sub(r'<button([^>]*)>(\s*Get Started\s*<span[^>]*>.*?</span>\s*)</button>', r'<a href="{% url \'signup\' %}"\1>\2</a>', nav, flags=re.DOTALL)


# Extract footer from footer.html
# The main footer is <!-- SiteBot Dark Footer Implementation -->
footer_match = re.search(r'<!-- SiteBot Dark Footer Implementation -->\s*(<footer.*?</footer>)', footer_html, re.DOTALL)
footer = footer_match.group(1) if footer_match else ""

# Build base.html
base_content = f"""{{% load static %}}
<!DOCTYPE html>
<html class="light" lang="en">
{head}
<body class="bg-background text-on-surface antialiased flex flex-col min-h-screen">
    {nav}
    
    <main class="pt-[72px] flex-grow">
        {{% block content %}}{{% endblock %}}
    </main>

    {footer}
</body>
</html>
"""
# clean up the literal markdown code blocks that stitch included in the output occasionally.
base_content = base_content.replace('```html', '').replace('```', '')

write_file('core/templates/base.html', base_content)

# Extract individual sections for landing.html
# 1. Hero Section: "Make Your Website Talk"
hero_section_match = re.search(r'<!-- New Hero Section \(Section 2\) -->\s*(<section.*?</section>)', hero_html, re.DOTALL)
hero_section = hero_section_match.group(1) if hero_section_match else ""

# Wire up the Create My Bot form
# Wrap the input and button in a form
form_html = """
<form method="POST" action="{% url 'landing' %}" class="flex flex-col sm:flex-row items-center justify-center gap-4 mt-10">
    {% csrf_token %}
    <input name="url" required class="w-full sm:w-[400px] h-[56px] px-4 rounded-lg border border-outline-variant bg-surface-container-lowest focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all" placeholder="https://yourwebsite.com" type="url"/>
    <button type="submit" class="w-full sm:w-auto bg-primary-container text-on-primary h-[56px] px-8 rounded-lg text-lg font-bold hover:bg-primary transition-all duration-300 shadow-xl shadow-primary/20 flex items-center justify-center gap-2 whitespace-nowrap">
        Create My Bot →
    </button>
</form>
"""
hero_section = re.sub(r'<div class="flex flex-col sm:flex-row items-center justify-center gap-4 mt-10">.*?</div>', form_html, hero_section, flags=re.DOTALL)


# 2. How it works section
how_it_works_section_match = re.search(r'<!-- How It Works Section -->\s*(<section.*?</section>)', how_it_works_html, re.DOTALL)
hiw_section = how_it_works_section_match.group(1) if how_it_works_section_match else ""

# 3. Features Grid Section
features_section_match = re.search(r'<!-- Feature Grid Section -->\s*(<section.*?</section>)', features_html, re.DOTALL)
feat_section = features_section_match.group(1) if features_section_match else ""

# 4. CTA Banner Section
cta_section_match = re.search(r'<!-- CTA Banner Section -->\s*(<section.*?</section>)', cta_html, re.DOTALL)
cta_section = cta_section_match.group(1) if cta_section_match else ""
# Link CTA buttons
cta_section = re.sub(r'<button([^>]*)>\s*Get Started Free\s*→\s*</button>', r'<a href="{% url \'signup\' %}"\1>Get Started Free →</a>', cta_section)


landing_content = f"""{{% extends 'base.html' %}}

{{% block content %}}
    {hero_section}
    {hiw_section}
    {feat_section}
    {cta_section}
{{% endblock %}}
"""

write_file('core/templates/landing.html', landing_content)
print("Django templates generated successfully.")
