import shutil
import tempfile
from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Group, Post, User, Comment

settings.MEDIA_ROOT = tempfile.mkdtemp(prefix='test1', dir=settings.BASE_DIR)

USERNAME = 'test_user'
SLUG = 'test_slug'
SLUG_2 = 'test_grou_2'
INDEX_URL = reverse('posts:index')
GROUP_URL = reverse('posts:group', args=[SLUG])
NEW_POST_URL = reverse('posts:new_post')
PROFILE_URL = reverse('posts:profile', args=[USERNAME])
ABOUT_AUTHOR_URL = reverse('about:author')
ABOUT_TECH_URL = reverse('about:tech')
SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)


@override_settings(MEDIA_ROOT=settings.MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.form = PostForm()
        cls.guest_client = Client()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.user = User.objects.create(username=USERNAME)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.group = Group.objects.create(
            title="Тестовая группа",
            description="Группа для тестирования",
            slug=SLUG
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif',
        )
        self.post = Post.objects.create(
            text='Тестовый текст',
            author=self.user,
            group=self.group,
            image=uploaded
        )
        self.POST_EDIT_URL = reverse(
            'posts:post_edit',
            args=[USERNAME, self.post.id]
        )
        self.POST_URL = reverse(
            'posts:post',
            args=[USERNAME, self.post.id]
        )
        self.ADD_COMMENT_URL = reverse(
            'posts:add_comment',
            args=[USERNAME, self.post.id]
        )

    def test_create_post(self):
        """Валидная форма создает пост в Post."""
        Post.objects.all().delete()
        cache.clear()
        uploaded = SimpleUploadedFile(
            name='smaaaaaaaaall.gif',
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
            NEW_POST_URL,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, INDEX_URL)
        self.assertTrue(len(response.context['page']) == 1)
        last_post = response.context['page'][0]
        self.assertEqual(last_post.text, form_data['text'])
        self.assertEqual(last_post.group.id, form_data['group'])
        self.assertEqual(last_post.author.username, self.user.username)
        image_data = form_data['image']
        self.assertEqual(last_post.image.name, f'posts/{image_data.name}')

    def test_edit_post(self):
        """При редактировании поста, изменяется запись в базе данных."""
        group_2 = Group.objects.create(
            title="Тестовая группа 2",
            slug=SLUG_2
        )
        form_data = {
            'text': 'Измененный текст',
            'group': group_2.id,
        }
        response = self.authorized_client.post(
            self.POST_EDIT_URL,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, self.POST_URL)
        self.assertEquals(
            response.context['post'].text,
            form_data['text']
        )
        self.assertEquals(
            response.context['post'].group.id,
            form_data['group']
        )

    def test_new_post_page_show_correct_context(self):
        """Шаблон new_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(NEW_POST_URL)
        # Список ожидаемых типов полей формы:
        # указываем, объектами какого класса должны быть поля формы
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_create_comment(self):
        """Валидная форма создает запись в Comment."""
        Comment.objects.all().delete()
        form_data = {
            'text': 'Тестовый комментарий',
        }
        response = self.authorized_client.post(
            self.ADD_COMMENT_URL,
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, self.POST_URL)
        self.assertTrue(len(response.context['comments']) == 1)
        self.assertEquals(
            response.context['comments'][0].text,
            form_data['text']
        )
        self.assertEquals(
            response.context['comments'][0].author,
            self.user
        )

    def test_anonymous_user_cant_create_post(self):
        """Анонимный пользователь не сможет создать пост"""
        Post.objects.all().delete()
        post_text = 'абракадабра'
        form_data = {
            'group': self.group.id,
            'text': post_text
        }
        self.guest_client.post(
            NEW_POST_URL,
            data=form_data,
            follow=True
        )
        self.assertTrue(len(Post.objects.all()) == 0)

    def test_anonymous_user_cant_edit_post(self):
        """Анонимный пользователь не сможет отредактировать пост"""
        post_text = 'Измененный текст абракадабры'
        form_data = {
            'text': post_text,
        }
        self.guest_client.post(
            self.POST_EDIT_URL,
            data=form_data,
            follow=True
        )
        new_post = Post.objects.all()[0]
        self.assertEquals(self.post.text, new_post.text)
