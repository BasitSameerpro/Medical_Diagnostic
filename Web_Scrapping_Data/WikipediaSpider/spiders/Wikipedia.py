import scrapy
import re
from ..items import Disease

class DiseasesSpider(scrapy.Spider):
    name = "WikipediaSpider"
    allowed_domains = ["en.wikipedia.org"]
    
    def start_requests(self):
        # Start from the lists of diseases main page
        yield scrapy.Request(
            url="https://en.wikipedia.org/wiki/Lists_of_diseases",
            callback=self.parse_main_list
        )
    
    def parse_main_list(self, response):
        # Extract links to disease category pages
        disease_category_links = response.css('div.mw-parser-output ul li a')
        
        # Filter out non-disease category links
        for link in disease_category_links:
            href = link.attrib.get('href', '')
            text = link.css('::text').get()
            
            # Check if the link is likely a disease category
            if (href.startswith('/wiki/List_of') and 
                'disease' in href.lower() or 
                'disorder' in href.lower() or
                'syndrome' in href.lower()):
                
                category_url = response.urljoin(href)
                yield scrapy.Request(
                    url=category_url,
                    callback=self.parse_disease_category,
                    meta={'category': text}
                )
    
    def parse_disease_category(self, response):
        category = response.meta.get('category', '')
        
        # Extract disease links from the category page
        disease_links = response.css('div.mw-parser-output ul li a')
        
        for link in disease_links:
            href = link.attrib.get('href', '')
            disease_name = link.css('::text').get()
            
            # Skip non-disease links or special pages
            if (not href.startswith('/wiki/') or 
                href.startswith('/wiki/File:') or
                href.startswith('/wiki/Template:') or
                href.startswith('/wiki/Category:') or
                href.startswith('/wiki/Help:') or
                href.startswith('/wiki/Wikipedia:')):
                continue
                
            # Follow the link to the disease page
            disease_url = response.urljoin(href)
            yield scrapy.Request(
                url=disease_url,
                callback=self.parse_disease_page,
                meta={'disease_name': disease_name, 'category': category}
            )
    
    def parse_disease_page(self, response):
        disease_name = response.meta.get('disease_name', '')
        category = response.meta.get('category', '')
        
        # Initialize disease item
        disease = Disease()
        disease['name'] = disease_name
        disease['url'] = response.url
        disease['category'] = category
        
                    # Extract description (often in the first paragraph)
        # Use a more comprehensive selector that captures all text nodes including links
        first_paragraph = response.css('div.mw-parser-output > p:first-of-type ::text').getall()
        if first_paragraph:
            disease['description'] = ''.join(first_paragraph)
        
        # Look for symptoms in various ways
        symptoms = []
        
        # Method 1: Look for a "Symptoms" or "Signs and symptoms" section
        symptom_section = self.get_section_content(response, ['Symptoms', 'Signs and symptoms'])
        if symptom_section:
            # Extract symptoms from lists in the section - get all text including links
            symptoms_list = symptom_section.css('ul li ::text').getall()
            symptoms.extend(symptoms_list)
        
        # Method 2: Look for symptoms mentioned in paragraphs
        symptom_paragraphs = self.get_section_paragraphs(response, ['Symptoms', 'Signs and symptoms'])
        if symptom_paragraphs:
            # Basic extraction - we'd want more sophisticated NLP in a real application
            symptoms.extend(symptom_paragraphs)
        
        # Store symptoms
        if symptoms:
            disease['symptoms'] = symptoms
        
        # Extract diagnosis information
        diagnosis = []
        
        # Look for "Diagnosis" section
        diagnosis_section = self.get_section_content(response, ['Diagnosis', 'Diagnostic approach'])
        if diagnosis_section:
            # Extract diagnosis methods from lists and paragraphs
            diagnosis_list = diagnosis_section.css('ul li ::text').getall()
            diagnosis.extend(diagnosis_list)
            
            diagnosis_paras = diagnosis_section.css('p ::text').getall()
            if diagnosis_paras:
                diagnosis.extend(diagnosis_paras)
        
        # Store diagnosis information
        if diagnosis:
            disease['diagnosis'] = diagnosis
        
        yield disease
    
    def get_section_content(self, response, section_names):
        """Find a section by possible names and return its content"""
        for section_name in section_names:
            # Try to find the section heading
            section_heading = response.xpath(f'//span[@id="{section_name}"]/../..')
            if section_heading:
                # Get the section content - all elements until the next heading
                section_content = section_heading.xpath('./following-sibling::*[position()<10 and not(self::h2 or self::h3)]')
                if section_content:
                    return section_content
                    
            # Alternative method - look for a span with the section name
            alt_heading = response.xpath(f'//span[@class="mw-headline" and contains(text(), "{section_name}")]/../..')
            if alt_heading:
                section_content = alt_heading.xpath('./following-sibling::*[position()<10 and not(self::h2 or self::h3)]')
                if section_content:
                    return section_content
        
        return None
    
    def get_section_paragraphs(self, response, section_names):
        """Extract text from paragraphs in a section"""
        section = self.get_section_content(response, section_names)
        if section:
            return section.css('p::text').getall()
        return []