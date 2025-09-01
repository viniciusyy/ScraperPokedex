from itemadapter import ItemAdapter

class DedupPipeline:
    def __init__(self):
        self.seen_keys = set()

    def process_item(self, item, spider):
        ad = ItemAdapter(item)
        # key: (number, form or '')
        key = (ad.get('number'), ad.get('form') or '')
        if key in self.seen_keys:
            raise DropItem(f"Duplicate item: {key}")
        self.seen_keys.add(key)
        return item
