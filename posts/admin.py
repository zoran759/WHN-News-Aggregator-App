from django.contrib import admin
from posts.models import *
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import ugettext_lazy as _

admin.site.register(User)

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'post_count', 'comment_count', 'postvote_count', 'commentvote_count', 'is_fake')
    #def has_add_permission(self, request):
    #    return False

admin.site.register(UserProfile, UserProfileAdmin)

class PostAdmin(admin.ModelAdmin):
    list_display = ('title','submit_time', 'url')

admin.site.register(Post, PostAdmin)

class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'text')
    def has_add_permission(self, request):
        return False

class NewsSuggestionsAdmin(admin.ModelAdmin):
    list_display = ('__str__',)
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'url']

admin.site.register(UserNewsSuggestion, NewsSuggestionsAdmin)

admin.site.register(Comment, CommentAdmin)
admin.site.register(PostVote)
admin.site.register(CommentVote)
admin.site.register(PostFlag)
# admin.site.register(RelatedArticle)

# class InstagramImageAdmin(admin.ModelAdmin):
#     list_display = ('caption', 'submitter_username', 'num_likes', 'created_time', 'tag', 'image_url_standardres')
#
# admin.site.register(InstagramImage, InstagramImageAdmin)
#
# class InstagramCommentAdmin(admin.ModelAdmin):
#     list_display = ('body', 'submitter_username', 'created_time', 'image')
#
# admin.site.register(InstagramComment, InstagramCommentAdmin)
#
# class InstagramHashtagsToFetchAdmin(admin.ModelAdmin):
#     list_display = ('tag',)
#
# admin.site.register(InstagramHashtagsToFetch, InstagramHashtagsToFetchAdmin)
#
# admin.site.register(BufferProfile)