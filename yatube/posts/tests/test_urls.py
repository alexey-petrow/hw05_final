from django.test import TestCase, Client
from django.contrib.auth import get_user_model

from ..models import Group, Post


User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user_author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост Тестовый пост Тестовый пост',
        )

    def setUp(self):
        self.authorized_author = Client()
        self.authorized_author.force_login(PostURLTests.user)
        self.authorized_user = Client()
        self.user_not_author = (
            User.objects.create_user(username='user_not_author'))
        self.authorized_user.force_login(self.user_not_author)

    def test_posts_urls_for_anonim_user(self):
        """Тест доступности всех урлов для неавторизованного пользователя"""
        all_urls = {
            '/': 200,
            f'/group/{PostURLTests.group.slug}/': 200,
            f'/profile/{self.user_not_author}/': 200,
            f'/posts/{PostURLTests.post.id}/': 200,
            '/create/': 302,
            f'/posts/{PostURLTests.post.id}/edit/': 302,
            '/not_existed_page': 404,
        }
        for adress, response_status in all_urls.items():
            with self.subTest(adress=adress):
                response = self.client.get(adress)
                self.assertEqual(response.status_code, response_status)

    def test_posts_urls_for_authorized_user(self):
        """Тест доступности всех урлов для авторизованного пользователя"""
        all_urls = {
            '/': 200,
            f'/group/{PostURLTests.group.slug}/': 200,
            f'/profile/{self.user_not_author}/': 200,
            f'/posts/{PostURLTests.post.id}/': 200,
            '/create/': 200,
            f'/posts/{PostURLTests.post.id}/edit/': 302,
            '/not_existed_page': 404,
        }
        for adress, response_status in all_urls.items():
            with self.subTest(adress=adress):
                response = self.authorized_user.get(adress)
                self.assertEqual(response.status_code, response_status)

    def test_posts_urls_for_author(self):
        """Тест доступности всех урлов для автора"""
        all_urls = {
            '/': 200,
            f'/group/{PostURLTests.group.slug}/': 200,
            f'/profile/{self.user_not_author}/': 200,
            f'/posts/{PostURLTests.post.id}/': 200,
            '/create/': 200,
            f'/posts/{PostURLTests.post.id}/edit/': 200,
            '/not_existed_page': 404,
        }
        for adress, response_status in all_urls.items():
            with self.subTest(adress=adress):
                response = self.authorized_author.get(adress)
                self.assertEqual(response.status_code, response_status)

    def test_posts_create_edit_redirect_for_anonim_user(self):
        """Тест на соответствия адреса после переадресации,
        ожидаемому, при попытке создания и редактирования
        поста для неавторизированного пользователя"""
        all_urls_for_redirect = {
            '/create/': '/auth/login/?next=/create/',
            f'/posts/{PostURLTests.post.id}/edit/':
            f'/auth/login/?next=/posts/{PostURLTests.post.id}/edit/',
        }
        for adress, redirect_adress in all_urls_for_redirect.items():
            with self.subTest(adress=adress):
                response = self.client.get(adress)
                self.assertRedirects(response, redirect_adress)

    def test_posts_edit_redirect_for_autrorized_user(self):
        """Тест на соответствия адреса после переадресации, ожидаемому,
        при попытке редактирования поста для авторизированного пользователя"""
        response = self.authorized_user.get(
            f'/posts/{PostURLTests.post.id}/edit/'
        )
        self.assertRedirects(response, f'/posts/{PostURLTests.post.id}/')

    def test_posts_templates(self):
        """Тест соответствия всех адресов с шаблонами"""
        all_urls_templates = {
            '/': 'posts/index.html/',
            f'/group/{PostURLTests.group.slug}/': 'posts/group_list.html/',
            f'/profile/{self.user_not_author}/': 'posts/profile.html/',
            f'/posts/{PostURLTests.post.id}/': 'posts/post_detail.html/',
            '/create/': 'posts/create_post.html/',
            f'/posts/{PostURLTests.post.id}/edit/': 'posts/create_post.html/',
            '/not_existed_page': 'core/404.html',
        }
        for adress, template in all_urls_templates.items():
            with self.subTest(adress=adress):
                response = self.authorized_author.get(adress)
                self.assertTemplateUsed(response, template)
