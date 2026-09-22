"""Shared DRF pagination.

The default ``PageNumberPagination`` ignores ``?page_size=``, which silently
truncates long lists (admin dashboard, sitemap) at ``PAGE_SIZE``. This subclass
lets clients ask for a larger page while capping how large they can go.
"""

from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    page_size_query_param = "page_size"
    max_page_size = 500
