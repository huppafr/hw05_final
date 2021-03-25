import shutil
import tempfile
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Post, Group, User, Follow

settings.MEDIA_ROOT = tempfile.mkdtemp(prefix='test2', dir=settings.BASE_DIR)

USERNAME = 'test_user'
USERNAME_2 = 'test_user_2'
USERNAME_3 = 'test_user_3'
AUTHOR_1 = 'test_author'
SLUG = 'test_slug'
SLUG_2 = 'test_slug_2'
INDEX_URL = reverse('posts:index')
FOLLOW_INDEX_URL = reverse('posts:follow_index')
GROUP_URL = reverse('posts:group', args=[SLUG])
GROUP_2_URL = reverse('posts:group', args=[SLUG_2])
NEW_POST_URL = reverse('posts:new_post')
PROFILE_URL = reverse('posts:profile', args=[USERNAME])
ABOUT_AUTHOR_URL = reverse('about:author')
ABOUT_TECH_URL = reverse('about:tech')
PROFILE_FOLLOW_URL = reverse('posts:profile_follow', args=[AUTHOR_1])
PROFILE_UNFOLLOW_URL = reverse('posts:profile_unfollow', args=[AUTHOR_1])

SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)


@override_settings(MEDIA_ROOT=settings.MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создадим запись в БД
        cls.user = User.objects.create(username=USERNAME)
        cls.author = User.objects.create(username=AUTHOR_1)
        cls.another_user = User.objects.create(username=USERNAME_2)
        cls.another_user_2 = User.objects.create(username=USERNAME_3)
        cls.group = Group.objects.create(
            title='Test',
            slug=SLUG,
            description='Много букв'
        )
        cls.group2 = Group.objects.create(
            title='Test 2',
            slug=SLUG_2,
            description='Много букв 2'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif',
        )
        cls.post = Post.objects.create(
            text='Пост из фикстуры',
            author=cls.user,
            group=cls.group,
            image=uploaded,

        )
        # cls.PROFILE_UNFOLLOW_URL = reverse(
        #     'posts:profile_unfollow',
        #     args=[cls.author]
        # )
        cls.POST_URL = reverse(
            'posts:post',
            args=[USERNAME, cls.post.id]
        )
        user_1 = cls.authorized_client = Client()
        user_1.force_login(cls.user)
        user_2 = cls.authorized_client_2 = Client()
        user_2.force_login(cls.another_user)
        user_3 = cls.authorized_client_3 = Client()
        user_3.force_login(cls.another_user_2)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_pages_show_correct_context(self):
        """Страница сформирована с правильным контекстом"""
        cache.clear()
        Follow.objects.create(user=self.another_user, author=self.user)
        page_urls = [
            INDEX_URL,
            GROUP_URL,
            PROFILE_URL,
            FOLLOW_INDEX_URL,
        ]
        for current_url in page_urls:
            response = self.authorized_client_2.get(current_url)
            self.assertEquals(
                response.context['page'][0],
                self.post
            )
            self.assertTrue(len(response.context['page']) == 1)

    def test_author_is_in_page_context(self):
        """Автор поста правильно передается в контекст страницы"""
        page_urls = [
            self.POST_URL,
            PROFILE_URL,
        ]
        for current_url in page_urls:
            self.assertEquals(
                self.authorized_client.get(current_url).context['author'],
                self.user
            )

    def test_post_dont_appears_on_another_group_page(self):
        """ Если при создании поста указать группу, то этот пост не появится
        на странице другой группы """
        response = self.authorized_client.get(GROUP_2_URL)
        self.assertNotIn(self.post, response.context['page'])

    def test_group_page_shows_correct_context(self):
        """Шаблон group сформирован с правильным контекстом."""
        response = self.authorized_client.get(GROUP_URL)
        self.assertEquals(response.context['group'], self.group)

    def test_post_page_show_correct_context(self):
        """Шаблон post сформирован с правильным контекстом."""
        response = self.authorized_client.get(self.POST_URL)
        self.assertEquals(response.context['post'], self.post)

    def test_cache_after_time(self):
        """Тест кеша страницы """
        response_old = self.authorized_client.get(INDEX_URL)
        Post.objects.create(
            text='abracadabra',
            author=self.user
        )
        response_new = self.authorized_client.get(INDEX_URL)
        self.assertEqual(response_old.content, response_new.content)
        cache.clear()
        response_newest = self.authorized_client.get(INDEX_URL)
        self.assertNotEqual(response_old.content, response_newest.content)

    def test_user_can_follow_author(self):
        """Проверка возможности подписки"""
        self.authorized_client.get(PROFILE_FOLLOW_URL)
        self.assertTrue(Follow.objects.get(
            user=self.user,
            author=self.author
        ))

    def test_user_can_unfollow_author(self):
        """Проверка возможности отписки"""
        Follow.objects.create(
            user=self.user,
            author=self.author
        )
        self.authorized_client.get(PROFILE_UNFOLLOW_URL)
        self.assertFalse(Follow.objects.filter(
            user=self.user,
            author=self.author).exists())

    def test_user_cant_follow_himself(self):
        """Проперка невозможности подписки на самого себя"""
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            args=[self.user]
        ))
        self.assertFalse(Follow.objects.filter(
            user=self.user,
            author=self.user).exists())

    def test_follow_context(self):
        """Новая запись пользователя появляется в ленте тех, кто на него
        подписан и не появляется в ленте тех, кто не подписан на него."""
        Follow.objects.create(user=self.another_user, author=self.user)
        self.assertNotIn(
            self.post,
            self.authorized_client_3.get(FOLLOW_INDEX_URL).context['page']
        )
