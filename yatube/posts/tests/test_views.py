import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django import forms
from django.core.cache import cache

from ..forms import CommentForm, PostForm
from ..models import Group, Post, Comment, Follow


User = get_user_model()


class PostViewsNamesTest(TestCase):
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
        self.authorized_author.force_login(PostViewsNamesTest.user)

    def test_views_names_for_templates(self):
        """Тест на соответствие имен ожидаемым шаблонам."""
        all_names_templates = {
            reverse('posts:index'): 'posts/index.html/',
            reverse('posts:group_list',
                    kwargs={'slug': f'{PostViewsNamesTest.group.slug}'}
                    ): 'posts/group_list.html/',
            reverse('posts:profile',
                    kwargs={'username': f'{PostViewsNamesTest.user.username}'}
                    ): 'posts/profile.html/',
            reverse('posts:post_detail',
                    kwargs={'post_id': PostViewsNamesTest.post.id}
                    ): 'posts/post_detail.html/',
            reverse('posts:post_create'): 'posts/create_post.html/',
            reverse('posts:post_edit',
                    kwargs={'post_id': PostViewsNamesTest.post.id}
                    ): 'posts/create_post.html/',
        }
        for reverse_name, template in all_names_templates.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_author.get(reverse_name)
                self.assertTemplateUsed(response, template)


class PostViewsPaginatorTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user_author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        for i in range(1, 16):
            cls.post = Post.objects.create(
                author=cls.user,
                group=cls.group,
                text=f'Text-{i}',
            )

    def setUp(self):
        self.authorized_author = Client()
        self.authorized_author.force_login(PostViewsPaginatorTest.user)
        self.posts_per_page = 10
        self.all_templates_with_paginator_and_posts_count = {
            reverse('posts:index'): Post.objects.count(),
            reverse('posts:group_list',
                    kwargs={'slug': f'{PostViewsPaginatorTest.group.slug}'}
                    ): Post.objects.filter(
                        group=PostViewsPaginatorTest.group).count(),
            reverse('posts:profile',
                    kwargs={'username':
                            f'{PostViewsPaginatorTest.user.username}'
                            }
                    ): Post.objects.filter(
                        author=PostViewsPaginatorTest.user).count(),
        }

    def test_paginator_page_1(self):
        """Тест первой страницы паджинатора."""
        for reverse_name, posts_count in (
            self.all_templates_with_paginator_and_posts_count.items()
        ):
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_author.get(reverse_name)
                expected_posts_count = 0
                if posts_count > self.posts_per_page:
                    expected_posts_count = self.posts_per_page
                else:
                    expected_posts_count = posts_count
                self.assertEqual(
                    len(response.context['page_obj']), expected_posts_count
                )

    def test_paginator_page_2(self):
        """Тест второй страницы паджинатора."""
        for reverse_name, posts_count in (
            self.all_templates_with_paginator_and_posts_count.items()
        ):
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_author.get(reverse_name + '?page=2')
                if response.status_code == 200:
                    expected_posts_count = 0
                    if posts_count - self.posts_per_page > self.posts_per_page:
                        expected_posts_count = self.posts_per_page
                    else:
                        expected_posts_count = (
                            posts_count - self.posts_per_page
                        )
                    self.assertEqual(
                        len(response.context['page_obj']), expected_posts_count
                    )


class PostViewsContextTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user_author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.group2 = Group.objects.create(
            title='Тестовая группа-2',
            slug='test-slug-2',
            description='Тестовое описание-2',
        )
        for i in range(1, 6):
            cls.post = Post.objects.create(
                author=cls.user,
                group=cls.group,
                text=f'Text-{i}',
            )

    def setUp(self):
        self.authorized_author = Client()
        self.authorized_author.force_login(PostViewsContextTest.user)

    def test_context_for_main_page_group_list_and_profile(self):
        """Тест первого элемента списка: главной страницы,
        страницы с постами группы, страницы с постами пользователя.
        """
        all_templates_with_posts = [
            reverse('posts:index'),
            reverse('posts:group_list',
                    kwargs={'slug': f'{PostViewsContextTest.group.slug}'}
                    ),
            reverse('posts:profile',
                    kwargs={'username':
                            f'{PostViewsContextTest.user.username}'
                            }
                    ),
        ]
        for reverse_name in all_templates_with_posts:
            response = self.authorized_author.get(reverse_name)
            first_object = response.context['page_obj'][0]
            post_fields_values = {
                first_object.author.username: 'user_author',
                first_object.group.title: 'Тестовая группа',
                first_object.text: 'Text-5',
            }
            for field_value, expected_value in post_fields_values.items():
                with self.subTest(field_value=field_value):
                    self.assertEqual(field_value, expected_value)

    def test_context_for_group_list(self):
        """Тест переменной group, передаваемой в context страницы
        с постами группы и тест на попадание поста в неверную группу"""
        reverse_name = reverse(
            'posts:group_list',
            kwargs={'slug': f'{PostViewsContextTest.group.slug}'}
        )
        response = self.authorized_author.get(reverse_name)
        first_object = response.context['page_obj'][0]
        self.assertEqual(response.context['group'], first_object.group)
        count_of_posts_in_group2 = (
            Post.objects.filter(group=PostViewsContextTest.group2).count())
        self.assertEqual(count_of_posts_in_group2, 0)

    def test_author_and_posts_count_for_profile_list(self):
        """Тест переменных author и posts_count для страницы
        с постами профиля"""
        expected_posts_count = Post.objects.filter(
            author=PostViewsContextTest.user).count()
        reverse_name = reverse(
            'posts:profile',
            kwargs={'username': f'{PostViewsContextTest.user.username}'}
        )
        response = self.authorized_author.get(reverse_name)
        first_object = response.context['page_obj'][0]
        self.assertEqual(response.context['author'], first_object.author)
        self.assertEqual(
            len(response.context['page_obj']), expected_posts_count
        )

    def test_post_detail_context(self):
        """Тест переменных post и posts_count для страницы поста"""
        reverse_name = reverse(
            'posts:post_detail',
            kwargs={'post_id': f'{PostViewsContextTest.post.id}'}
        )
        response = self.authorized_author.get(reverse_name)
        posts_count = Post.objects.filter(
            author=PostViewsContextTest.post.author
        ).count()
        self.assertEqual(response.context['posts_count'], posts_count)
        self.assertEqual(
            response.context['post'],
            Post.objects.get(id=PostViewsContextTest.post.id)
        )

    def test_context_for_post_create_and_edit_views(self):
        """Тест переменной form для страниц создания и редактирования
        поста"""
        all_names_templates = [
            reverse('posts:post_create'),
            reverse(
                'posts:post_edit',
                kwargs={'post_id': f'{PostViewsContextTest.post.id}'}
            ),
        ]
        for reverse_name in all_names_templates:
            response = self.authorized_author.get(reverse_name)
            form_fields_expect = {
                'text': forms.fields.CharField,
                'group': forms.fields.ChoiceField,
            }
            for value, expected in form_fields_expect.items():
                with self.subTest(value=value):
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, expected)


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsImageTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user_author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.test_image = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.test_image_2 = SimpleUploadedFile(
            name='small_2.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Text',
            image=cls.test_image,
        )
        cls.form = PostForm()

    def setUp(self):
        self.authorized_author = Client()
        self.authorized_author.force_login(PostViewsImageTest.user)
        cache.clear()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_image_in_context(self):
        """При выводе поста в шаблон, картинка передается в context"""
        templates = [
            reverse('posts:index'),
            reverse('posts:group_list',
                    kwargs={'slug': f'{PostViewsImageTest.group.slug}'}
                    ),
            reverse('posts:profile',
                    kwargs={
                        'username': f'{PostViewsImageTest.user.username}'
                    }
                    ),
            reverse('posts:post_detail',
                    kwargs={'post_id': PostViewsImageTest.post.id}
                    ),
        ]
        for reversed_name in templates:
            with self.subTest(reversed_name=reversed_name):
                response = self.authorized_author.get(reversed_name)
                value = response.context.get('post')
                expected = PostViewsImageTest.post.image
                self.assertEqual(value.image, expected)

    def test_create_post_with_image(self):
        """Создании нового поста с картинкой через форму работает правильно"""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст',
            'group': PostViewsImageTest.group.id,
            'image': PostViewsImageTest.test_image_2,
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
                kwargs={'username': PostViewsImageTest.user.username}
            )
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        last_post = Post.objects.order_by('-pub_date')[0]
        self.assertTrue(Post.objects.filter(
            id=last_post.id,
            text=form_data['text'],
            group=form_data['group'],
            image='posts/small_2.gif',
        ).exists()
        )


class CommentsViewsTest(TestCase):
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
            group=cls.group,
            text='Text',
        )
        cls.form = CommentForm()

    def setUp(self):
        self.authorized_author = Client()
        self.authorized_author.force_login(CommentsViewsTest.user)

    def test_comment_create_for_anonim_user(self):
        """Тест возможности добавлять коментарии
        только для авторизированных пользователей"""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый комментарий',
        }
        self.client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': CommentsViewsTest.post.id}
            ),
            data=form_data,
            follow=True,
        )
        self.assertNotEqual(Comment.objects.count(), comments_count + 1)

    def test_comment_appeared_in_post_detail(self):
        """Тест корректной работы добавления комментария к посту"""
        form_data = {
            'text': 'Тестовый комментарий',
        }
        self.authorized_author.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': CommentsViewsTest.post.id}
            ),
            data=form_data,
            follow=True,
        )
        last_comment = Comment.objects.filter(
            post=CommentsViewsTest.post.id).order_by('-created')[0]
        self.assertTrue(Comment.objects.filter(
            post=last_comment.post,
            text=form_data['text'],
        ).exists()
        )

    def test_cache(self):
        """Тест корректной работы кеширования, после удаления поста
        содержимое response.content у 1 и 2 запростов должны быть разными"""
        new_post = Post.objects.create(
            author=CommentsViewsTest.user,
            text='Text12345',
        )
        first_response = self.client.get(reverse('posts:index'))
        new_post.delete()
        second_response = self.client.get(reverse('posts:index'))
        self.assertEqual(first_response.content, second_response.content)


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_follower = User.objects.create_user(username='user_follower')
        cls.user_not_follower = User.objects.create_user(
            username='user_not_follower')
        cls.vasia_author = User.objects.create_user(username='vasia_author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.vasia_author,
            group=cls.group,
            text='Text',
        )

    def setUp(self):
        self.authorized_author = Client()
        self.authorized_author.force_login(FollowViewsTest.user_follower)

    def test_follow(self):
        """Тест подписки и отписки от автора"""
        new_follow = Follow.objects.create(
            user=FollowViewsTest.user_follower,
            author=FollowViewsTest.vasia_author,
        )
        authors = Follow.objects.filter(user=FollowViewsTest.user_follower)
        authors_list = [author.author for author in authors]
        self.assertIn(FollowViewsTest.vasia_author, authors_list)

        new_follow.delete()
        authors = Follow.objects.filter(user=FollowViewsTest.user_follower)
        authors_list = [author.author for author in authors]
        self.assertNotIn(FollowViewsTest.vasia_author, authors_list)

    def test_follower_has_posts_he_followed(self):
        """Тест: новая запись появляется в ленте тех, кто на него подписан
        и не появляется в ленте тех, кто не подписан."""
        Follow.objects.create(
            user=FollowViewsTest.user_follower,
            author=FollowViewsTest.vasia_author,
        )
        Post.objects.create(
            author=FollowViewsTest.vasia_author,
            group=FollowViewsTest.group,
            text='Text2',
        )
        authors = Follow.objects.filter(user=FollowViewsTest.user_follower)
        post_list_followed = Post.objects.filter(
            author__in=[author.author for author in authors])
        author_posts = Post.objects.filter(author=FollowViewsTest.vasia_author)
        for post in author_posts:
            self.assertIn(post, post_list_followed)

        authors = Follow.objects.filter(user=FollowViewsTest.user_not_follower)
        post_list_followed = Post.objects.filter(
            author__in=[author.author for author in authors])
        author_posts = Post.objects.filter(author=FollowViewsTest.vasia_author)
        for post in author_posts:
            self.assertNotIn(post, post_list_followed)
