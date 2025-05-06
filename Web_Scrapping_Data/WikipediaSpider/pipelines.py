from itemadapter import ItemAdapter

class DiseaseScraperPipeline:
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        # Clean the description text
        if adapter.get('description'):
            adapter['description'] = adapter['description'].strip()
        
        # Clean symptoms and diagnosis lists
        for field in ['symptoms', 'diagnosis']:
            if adapter.get(field):
                # Remove empty entries and strip whitespace
                adapter[field] = [symptom.strip() for symptom in adapter[field] if symptom.strip()]
        
        return item