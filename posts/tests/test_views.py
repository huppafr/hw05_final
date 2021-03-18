import shutil
import tempfile
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Post, Group, User, Follow
from yatube.settings import MEDIA_ROOT, BASE_DIR

settings.MEDIA_ROOT = tempfile.mkdtemp(prefix='test2', dir=settings.BASE_DIR)

USERNAME = 'test_user'
USERNAME_2 = 'test_user_2'
AUTHOR_1 = 'test_author'
SLUG = 'test_slug'
SLUG_2 = 'test_slug_2'
INDEX_URL = reverse('posts:index')
GROUP_URL = reverse('posts:group', args=[SLUG])
GROUP_2_URL = reverse('posts:group', args=[SLUG_2])
NEW_POST_URL = reverse('posts:new_post')
PROFILE_URL = reverse('posts:profile', args=[USERNAME])
ABOUT_AUTHOR_URL = reverse('about:author')
ABOUT_TECH_URL = reverse('about:tech')
PROFILE_FOLLOW_URL = reverse('posts:profile_follow', args=[AUTHOR_1])
PROFILE_UNFOLLOW_URL = reverse('posts:profile_unfollow', args=[AUTHOR_1])
# PROFILE_FOLLOW = reverse("posts:profile_follow", args=[USERNAME]) # что это за дичь?

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
        cls.post = Post.objects.create(
            text='Пост из фикстуры',
            author=cls.user,
            group=cls.group,
        )
        cls.POST_PAGE_URL = reverse('posts:post', args=[USERNAME, cls.post.id])

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_1 = Client()
        self.authorized_client_1.force_login(self.author)
        self.authorized_client_2 = Client()
        self.authorized_client_2.force_login(self.another_user)

    def test_pages_show_correct_context(self):
        """Шаблоны сформированы с правильным контекстом."""
        cache.clear()
        page_urls = [
            INDEX_URL,
            GROUP_URL,
            PROFILE_URL,
        ]
        for current_url in page_urls:
            response = self.authorized_client.get(current_url)
            self.assertEquals(
                response.context['page'][0],
                self.post
            )
            self.assertTrue(len(response.context['page']) == 1)

    def test_author_is_in_page_context(self):
        """Автор поста правильно передается в контекст страницы"""
        page_urls = [
            self.POST_PAGE_URL,
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
        response = self.authorized_client.get(self.POST_PAGE_URL)
        self.assertEquals(response.context['post'], self.post)

    def test_index_page_cashe(self):
        """Тест кеша главной страницы"""
        cache.clear()
        # Убеждаемся, что количество постов на странице = 1
        response = self.authorized_client.get(INDEX_URL)
        self.assertTrue(len(response.context['page']) == 1)
        self.assertIn(self.post, response.context['page'])
        new_post = Post.objects.create(
            text='Проверка кеша',
            author=self.user,
            group=self.group,
        )
        self.assertNotIn(new_post, response.context['page'])

    def test_image_includes_in_page_context(self):
        '''При выводе поста с картинкой на запрашиваемой странице, 
        image передаётся в context этой страницы'''
        Post.objects.all().delete()
        cache.clear()
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif',
        )
        text = 'post with image'
        form_data = {
            'group': self.group.id,
            'text': text,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:new_post'),
            data=form_data,
            follow=True
        )
        page_urls = [
            INDEX_URL,
            PROFILE_URL,
            GROUP_URL,
        ]
        for current_url in page_urls:
            cache.clear()
            image_data = form_data['image']
            self.assertEqual(self.authorized_client.get(
                current_url).context['page'][0].image.name,
                             f'posts/{image_data.name}'
                             )

    def test_author_can_not_follow_himself(self):
        """Проверка невозможности подписки на самого себя"""
        before_follow = self.author.follower.count()
        self.authorized_client.get(PROFILE_FOLLOW_URL)
        after_follow = self.author.follower.count()
        self.assertEqual(before_follow, after_follow)

    def test_user_can_follow_author(self):
        """Проверка возможности подписки"""
        self.authorized_client.get(PROFILE_FOLLOW_URL)
        after_follow = self.user.follower.count()
        self.assertEqual(after_follow, 1)
        self.authorized_client.get(PROFILE_FOLLOW_URL)
        second_follow = self.user.follower.count()
        self.assertTrue(after_follow == second_follow)

    def test_user_can_unfollow_author(self):
        """Проверка возможности отписки"""
        Follow.objects.create(
            user=self.user,
            author=self.author
        )
        self.authorized_client.get(PROFILE_UNFOLLOW_URL)
        count = self.user.follower.count()
        self.assertTrue(count == 0)

    def test_follow_context(self):
        """Новая запись пользователя появляется в ленте тех, кто на него
        подписан и не появляется в ленте тех, кто не подписан на него."""
        Post.objects.all().delete()
        self.authorized_client_1 = Client()
        self.authorized_client_2 = Client()
        self.authorized_client_1.force_login(self.author)
        self.authorized_client_2.force_login(self.another_user)

        Post.objects.create(
            author=self.author,
            text='Тестовый текст',
            group=self.group
        )
        Post.objects.create(
            author=self.author,
            text='Тестовый текст1',
            group=self.group
        )
        Post.objects.create(
            author=self.user,
            text='Тестовый текст2',
            group=self.group
        )
        Follow.objects.create(
            user=self.user,
            author=self.author
        )
        Follow.objects.create(
            user=self.author,
            author=self.user
        )
        Follow.objects.create(
            user=self.another_user,
            author=self.user
        )
        Follow.objects.create(
            user=self.another_user,
            author=self.author
        )
        response = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        self.assertTrue(len(response.context['page']) == 2,
                        'Проверьте, что на странице `/follow/` отображается'
                        'список статей авторов на которых подписаны')
        response_1 = self.authorized_client_1.get(
            reverse('posts:follow_index')
        )
        self.assertTrue(len(response_1.context['page']) == 1,
                        'Проверьте, что на странице `/follow/` отображается'
                        'список статей авторов на которых подписаны')
        response_2 = self.authorized_client_2.get(
            reverse('posts:follow_index')
        )
        self.assertTrue(len(response_2.context['page']) == 3,
                        'Проверьте, что на странице `/follow/` отображается'
                        'список статей авторов на которых подписаны')
