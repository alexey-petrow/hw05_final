from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required

from .models import Post, Group, User, Comment, Follow
from .forms import PostForm, CommentForm
from .utils import add_paginator


def index(request):
    template = 'posts/index.html/'
    title = "Последние обновления на сайте"
    post_list = Post.objects.all()
    page_obj = add_paginator(post_list, request)
    context = {
        'title': title,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html/'
    group = get_object_or_404(Group, slug=slug)
    post_list = Post.objects.filter(group=group)
    page_obj = add_paginator(post_list, request)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html/'
    author = get_object_or_404(User, username=username)
    posts_count = Post.objects.filter(author=author).count()
    post_list = Post.objects.filter(author=author)
    page_obj = add_paginator(post_list, request)
    following = False
    if request.user.is_authenticated:
        # Михаил Иванов ревьюер: "Замечание так и не исправлено"
        # Так я удалил переменную, что теперь не так?
        if Follow.objects.filter(user=request.user).filter(
                author=author).exists():
            following = True
        else:
            following = False
    context = {
        'author': author,
        'user': request.user,
        'posts_count': posts_count,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html/'
    post = get_object_or_404(Post, id=post_id)
    author = post.author
    posts_count = Post.objects.filter(author=author).count()
    form = CommentForm(request.POST or None)
    post_comments = Comment.objects.filter(post=post_id)
    context = {
        'post': post,
        'posts_count': posts_count,
        'form': form,
        'comments': post_comments,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    is_edit = False
    template = 'posts/create_post.html/'
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if request.method == 'POST':
        if form.is_valid():
            new_post = form.save(commit=False)
            new_post.author = request.user
            new_post.save()
            return redirect('posts:profile', username=request.user)
        return render(request, template, {'form': form})
    context = {
        'is_edit': is_edit,
        'form': form,
    }
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    is_edit = True
    template = 'posts/create_post.html/'
    post = get_object_or_404(Post, id=post_id)
    form = PostForm(
        request.POST,
        files=request.FILES or None,
        instance=post or None,
    )
    if request.user != post.author:
        return redirect('posts:post_detail', post_id=post_id)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('posts:post_detail', post_id=post_id)
        return render(request, template, {'form': form})
    context = {
        'is_edit': is_edit,
        'form': form,
    }
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    template = 'posts/follow.html/'
    title = f"Подписки пользователя {request.user.username}"
    post_list = Post.objects.filter(
        author__following__user=request.user)
    page_obj = add_paginator(post_list, request)
    context = {
        'title': title,
        'page_obj': page_obj,
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        is_you_follow = Follow.objects.filter(
            user=request.user).filter(author=author).exists()
        if not is_you_follow:
            Follow.objects.create(
                user=request.user,
                author=author,
            )
    return redirect('posts:profile', username=author.username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    unfollow = get_object_or_404(
        Follow,
        user=request.user,
        author=author,
    )
    unfollow.delete()
    return redirect('posts:profile', username=author.username)
