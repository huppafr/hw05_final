from django.conf import settings
from django.core.cache import cache
from django.test import TestCase, Client
from django.urls import reverse

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
        cls.POST_EDIT_PAGE_URL = reverse(
            'posts:post_edit',
            args=[USERNAME, cls.post.id]
        )
        cls.POST_PAGE_URL = reverse(
            'posts:post',
            args=[USERNAME, cls.post.id]
        )
        cls.PROFILE_FOLLOW_PAGE_URL = reverse(
            'posts:profile_follow',
            args=[USERNAME]
        )
        cls.PROFILE_UNFOLLOW_PAGE_URL = reverse(
            'posts:profile_unfollow',
            args=[USERNAME]
        )
        cls.ADD_COMMENT_PAGE_URL = reverse(
            'posts:add_comment',
            args=[USERNAME, cls.post.id]
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        cache.clear()
        templates_url_names = {
            INDEX_URL: 'index.html',
            GROUP_URL: 'group.html',
            NEW_POST_URL: 'new_post.html',
            PROFILE_URL: 'profile.html',
            FOLLOW_INDEX_URL: 'follow.html',
            self.POST_PAGE_URL: 'post.html',
            self.POST_EDIT_PAGE_URL: 'new_post.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                self.assertTemplateUsed(
                    self.authorized_client.get(url),
                    template
                )

    def test_user_can_get_current_pages(self):
        """Страницы доступны пользователям."""
        url_status_code = [
            [INDEX_URL, 200],
            [FOLLOW_INDEX_URL, 200],
            [GROUP_URL, 200],
            [ABOUT_AUTHOR_URL, 200],
            [ABOUT_TECH_URL, 200],
            [PROFILE_URL, 200],
            [NEW_POST_URL, 200],
            [self.POST_PAGE_URL, 200],
            [self.POST_EDIT_PAGE_URL, 200],
        ]
        for url, code in url_status_code:
            with self.subTest():
                self.assertEquals(
                    self.authorized_client.get(url).status_code,
                    code
                )

    def test_guest_user_can_not_get_current_pages(self):
        """Страницы, доступные только авторизированным пользователям,
        перенаправят анонимного пользователя на страницу регистрации"""
        urls = [
            NEW_POST_URL,
            FOLLOW_INDEX_URL,
            self.POST_EDIT_PAGE_URL,
            self.PROFILE_FOLLOW_PAGE_URL,
            self.PROFILE_UNFOLLOW_PAGE_URL,
            self.ADD_COMMENT_PAGE_URL,
        ]
        for url in urls:
            with self.subTest():
                self.assertRedirects(
                    self.guest_client.get(url, follow=True),
                    f'{settings.LOGIN_URL}?next={url}'
                )

    def test_author_cant_edit_posts_of_the_other_authors(self):
        """Авторизированный пользователь, не являющийся автором поста
        будет перенаправлен при попытке редактирования чужих постов"""
        another_user = User.objects.create(username=USERNAME_2)
        self.authorized_client.force_login(another_user)

        self.assertRedirects(
            self.authorized_client.get(self.POST_EDIT_PAGE_URL, follow=True),
            self.POST_PAGE_URL
        )
