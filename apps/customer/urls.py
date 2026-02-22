from django.urls import path
from . import views

urlpatterns = [
    path("profile/create/", views.ProfileCreateAPIView.as_view()),
    path("profile/delete/", views.ProfileDelete.as_view(), name="profile-delete"),
    path("profile/update/", views.ProfileUpdate.as_view(), name="profile-update"),
    path("location/create/", views.LocationCreateAPIView.as_view()),
    path("location/list/", views.LocationListAPIView.as_view()),
    path("location/<int:pk>/retrieve/", views.LocationRetrieveUpdateDelete.as_view()),
    path("news/list/", views.NewsListAPIView.as_view()),
    path("news/<int:pk>/retrieve/", views.NewsRetrieveUpdateDelete.as_view()),
    path("viewed/create/", views.ViewedNewsCreateAPIView.as_view()),
    # path("viewed/list/", views.ViewedNewsListAPIView.as_view()),
    # path("viewed/list/", views.ViewedNewsListAPIView.as_view()),
    path("favorite/create/", views.FavoriteCreateAPIView.as_view()),
    path(
        "remove_from_favorites/<int:product_id>/",
        views.RemoveFromFavoritesView.as_view(),
    ),
    path("favorite/list/", views.FavoriteListAPIView.as_view()),
    path("favorite/<int:pk>/retrieve/", views.FavoriteRetrieveUpdateDelete.as_view()),
    path("register/", views.RegisterView.as_view(), name="send_otp"),
    path("verify-otp/", views.VerifyRegisterOTPView.as_view(), name="verify_otp"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("set-password/", views.SetPasswordView.as_view()),
    path("profile/edit/", views.ProfileEditAPIView.as_view()),
    path("banners/", views.BannerListAPIView.as_view(), name="banner"),
    path('latest-unviewed-news/', views.LatestUnviewedNewsView.as_view(), name='latest-unviewed-news'),
    path('mark-news-as-viewed/', views.MarkNewsAsViewed.as_view(), name='mark-news-as-viewed'),

    # /api/customer/b2b/apply/ -> B2B ariza yuborish
    path("b2b/apply/", views.B2BApplicationCreateAPIView.as_view(), name="b2b-apply"),
   

]
