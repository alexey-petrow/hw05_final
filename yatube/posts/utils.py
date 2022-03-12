from django.core.paginator import Paginator
from django.conf import settings


def add_paginator(post_list, request):
    paginator = Paginator(post_list, settings.POSTS_IN_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
