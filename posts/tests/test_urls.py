from django.conf import settings
from django.core.cache import cache
from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Post, Group, User

USERNAME = 'test_user'
USERNAME_2 = 'another_user'
SLUG = 'test_slug'
INDEX_URL = reverse('posts:index')
GROUP_URL = reverse('posts:group', args=[SLUG])
NEW_POST_URL = reverse('posts:new_post')
PROFILE_URL = reverse('posts:profile', args=[USERNAME])
ABOUT_AUTHOR_URL = reverse('about:author')
ABOUT_TECH_URL = reverse('about:tech')
FOLLOW_INDEX_URL = reverse('posts:follow_index')
PROFILE_FOLLOW_URL = reverse('posts:profile_follow', args=[USERNAME])
PROFILE_UNFOLLOW_URL = reverse('posts:profile_unfollow', args=[USERNAME])
URL_NOT_EXISTS = reverse(
    'posts:profile',
    args=['strhfgd_fgdht_234trsfb_fsh2_3q4ergsfd_']
)


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username=USERNAME)
        cls.another_user = User.objects.create(username=USERNAME_2)
        cls.guest_client = Client()
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
        cls.POST_EDIT_URL = reverse(
            'posts:post_edit',
            args=[USERNAME, cls.post.id]
        )
        cls.POST_URL = reverse(
            'posts:post',
            args=[USERNAME, cls.post.id]
        )
        cls.ADD_COMMENT_URL = reverse(
            'posts:add_comment',
            args=[USERNAME, cls.post.id]
        )
        user_1 = cls.authorized_client = Client()
        user_1.force_login(cls.user)
        user_2 = cls.authorized_client_2 = Client()
        user_2.force_login(cls.another_user)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        cache.clear()
        templates_url_names = {
            INDEX_URL: 'index.html',
            GROUP_URL: 'group.html',
            NEW_POST_URL: 'new_post.html',
            PROFILE_URL: 'profile.html',
            FOLLOW_INDEX_URL: 'follow.html',
            self.POST_URL: 'post.html',
            self.POST_EDIT_URL: 'new_post.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                self.assertTemplateUsed(
                    self.authorized_client.get(url),
                    template
                )

    def test_user_can_get_current_pagessss(self):
        """Проверка доступности страниц для пользователей"""
        url_status_code = [
            [self.authorized_client, INDEX_URL, 200],
            [self.authorized_client, FOLLOW_INDEX_URL, 200],
            [self.authorized_client, GROUP_URL, 200],
            [self.authorized_client, ABOUT_AUTHOR_URL, 200],
            [self.authorized_client, ABOUT_TECH_URL, 200],
            [self.authorized_client, PROFILE_URL, 200],
            [self.authorized_client, NEW_POST_URL, 200],
            [self.authorized_client, self.POST_URL, 200],
            [self.authorized_client, self.POST_EDIT_URL, 200],
            [self.authorized_client, URL_NOT_EXISTS, 404],
            # Юзер не яляется автором поста
            [self.authorized_client_2, self.POST_EDIT_URL, 302],
            [self.guest_client, INDEX_URL, 200],
            [self.guest_client, GROUP_URL, 200],
            [self.guest_client, ABOUT_AUTHOR_URL, 200],
            [self.guest_client, ABOUT_TECH_URL, 200],
            [self.guest_client, PROFILE_URL, 200],
            [self.guest_client, FOLLOW_INDEX_URL, 302],
            [self.guest_client, NEW_POST_URL, 302],
            [self.guest_client, self.POST_URL, 200],
            [self.guest_client, self.POST_EDIT_URL, 302],
            [self.guest_client, URL_NOT_EXISTS, 404],
        ]
        for client, url, code in url_status_code:
            with self.subTest(url=url):
                self.assertEquals(
                    client.get(url).status_code,
                    code
                )

    def test_guest_user_can_not_get_current_pages(self):
        """Страницы, доступные только авторизированным пользователям,
        перенаправят анонимного пользователя на страницу регистрации"""
        urls = [
            [self.guest_client, NEW_POST_URL,
             f'{settings.LOGIN_URL}?next={NEW_POST_URL}'],
            [self.guest_client, FOLLOW_INDEX_URL,
             f'{settings.LOGIN_URL}?next={FOLLOW_INDEX_URL}'],
            [self.guest_client, PROFILE_FOLLOW_URL,
             f'{settings.LOGIN_URL}?next={PROFILE_FOLLOW_URL}'],
            [self.guest_client, PROFILE_UNFOLLOW_URL,
             f'{settings.LOGIN_URL}?next={PROFILE_UNFOLLOW_URL}'],
            [self.guest_client, self.POST_EDIT_URL,
             f'{settings.LOGIN_URL}?next={self.POST_EDIT_URL}'],
            [self.guest_client, self.ADD_COMMENT_URL,
             f'{settings.LOGIN_URL}?next={self.ADD_COMMENT_URL}'],
            [self.authorized_client_2, self.POST_EDIT_URL,
             self.POST_URL],
        ]
        for client, url, redirect_url in urls:
            with self.subTest(url=url):
                self.assertRedirects(
                    client.get(url, follow=True),
                    redirect_url
                )
