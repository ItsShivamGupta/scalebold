import os
from bs4 import BeautifulSoup
import re

# Configuration
SERVICES = {
    "branding-agency": {
        "name": "Branding Agency",
        "keywords": "branding, brand identity, logo design, brand strategy"
    },
    "web-development-agency": {
        "name": "Web Development Agency",
        "keywords": "web development, website design, custom web apps, responsive design"
    },
    "marketing-agency": {
        "name": "Marketing Agency",
        "keywords": "digital marketing, seo, social media marketing, content marketing"
    }
}

CITIES = {
    "bangalore": "Bangalore",
    "hyderabad": "Hyderabad",
    "pune": "Pune",
    "chennai": "Chennai",
    "gurgaon": "Gurgaon",
    "noida": "Noida",
    "mumbai": "Mumbai",
    "delhi": "Delhi"
}

SOURCE_FILE = "index.html"
OUTPUT_DIR = "locations"

def fix_links(soup, depth=3):
    """Fix all relative links to work from subdirectories"""
    prefix = "../" * depth
    
    # Fix href
    for tag in soup.find_all(href=True):
        href = tag['href']
        if not href.startswith(('http', '//', '#', 'mailto:', 'tel:', 'javascript:')):
            tag['href'] = prefix + href
            
    # Fix src
    for tag in soup.find_all(src=True):
        src = tag['src']
        if not src.startswith(('http', '//', 'data:')):
            tag['src'] = prefix + src
            
    # Fix srcset
    for tag in soup.find_all(srcset=True):
        srcset = tag['srcset']
        new_srcset = []
        for src_def in srcset.split(','):
            parts = src_def.strip().split(' ')
            url = parts[0]
            if not url.startswith(('http', '//', 'data:')):
                parts[0] = prefix + url
            new_srcset.append(' '.join(parts))
        tag['srcset'] = ', '.join(new_srcset)
        
    # Fix inline styles with url()
    url_pattern = re.compile(r'url\([\'"]?((?!http|//|data:)[^\'"\)]+)[\'"]?\)')
    
    def replace_url(match):
        return f'url({prefix}{match.group(1)})'

    for tag in soup.find_all(style=True):
        if tag['style']:
            tag['style'] = url_pattern.sub(replace_url, tag['style'])
            
    for tag in soup.find_all('style'):
        if tag.string:
            tag.string = url_pattern.sub(replace_url, tag.string)

def generate_meta_data(city_name, service_name, service_slug, service_keywords):
    """Generate SEO metadata for service + location combinations"""
    titles = {
        "branding-agency": f"Best {service_name} in {city_name} | ScaleBold",
        "web-development-agency": f"Top {service_name} in {city_name} | ScaleBold",
        "marketing-agency": f"Leading {service_name} in {city_name} | ScaleBold"
    }
    
    descriptions = {
        "branding-agency": f"ScaleBold is the best branding agency in {city_name}. We create bold brand identities that help businesses in {city_name} stand out and dominate their market.",
        "web-development-agency": f"Looking for expert web development in {city_name}? ScaleBold builds custom, scalable websites and web applications for {city_name} businesses.",
        "marketing-agency": f"ScaleBold is a leading digital marketing agency in {city_name}. We deliver data-driven marketing strategies to help {city_name} businesses grow online."
    }
    
    h1s = {
        "branding-agency": f"Best Branding Agency in {city_name}",
        "web-development-agency": f"Expert Web Development Services in {city_name}",
        "marketing-agency": f"Top Digital Marketing Agency in {city_name}"
    }
    
    return {
        "title": titles.get(service_slug, f"{service_name} in {city_name} | ScaleBold"),
        "description": descriptions.get(service_slug, f"Professional {service_name.lower()} services in {city_name}."),
        "h1": h1s.get(service_slug, f"{service_name} in {city_name}"),
        "keywords": f"{service_keywords}, {city_name}, {city_name} {service_name.lower()}"
    }

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
        
    total_pages = 0
    
    for city_slug, city_name in CITIES.items():
        for service_slug, service_data in SERVICES.items():
            service_name = service_data['name']
            service_keywords = service_data['keywords']
            
            print(f"Generating page for {service_name} in {city_name}...")
            
            # Fresh parse
            page_soup = BeautifulSoup(content, 'html.parser')
            
            # Get metadata
            meta_data = generate_meta_data(city_name, service_name, service_slug, service_keywords)
            
            # Update Title
            if page_soup.title:
                page_soup.title.string = meta_data['title']
                
            # Update Meta Description
            meta_desc = page_soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                meta_desc['content'] = meta_data['description']
            else:
                new_meta = page_soup.new_tag('meta', attrs={'name': 'description', 'content': meta_data['description']})
                page_soup.head.append(new_meta)
                
            # Update Meta Keywords
            meta_kw = page_soup.find('meta', attrs={'name': 'keywords'})
            if meta_kw:
                meta_kw['content'] = meta_data['keywords']
            else:
                new_kw = page_soup.new_tag('meta', attrs={'name': 'keywords', 'content': meta_data['keywords']})
                page_soup.head.append(new_kw)
            
            # Update canonical
            canonical = page_soup.find('link', attrs={'rel': 'canonical'})
            if canonical:
                canonical['href'] = f"https://scalebold.com/locations/{city_slug}/{service_slug}/"
                
            # Try to update H1 or prominent text
            h1 = page_soup.find('h1')
            if h1:
                h1.string = meta_data['h1']
            else:
                # Fallback: replace "Scale. Dominate. Boldly." text
                target_text = page_soup.find(string=re.compile("Scale. Dominate. Boldly."))
                if target_text:
                    target_text.replace_with(meta_data['h1'])
            
            # Fix Links - depth=3 because we're in locations/{city}/{service}/
            fix_links(page_soup, depth=3)
            
            # Create Directory
            page_dir = os.path.join(OUTPUT_DIR, city_slug, service_slug)
            if not os.path.exists(page_dir):
                os.makedirs(page_dir)
                
            # Write File
            output_path = os.path.join(page_dir, 'index.html')
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(str(page_soup))
                
            total_pages += 1
            
    print(f"\n✅ Successfully generated {total_pages} service-specific location pages!")

if __name__ == "__main__":
    main()
