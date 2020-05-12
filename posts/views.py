from django.shortcuts import render, get_object_or_404, get_list_or_404
from .models import Post, Group, Comment, Follow
from django.contrib.auth.decorators import login_required
from .forms import PostForm, CommentForm
from django.shortcuts import redirect, reverse
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model

User = get_user_model()


def index(request):
    # in case there are no posts for index page dont use get_list_or_404
    # posts ordering is set in models (field - '-pud_date')
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'index.html', {'page': page, 'paginator': paginator})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    # do not use get_list_or_404 cuz group could have 0 posts
    posts = Post.objects.filter(group=group)
    paginator = Paginator(posts, 5)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'group.html', {'page': page, 'group': group, 'paginator': paginator})


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if request.method == 'POST':
        if form.is_valid():
            new_post = form.save(commit=False)
            new_post.author = request.user
            form.save()
            return redirect('index')
        return render(request, 'new_post.html', {'form': form})
    return render(request, 'new_post.html', {'form': form})


def profile(request, username):
    profile = get_object_or_404(User, username=username)
    # do not use get_list_or_404 cuz user could have 0 posts
    posts = Post.objects.filter(author=profile) 
    paginator = Paginator(posts, 5)
    page = paginator.get_page(request.GET.get('page'))
    allow_edit = False
    following = False
    if request.user.is_authenticated:
        if request.user.username == username:
            allow_edit = True
        try:
            Follow.objects.get(user=request.user, author=profile)
            following = True
        except Follow.DoesNotExist:
            following = False
    return render(request, 'profile.html', {'profile': profile, 'paginator': paginator, 'page': page, 'allow_edit': allow_edit, 'following': following})


def post_view(request, username, post_id):
    post = get_object_or_404(Post, id=post_id)
    profile = post.author
    form = CommentForm(request.POST or None)
    items = Comment.objects.filter(post__id=post_id)
    posts_count = Post.objects.filter(author__username=username).count()
    if request.user.username == username:
        allow_edit = True
    else:
        allow_edit = False
    return render(request, 'post.html', {'post': post, 'profile': profile, 'posts_count': posts_count, 'allow_edit': allow_edit, 'items': items, 'form': form})


@login_required
def post_edit(request, username, post_id):
    allow_edit = False
    if request.user.username != username:
        return redirect('post', username, post_id)
    else:
        allow_edit = True
    post = get_object_or_404(Post, author__username=username, id=post_id)
    form = PostForm(request.POST or None, files=request.FILES or None, instance=post)
    if request.method == 'POST' and allow_edit:
        if form.is_valid():
            form.save()
            return redirect('post', username, post_id)
        return render(request, 'new_post.html', {'form': form, 'allow_edit': allow_edit, 'username': username, 'post_id': post_id, 'post': post})
    return render(request, 'new_post.html', {'form': form, 'allow_edit': allow_edit, 'username': username, 'post_id': post_id, 'post': post})


@login_required
def add_comment(request, username, post_id):
    form = CommentForm(request.POST or None)
    if form.is_valid():
        new_comment = form.save(commit=False)
        new_comment.author = request.user
        new_comment.post = get_object_or_404(Post, id=post_id)
        form.save()
        return redirect('post', username, post_id)
    return redirect('post', username, post_id)


@login_required
def follow_index(request):
    # do not use get_list_or_404 cuz user could have 0 followings
    posts = []
    authors = Follow.objects.filter(user=request.user).values_list('author')
    if authors.count() != 0:
        posts = Post.objects.filter(author__in=authors)
    paginator = Paginator(posts, 5)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'follow.html', {'page': page, 'paginator': paginator})


@login_required
def profile_follow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    try:
        follow = Follow.objects.get(user=user, author=author)
        return redirect(reverse('profile', kwargs={'username': username}))
    except Follow.DoesNotExist:
        if user != author:
            Follow.objects.create(user=user, author=author)
        return redirect(reverse('profile', kwargs={'username': username}))


@login_required
def profile_unfollow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    try:
        follow = Follow.objects.get(user=user, author=author).delete()
        return redirect(reverse('profile', kwargs={'username': username}))
    except Follow.DoesNotExist:
        return redirect(reverse('profile', kwargs={'username': username}))


def page_not_found(request, exception):
    return render(request, 'misc/404.html', {'path': request.path}, status=404)


def server_error(request):
    return render(request, 'misc/500.html', status=500)
