from django.test import TestCase
from django.test import Client
from django.contrib.auth.models import User
from .models import Post
from .forms import NewPostForm
from .models import Group
from django.urls import reverse
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key


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
        self.client.get(reverse('index'))
        self.assertIsNotNone(cache.get(make_template_fragment_key('index_page')), msg='Index page should been cached')
        cache.delete(make_template_fragment_key('index_page'))
        self.client.get(reverse('post', kwargs={'username': self.user.username, 'post_id': self.post.id}))
        self.assertIsNone(cache.get(make_template_fragment_key('index_page')), msg='Only index page should be cached')

    def tearDown(self):
        self.client.logout()
