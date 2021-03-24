from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import PostForm, CommentForm
from .models import Group, Post, User, Follow


@cache_page(60)
def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, settings.POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'index.html', {
        'page': page,
        'paginator': paginator
    })


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    paginator = Paginator(post_list, settings.POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'group.html', {
        'group': group,
        'page': page,
        'paginator': paginator
    })


@login_required
def new_post(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    if not form.is_valid():
        return render(request, 'new_post.html', {'form': form})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:index')


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    paginator = Paginator(post_list, settings.POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    following = (
        request.user.is_authenticated
        and (request.user != author)
        and Follow.objects.filter(
            user=request.user,
            author=author).exists()
    )
    return render(request, 'profile.html', {
        'page': page,
        'author': author,
        'paginator': paginator,
        'following': following,
    })


def post_view(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    comments = post.comments.all()
    form = CommentForm()
    following = (
        request.user.is_authenticated
        and (request.user != post.author)
        and Follow.objects.filter(
            user=request.user,
            author=post.author).exists()
    )
    return render(request, 'post.html', {
        'post': post,
        'author': post.author,
        'comments': comments,
        'form': form,
        'following': following
    })


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, id=post_id,
                             author__username=username)
    form = CommentForm(request.POST or None)
    if not form.is_valid():
        return redirect('posts:post', username, post_id)
    comment = form.save(commit=False)
    comment.author = request.user
    comment.post = post
    comment.save()
    return redirect('posts:post', username, post_id)


@login_required
def post_edit(request, username, post_id):
    if request.user.username != username:
        return redirect('posts:post', username, post_id)
    post = get_object_or_404(Post, author__username=username, id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post', username, post_id)
    return render(request, 'new_post.html', {
        "form": form,
        'post': post,
    })


@login_required
def follow_index(request):
    """Страница с постами авторов на которые подписан пользователь"""
    posts = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(posts, settings.POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'follow.html', {
        'post': posts,
        'page': page,
        'paginator': paginator,
    })


@login_required
def profile_follow(request, username):
    """Функция для подписки на автора"""
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    """Функция для отписки от автора"""
    user_following_author = Follow.objects.get(
        user=request.user,
        author__username=username)
    if user_following_author:
        user_following_author.delete()
        return redirect('posts:profile', username=username)


def page_not_found(request, exception):
    # Переменная exception содержит отладочную информацию,
    # выводить её в шаблон пользователской страницы 404 мы не станем
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)
