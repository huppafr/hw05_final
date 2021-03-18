from django.conf import settings
from django.test import TestCase, Client
from django.urls import reverse
from django.core.cache import cache

from posts.models import Post, Group, User

USERNAME = 'test_user'
USERNAME_2 = 'another_author'
SLUG = 'test_slug'
INDEX_URL = reverse('posts:index')
GROUP_URL = reverse('posts:group', args=[SLUG])
NEW_POST_URL = reverse('posts:new_post')
PROFILE_URL = reverse('posts:profile', args=[USERNAME])
ABOUT_AUTHOR_URL = reverse('about:author')
ABOUT_TECH_URL = reverse('about:tech')
FOLLOW_INDEX_URL = reverse('posts:follow_index')


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username=USERNAME)
        cls.group = Group.objects.create(
            title='Test',
            slug=SLUG,
            description='Много букв'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
        )
        cls.POST_EDIT_PAGE_URL = reverse(
            'posts:post_edit',
            args=[USERNAME, cls.post.id]
        )
        cls.POST_PAGE_URL = reverse(
            'posts:post',
            args=[USERNAME, cls.post.id]
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        cache.clear()
        templates_url_names = {
            INDEX_URL: 'index.html',
            GROUP_URL: 'group.html',
            NEW_POST_URL: 'new_post.html',
            PROFILE_URL: 'profile.html',
            self.POST_PAGE_URL: 'post.html',
            self.POST_EDIT_PAGE_URL: 'new_post.html',
            FOLLOW_INDEX_URL: 'follow.html'
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_user_can_get_current_pages(self):
        """Страницы доступны пользователям."""
        url_status_code = [
            [self.guest_client.get(INDEX_URL).status_code,
             200],
            [self.guest_client.get(GROUP_URL).status_code,
             200],
            [self.guest_client.get(ABOUT_AUTHOR_URL).status_code,
             200],
            [self.guest_client.get(ABOUT_TECH_URL).status_code,
             200],
            [self.guest_client.get(PROFILE_URL).status_code,
             200],
            [self.guest_client.get(self.POST_PAGE_URL).status_code,
             200],
            [self.authorized_client.get(NEW_POST_URL).status_code,
             200],
            [self.authorized_client.get(
                self.POST_EDIT_PAGE_URL).status_code,
             200],
            [self.authorized_client.get(FOLLOW_INDEX_URL).status_code,
             200],
        ]
        for response_code, code in url_status_code:
            with self.subTest():
                self.assertEquals(response_code, code)

    def test_guest_user_can_not_get_current_pages(self):
        """Страницы, доступные только авторизированным пользователям,
        перенаправят анонимного пользователя на страницу регистрации"""
        another_user = User.objects.create(username=USERNAME_2)
        self.authorized_client.force_login(another_user)

        urls = [
            [self.guest_client.get(NEW_POST_URL, follow=True),
             f'{settings.LOGIN_URL}?next={NEW_POST_URL}'],
            [self.guest_client.get(self.POST_EDIT_PAGE_URL, follow=True),
             f'{settings.LOGIN_URL}?next={self.POST_EDIT_PAGE_URL}'],
            [self.authorized_client.get(
                self.POST_EDIT_PAGE_URL,
                follow=True),
                self.POST_PAGE_URL],
            [self.guest_client.get(FOLLOW_INDEX_URL, follow=True),
             f'{settings.LOGIN_URL}?next={FOLLOW_INDEX_URL}'],
        ]
        for page_url, checking_each_page in urls:
            with self.subTest():
                self.assertRedirects(
                    page_url,
                    checking_each_page
                )
