from django.contrib.syndication.views import Feed
from haystack.query import SearchQuerySet

from models import Staff

class LatestEntriesFeed(Feed):
    title =  'Latest Staff'
    link =  "/quotes/"
    description =  "Latest Staff"

    def items(self):
        sqs = SearchQuerySet().models(Staff).order_by('-start_dt')[:20]
        return [sq.object for sq in sqs]

    def item_title(self, item):
        return item.name

    def item_description(self, item):
        return item.biography