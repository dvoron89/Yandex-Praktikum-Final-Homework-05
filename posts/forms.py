from .models import Post, Comment
from django import forms


class NewPostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')


class NewCommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
