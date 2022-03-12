from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

from ..models import Group, Post


User = get_user_model()


class PostFormTest(TestCase):
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
            text='Тестовый пост',
        )

    def setUp(self):
        self.authorized_author = Client()
        self.authorized_author.force_login(PostFormTest.user)

    def test_create_new_post(self):
        """Проверка создания нового поста при отправке
        и валидации данных формы"""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Test text',
            'group': PostFormTest.group.id,
        }
        response = self.authorized_author.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                kwargs={'username': PostFormTest.user.username}
            )
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        last_post = Post.objects.order_by('-pub_date')[0]
        self.assertTrue(Post.objects.filter(
            id=last_post.id,
            text=form_data['text'],
            group=form_data['group']
        ).exists()
        )

    def test_post_edit(self):
        """Проверка изменения содержания существующего поста"""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Измененный текст',
            'group': PostFormTest.group.id,
        }
        response = self.authorized_author.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostFormTest.post.id}
            ),
            data=form_data,
            folow=True,
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostFormTest.post.id}
            )
        )
        self.assertEqual(Post.objects.count(), posts_count)
        post = Post.objects.get(id=PostFormTest.post.id)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group, PostFormTest.group)
