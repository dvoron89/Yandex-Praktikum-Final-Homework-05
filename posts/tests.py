from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import Post, Group, Follow
from .forms import PostForm
from django.urls import reverse
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.core.paginator import Paginator
import time


class TestMemasik(TestCase):
    def test_Natasha(self):
        self.assertTrue(False, msg = 'Наташ, все упало')

class TestPosts(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username = 'test_dummy',
            password = 'test'
        )
        self.group = Group.objects.create(
            title = 'Best Group Ever',
            slug = 'bge',
            description = 'Best group you ever see. Really. Best one'
        )
        self.post = Post.objects.create(
            text = 'I am new beautiful post, love me',
            group = self.group,
            author = self.user,
            image = 'posts/bender_icon.png'
        )
        for i in range(0, 100):
            Post.objects.create(
                text = f'some text #{i}',
                author = self.user,
                image = 'posts/bender_icon.png'
            )

    # 1 registration of new user and check profile page avl
    def test_new_user_reg(self):
        self.new_user = User.objects.create_user(
            username = 'new_user',
            password = 'new_test'
        )
        self.assertIn(self.new_user, User.objects.all(), msg = 'New user was not created')
        response = self.client.get(reverse('profile', kwargs = {'username' : self.new_user.username}))
        self.assertEqual(response.status_code, 200, msg = 'New user has no profile page')
        

    # 1 check profile page of premade user
    def test_profile_creation(self):
        response = self.client.get(reverse('profile', kwargs = {'username' : self.user.username}))
        self.assertEqual(response.status_code, 200, msg = 'Profile page was not created for new user')

    # 2 premade user login and attempting to create new post
    def test_login_and_new_post(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('new_post'), follow = False)
        self.assertEqual(response.status_code, 200, msg = 'Authorized person should have access to create new post')
        test_text = 'I am new test post, should have id = 2'
        response = self.client.post(reverse('new_post'), {'text' : test_text}, follow = True)
        self.new_post = Post.objects.get(text = test_text)
        self.assertIn(self.new_post, Post.objects.all(), msg = 'New post is not in Post')

    # 3 logout user attempt to create new post
    def test_logout_and_new_post(self):
        response = self.client.get('/new/', follow = True)
        self.assertRedirects(
            response, 
            '/auth/login/?next=/new/', 
            status_code = 302, 
            target_status_code = 200, 
            msg_prefix = 'Unauthorized person should not have access to create new post', 
            fetch_redirect_response = True)

    # 4 check new post is avl at index, profile and post pages
    def test_new_post_creation(self):
        self.client.force_login(self.user)
        test_text = 'I am new test post, should have id = 2'
        self.client.post(reverse('new_post'), {'text' : test_text}, follow = True)
        self.new_post = Post.objects.get(text = test_text)

        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200, msg = "Index page is not avl somewhy")
        self.assertIn(self.new_post, response.context['page'], msg = 'New post is not on the index page')

        response = self.client.get(reverse('profile', kwargs = {'username' : self.user.username}))
        self.assertEqual(response.status_code, 200, msg = "Profile page is not avl somewhy")
        self.assertIn(self.new_post, response.context['page'], msg = 'New post is not on the profile page')

        response = self.client.get(reverse('post', kwargs = {'username' : self.user.username, 'post_id' : self.new_post.id}))
        self.assertEqual(response.status_code, 200, msg = "Post page is not avl somewhy")
        self.assertEqual(self.new_post, response.context['post'], msg = 'New post is not on the post page')

    # 5 check edited post is refreshed at index. profile and post pages
    def test_edit_post(self):
        self.client.force_login(self.user)
        test_text = 'I am new test post, should have id = 2'
        new_text = 'I am still that old post with pk = 1, but with new text'
        self.client.post(reverse('new_post'), {'text' : test_text})
        self.new_post = Post.objects.get(text = test_text)

        response = self.client.post(reverse('post_edit', kwargs = {'username' : self.user.username, 'post_id' : self.new_post.id}), {'text' : new_text}, follow = True)
        self.assertEqual(response.status_code, 200, msg = 'Authorized person should be able to edit his post')

        self.new_post = Post.objects.get(text = new_text)

        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200, msg = "Index page is not avl somewhy")
        self.assertIn(self.new_post, response.context['page'], msg = 'Refreshed post is not on the index page')

        response = self.client.get(reverse('profile', kwargs = {'username' : self.user.username}))
        self.assertEqual(response.status_code, 200, msg = "Profile page is not avl somewhy")
        self.assertIn(self.new_post, response.context['page'], msg = 'Refreshed post is not on the profile page')

        response = self.client.get(reverse('post', kwargs = {'username' : self.user.username, 'post_id' : self.new_post.id}))
        self.assertEqual(response.status_code, 200, msg = "Post page is not avl somewhy")
        self.assertEqual(self.new_post, response.context['post'], msg = 'Refreshed post is not on the post page')

    def test_404(self):
        fairy_url = 'page_that_never_exist'
        response = self.client.get('/' + fairy_url + '/', follow = False)
        self.assertEqual(response.status_code, 404, msg = 'You reached unreachable page! GJ! Not really, it should return 404 instead')

    def test_img_tag(self):
        response = self.client.get(reverse('post', kwargs = {'username' : self.post.author.username, 'post_id' : self.post.id}))
        self.assertContains(response, '<img', count = None, status_code = 200, msg_prefix = 'Post has image, but it does not shown on the post page')
        response = self.client.get(reverse('index'))
        self.assertContains(response, '<img', count = None, status_code = 200, msg_prefix = 'Post has image, but it does not shown on the index page')
        response = self.client.get(reverse('profile', kwargs = {'username' : self.user.username}))
        self.assertContains(response, '<img', count = None, status_code = 200, msg_prefix = 'Post has image, but it does not shown on the profile page')
        response = self.client.get(reverse('group', kwargs = {'slug' : self.group.slug}))
        self.assertContains(response, '<img', count = None, status_code = 200, msg_prefix = 'Post has image, but it does not shown on the group page')

    def test_not_img_protection(self):
        self.client.force_login(self.user)
        # remember the post before attempt to edit
        self.post_before = self.post
        with open('media/posts/fails.txt', 'rb') as image: # parse wrong format
            response = self.client.post(reverse('post_edit', kwargs = {
                'username' : self.user.username, 
                'post_id' : self.post.id}), 
                    {'text' : 'I am trying to put txt instead of img' ,
                    'image' : image}, 
                        follow = False)
        # remember the post after attempt to edit 
        self.post_after = Post.objects.get(id = self.post.id)
        self.assertEqual(self.post_before, self.post_after, msg = 'Wrong image format was passed, but post was edited anyways')
        self.assertEqual(response.status_code, 200, msg = 'After failing to edit post with wrong image format you should stay on the same page for next attempt')

        text = 'I am trying to create new post with txt instead of image'
        with open('media/posts/fails.txt', 'rb') as image:
            response = self.client.post(reverse('new_post'), {'text': text, 'image': image}, follow=False)
        self.assertFalse(Post.objects.filter(text=text),
                         msg='New post with wrong image format was created')
        self.assertEqual(response.status_code, 200, msg='After failing to create post with wrong image format you should stay on the same page for next attempt')


    def test_cache_index_page(self):
        response = self.client.get(reverse('index'))
        # every iteration check if cache exists exactly for current page
        for index in response.context['paginator'].page_range:
            inner_response = self.client.get(reverse('index') + f'/?page={index}')
            self.assertIsNotNone(
                cache.get(
                    make_template_fragment_key(
                        'index_page', 
                        [response.context['paginator'].get_page(index)])), 
                        msg=f'Index page should been cached, error at page - {index}')
            posts_on_this_page = inner_response.context['paginator'].get_page(index)
            # every inner iteration check if cache contains text for post from current page
            for post in posts_on_this_page:
                self.assertIn(
                    post.text, 
                    cache.get(
                        make_template_fragment_key(
                            'index_page', 
                            [response.context['paginator'].get_page(index)])), 
                            msg=f'Post is not cached. Post content - {post.text}')

        # have to wait at least 20 seconds to let cache clear itself
        print('Я НЕ ЗАВИС, Я ТАК РАБОТАЮ. ПОДОЖДИ 25 СЕКУНД')
        for seconds in range(0, 25):
            print(25 - seconds)
            time.sleep(1)

        # every iteration check cache is not exists for current page
        for index in response.context['paginator'].page_range:
            self.assertIsNone(
                cache.get(
                    make_template_fragment_key(
                        'index_page', 
                        [response.context['paginator'].get_page(index)])), 
                        msg=f'Cache from index page should be cleared, error at page - {index}')


    def test_follow_unfollow(self):
        self.client.force_login(self.user)
        self.best_author_ever = User.objects.create_user(
            username = 'Max Power',
            password = 'godlike'
        )
        response = self.client.post(reverse('profile_follow', kwargs={'username': self.best_author_ever.username}), follow=True)
        self.assertEqual(response.status_code, 200, msg='Authorized user should be able to reach follow page')
        self.follows_count = Follow.objects.count()
        self.assertIn(Follow.objects.get(user=self.user, author=self.best_author_ever), Follow.objects.all(), msg='Authorized user should be able to follow author')
        self.client.post(reverse('profile_follow', kwargs={'username': self.best_author_ever.username}), follow=True)
        self.follow_obj = Follow.objects.get(user=self.user, author=self.best_author_ever)
        self.assertEqual(self.follows_count, Follow.objects.count(), msg='Double following should not happen')
        response = self.client.post(reverse('profile_unfollow', kwargs={'username': self.best_author_ever.username}), follow=True)
        self.assertEqual(response.status_code, 200, msg='Authorized user should be able to reach unfollow page')
        self.assertNotIn(self.follow_obj, Follow.objects.all(), msg='Authorized user should be able to unfollow author')
        self.follows_count = Follow.objects.count()
        self.client.post(reverse('profile_unfollow', kwargs={'username': self.best_author_ever.username}), follow=True)
        self.assertEqual(self.follows_count, Follow.objects.count(), msg='Cant unfollow author that you never followed')

        self.client.logout()
        self.follow_obj = Follow.objects.create(
            user = self.user,
            author = self.best_author_ever
        )
        self.follows_count = Follow.objects.count()
        response = self.client.post(reverse('profile_follow', kwargs={'username': self.best_author_ever.username}), follow=True)
        self.assertContains(response, '/auth/login/', msg_prefix='Unauthorized user should be redirected to authorization page')
        self.assertEqual(self.follows_count, Follow.objects.count(), msg='Follow object was created by unauthorized user')
        response = self.client.post(reverse('profile_unfollow', kwargs={'username': self.best_author_ever.username}), follow=True)
        self.assertContains(response, '/auth/login/', msg_prefix='Unauthorized user should be redirected to authorization page')
        self.assertEqual(self.follows_count, Follow.objects.count(), msg='Follow object was destoyed by unauthorized user')


    def test_personal_feed(self):
        self.author = User.objects.create_user(
            username = 'author',
            password = 'author'
        )
        self.sub = User.objects.create_user(
            username = 'sub',
            password = 'sub'
        )
        self.unsub = User.objects.create_user(
            username = 'unsub',
            password = 'unsub'
        )
        self.authors_post = Post.objects.create(
            text = 'Best text',
            author = self.author
        )
        self.following = Follow.objects.create(
            user = self.sub,
            author = self.author
        )
        self.client.force_login(self.sub)
        response = self.client.get(reverse('follow_index'))
        self.assertContains(response, self.authors_post.text, msg_prefix='Subscriber should see posts from followed authors')
        self.client.force_login(self.unsub)
        response = self.client.get(reverse('follow_index'))
        self.assertNotContains(response, self.authors_post.text, msg_prefix='Only followed authors should appear at follow_index page')


    def test_comment_post(self):
        response = self.client.post(reverse('add_comment', kwargs={'username': self.post.author.username, 'post_id': self.post.id}), follow=True)
        self.assertContains(response, '/auth/login/', msg_prefix='Unauthorized user should be redirected to authorization page')

        self.client.force_login(self.user)
        response = self.client.post(reverse('add_comment', kwargs={'username': self.post.author.username, 'post_id': self.post.id}), follow=True)
        self.assertNotContains(response, '/auth/login/', msg_prefix='Authorized user should have assecc to comment post')

    def tearDown(self):
        self.client.logout()