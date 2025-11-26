import os
from bs4 import BeautifulSoup
import re
import shutil

# Configuration
CITIES = {
    "bangalore": {
        "name": "Bangalore",
        "title": "Best Branding & Web Development Agency in Bangalore | ScaleBold",
        "description": "ScaleBold is a leading branding, web development, and digital marketing agency in Bangalore. We help businesses in Bangalore scale with bold strategies.",
        "h1": "Top Branding & Web Development Agency in Bangalore"
    },
    "hyderabad": {
        "name": "Hyderabad",
        "title": "Top Digital Marketing & Web Development Company in Hyderabad | ScaleBold",
        "description": "Looking for a web development agency in Hyderabad? ScaleBold offers premium branding and marketing services to help Hyderabad businesses grow.",
        "h1": "Leading Digital Marketing Agency in Hyderabad"
    },
    "pune": {
        "name": "Pune",
        "title": "Creative Branding & Web Design Agency in Pune | ScaleBold",
        "description": "ScaleBold provides expert web design, branding, and marketing services in Pune. Transform your business with our innovative digital solutions.",
        "h1": "Creative Branding & Web Design Agency in Pune"
    },
    "chennai": {
        "name": "Chennai",
        "title": "Expert Web Development & Marketing Services in Chennai | ScaleBold",
        "description": "ScaleBold is a trusted web development and marketing agency in Chennai, delivering custom solutions for brands looking to dominate the market.",
        "h1": "Expert Web Development Services in Chennai"
    },
    "gurgaon": {
        "name": "Gurgaon",
        "title": "Premium Branding & Digital Agency in Gurgaon | ScaleBold",
        "description": "ScaleBold offers high-end branding and digital marketing services in Gurgaon. We build bold brands for ambitious businesses.",
        "h1": "Premium Branding & Digital Agency in Gurgaon"
    },
    "noida": {
        "name": "Noida",
        "title": "Best Web Development & SEO Agency in Noida | ScaleBold",
        "description": "ScaleBold is a top-rated web development and SEO agency in Noida, helping startups and enterprises achieve digital excellence.",
        "h1": "Best Web Development & SEO Agency in Noida"
    },
    "mumbai": {
        "name": "Mumbai",
        "title": "Leading Creative & Digital Marketing Agency in Mumbai | ScaleBold",
        "description": "ScaleBold is a premier creative and digital marketing agency in Mumbai. We craft unique brand experiences for Mumbai's competitive market.",
        "h1": "Leading Creative & Digital Marketing Agency in Mumbai"
    },
    "delhi": {
        "name": "Delhi",
        "title": "Top Branding & Web Design Company in Delhi | ScaleBold",
        "description": "ScaleBold delivers exceptional branding and web design services in Delhi. Elevate your brand with our strategic digital solutions.",
        "h1": "Top Branding & Web Design Company in Delhi"
    }
}

SOURCE_FILE = "index.html"
OUTPUT_DIR = "locations"

def fix_links(soup, depth=2):
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
    # This is harder with BS4, we might need regex on the string representation or iterate all tags with style attr
    # For now, let's handle style tags and style attributes
    
    url_pattern = re.compile(r'url\([\'"]?((?!http|//|data:)[^\'"\)]+)[\'"]?\)')
    
    def replace_url(match):
        return f'url({prefix}{match.group(1)})'

    for tag in soup.find_all(style=True):
        if tag['style']:
            tag['style'] = url_pattern.sub(replace_url, tag['style'])
            
    for tag in soup.find_all('style'):
        if tag.string:
            tag.string = url_pattern.sub(replace_url, tag.string)

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
        
    soup = BeautifulSoup(content, 'html.parser')
    
    # Find H1 - if not found, we might need to be creative
    h1_tag = soup.find('h1')
    if not h1_tag:
        print("Warning: No H1 tag found in index.html")
        # Try to find a prominent title class
        h1_tag = soup.find(class_=re.compile(r'title|heading', re.I))
        
    base_soup = soup # Keep a copy? No, BS4 modifies in place. 
    # We should parse fresh for each city or deep copy
    
    for slug, data in CITIES.items():
        print(f"Generating page for {data['name']}...")
        
        # Fresh parse to avoid accumulating changes
        city_soup = BeautifulSoup(content, 'html.parser')
        
        # Update Title
        if city_soup.title:
            city_soup.title.string = data['title']
            
        # Update Meta Description
        meta_desc = city_soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            meta_desc['content'] = data['description']
        else:
            city_soup.head.append(city_soup.new_tag('meta', attrs={'name': 'description', 'content': data['description']}))
            
        # Update Meta Keywords
        meta_kw = city_soup.find('meta', attrs={'name': 'keywords'})
        if meta_kw:
            meta_kw['content'] += f", {data['name']}, {data['name']} agency"
            
        # Update H1
        h1 = city_soup.find('h1')
        if h1:
            h1.string = data['h1']
        else:
            # If no H1, try to find the big text we saw in index.html
            # "Scale. Dominate. Boldly."
            # It was in a title class?
            # Let's look for text content
            target_text = city_soup.find(string=re.compile("Scale. Dominate. Boldly."))
            if target_text:
                target_text.replace_with(data['h1'])
        
        # Fix Links
        fix_links(city_soup, depth=2)
        
        # Create Directory
        city_dir = os.path.join(OUTPUT_DIR, slug)
        if not os.path.exists(city_dir):
            os.makedirs(city_dir)
            
        # Write File
        output_path = os.path.join(city_dir, 'index.html')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(str(city_soup))
            
    print("All pages generated successfully.")

if __name__ == "__main__":
    main()
