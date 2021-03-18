from django.urls import reverse

USERNAME = 'test_user'
SLUG = 'test_slug'
POST_ID = 32


def test_route_calculations_match_the_expected_URL(self):
    """расчеты маршрута соответствуют ожидаемому URL."""
    url_names = {
        '/': reverse('posts:index'),
        f'/group/{SLUG}/': reverse('posts:group', args=[SLUG]),
        '/new/': reverse('posts:new_post'),
        f'/{USERNAME}/': reverse('posts:profile', args=[USERNAME]),
        f'/{USERNAME}/{POST_ID}/':
            reverse('posts:post', args=[USERNAME, POST_ID]),
        f'/{USERNAME}/{POST_ID}/edit':
            reverse('posts:post_edit', args=[USERNAME, POST_ID])
    }

    for url, route in url_names.items():
        self.assertEqual(url, route)
