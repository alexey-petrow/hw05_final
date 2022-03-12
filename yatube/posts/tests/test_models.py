from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post


User = get_user_model()


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )

    def test_verbose_name(self):
        """verbose_name полей соответствует ожидаеым"""
        group = GroupModelTest.group
        field_verboses = {
            'title': 'Название группы',
            'slug': 'Url адрес группы',
            'description': 'Описание группы',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    group._meta.get_field(field).verbose_name,
                    expected_value
                )

    def test_group_str_method(self):
        """str method возвращает имя объекта"""
        group = GroupModelTest.group
        expected_name = group.title
        self.assertEqual(expected_name, group.__str__())


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост Тестовый пост Тестовый пост',
        )

    def test_verbose_name(self):
        """verbose_name полей соответствует ожидаеым"""
        post = PostModelTest.post
        field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор поста',
            'group': 'Группа',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name,
                    expected_value
                )

    def test_help_text(self):
        """help_text полей соответствует ожидаеым"""
        post = PostModelTest.post
        fields_help_text = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост',
        }
        for field, expected_value in fields_help_text.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text,
                    expected_value
                )

    def test_post_str_method(self):
        """str method возвращает первые 15 символов текста поста"""
        post = PostModelTest.post
        expected_name = post.text[:15]
        self.assertEqual(expected_name, post.__str__())
