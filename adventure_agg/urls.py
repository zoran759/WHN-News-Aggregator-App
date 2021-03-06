"""WHITE HAT NEWS URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from posts import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.views.generic.base import TemplateView

urlpatterns = [
    path('WHN@dm!n/', admin.site.urls),
    path('api/new_feedly_entry/', views.feedly_hook),
    path('api/get_popular_post', views.get_popular_article_view),
    path('', views.IndexView.as_view(), name='index'),
    path('latest/', views.IndexLatestView.as_view(), name='index_latest'),
    path('popular/', views.IndexPopularView.as_view(), name='index_popular'),
    path('post/<pk>/', views.PostDetailView.as_view(), name='post_detail'),
    path('search/', views.SearchView.as_view(), name='search'),
    path('post/<int:post_id>/vote/', views.vote_post, name='vote_post'),
    path('post/<int:post_id>/comments/', views.comment_sort, name='sort_comments'),
    path('post/<int:post_id>/comments/<int:comment_id>/vote/', views.vote_comment, name='vote_comment'),
    path('api/suggest_news/', views.NewNewsSuggestionView.as_view(), name="suggest_news"),
    path('post/<int:post_id>/comments/new_comment/', views.new_comment, name="new_comment"),
    path('post/<int:post_id>/comments/new_comment/<int:parent_id>/', views.new_comment, name="new_comment"),
    path('accounts/register/',
         views.CustomRegistrationView.as_view(), name='django_registration_register',
    ),
    path('accounts/login/', views.CustomLoginView.as_view(),
         name='django_registration_login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(template_name="django_registration/with_base/logout.html"), name='logout'),
    path('accounts/password_reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('accounts/activate/complete/', TemplateView.as_view(
            template_name='django_registration/activation_complete.html'
        ),
        name='django_registration_activation_complete'),
    path('accounts/activate/send_again/<str:email>/', views.send_activation_again),
    re_path(r'^accounts/activate/(?P<activation_key>[-:\w]+)/$', views.CustomActivationView.as_view(),
         name='django_registration_activate'),
    path('accounts/profile/', views.UserProfileView.as_view(), name='profile'),
    path('accounts/profile/change_user_image/', views.change_user_profile_image, name='change-profile-image'),
    path('accounts/', include('django_registration.backends.activation.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('terms_of_service/', views.TermsOfServiceView.as_view(), name='terms_of_service'),
    path('', include('social_django.urls', namespace='social'))
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) \
              + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


if settings.DEBUG and 'debug_toolbar' in settings.INSTALLED_APPS:
    import debug_toolbar
    urlpatterns = [
        path('debug/', include(debug_toolbar.urls)),
    ] + urlpatterns

# if settings.DEBUG:
#     import debug_toolbar
#     urlpatterns = [
#         path('debug/', include(debug_toolbar.urls)),
#     ] + urlpatterns
