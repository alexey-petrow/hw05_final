from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image',)
        labels = {
            'text': 'Текст поста',
            'group': 'Группа',
        }
        help_texts = {
            'group': 'Группа, к которой будет относиться пост',
            'image': 'Загрузка изображения для поста',
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
