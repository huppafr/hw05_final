from django.test import TestCase
from django.urls import reverse
from django.conf import settings
from django.core.cache import cache

from posts.models import Post, Group, User

USERNAME = 'test_user'
SLUG = 'test_slug'
INDEX_URL = reverse('posts:index')


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username=USERNAME)
        cls.group = Group.objects.create(
            title="Тестовая группа",
            description="Группа для тестирования",
            slug=SLUG
        )
        # Здесь создаются фикстуры: клиент и 24 тестовых записей.
        for num in range(24):
            Post.objects.create(
                author=cls.user,
                text=num,
            )

    def test_first_page_contains_number_of_posts_specified_in_settings(self):
        '''Проверка Paginator: количество постов на странице
        не превышает количество постов, указанных в
        settings.POSTS_PER_PAGE'''
        cache.clear()
        response = self.client.get(INDEX_URL)
        posts_on_page = len(response.context['page'])

        self.assertTrue(
            posts_on_page <= settings.POSTS_PER_PAGE
        )
