from django.urls import path
from django.contrib.auth import views as auth_views
from . import admin_views, admin_views_shop

urlpatterns = [
    path('',               admin_views.dashboard,          name='ghd_dashboard'),
    path('services/',      admin_views.services_view,       name='ghd_services'),
    path('availability/',  admin_views.availability_view,   name='ghd_availability'),
    path('appointments/',  admin_views.appointments_view,   name='ghd_appointments'),
    path('users/',         admin_views.users_view,           name='ghd_users'),
    path('gallery/',       admin_views.gallery_view,         name='ghd_gallery'),
    path('reviews/',       admin_views.reviews_view,         name='ghd_reviews'),
    path('shop/products/', admin_views_shop.shop_products_view, name='ghd_shop_products'),
    path('shop/orders/',   admin_views_shop.shop_orders_view,   name='ghd_shop_orders'),

    # Auth
    path('login/',  auth_views.LoginView.as_view(template_name='ghd_admin/login.html'),       name='ghd_login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/admin/login/'),                 name='ghd_logout'),

    # AJAX APIs
    path('api/toggle-date/',                          admin_views.api_toggle_date,          name='ghd_api_toggle_date'),
    path('api/update-schedule/',                      admin_views.api_update_schedule,      name='ghd_api_update_schedule'),
    path('api/booking-settings/update/',               admin_views.api_update_booking_settings, name='ghd_api_booking_settings'),
    path('api/categories/add/',                        admin_views.api_add_category,            name='ghd_api_cat_add'),
    path('api/categories/<int:cat_id>/delete/',        admin_views.api_delete_category,         name='ghd_api_cat_delete'),
    path('api/services/add/',                         admin_views.api_add_service,          name='ghd_api_add_service'),
    path('api/services/<int:service_id>/update/',     admin_views.api_update_service,       name='ghd_api_update_service'),
    path('api/services/<int:service_id>/delete/',     admin_views.api_delete_service,       name='ghd_api_delete_service'),
    path('api/appointments/<int:appt_id>/update/',    admin_views.api_update_appointment,   name='ghd_api_update_appt'),
    path('api/users/add/',                            admin_views.api_add_user,             name='ghd_api_add_user'),
    path('api/users/<int:user_id>/delete/',           admin_views.api_delete_user,          name='ghd_api_delete_user'),
    path('api/gallery/add/',                          admin_views.api_gallery_add,          name='ghd_api_gallery_add'),
    path('api/gallery/<int:photo_id>/update/',        admin_views.api_gallery_update,       name='ghd_api_gallery_update'),
    path('api/gallery/<int:photo_id>/delete/',        admin_views.api_gallery_delete,       name='ghd_api_gallery_delete'),
    path('api/reviews/add/',                          admin_views.api_review_add,           name='ghd_api_review_add'),
    path('api/reviews/<int:review_id>/update/',       admin_views.api_review_update,        name='ghd_api_review_update'),
    path('api/reviews/<int:review_id>/delete/',       admin_views.api_review_delete,        name='ghd_api_review_delete'),

    # Shop AJAX APIs
    path('api/shop/categories/add/',                      admin_views_shop.api_shop_add_category,    name='ghd_api_shop_cat_add'),
    path('api/shop/categories/<int:category_id>/update/', admin_views_shop.api_shop_update_category, name='ghd_api_shop_cat_update'),
    path('api/shop/categories/<int:category_id>/delete/', admin_views_shop.api_shop_delete_category, name='ghd_api_shop_cat_delete'),
    path('api/shop/products/add/',                        admin_views_shop.api_shop_add_product,      name='ghd_api_shop_product_add'),
    path('api/shop/products/<int:product_id>/update/',    admin_views_shop.api_shop_update_product,   name='ghd_api_shop_product_update'),
    path('api/shop/products/<int:product_id>/delete/',    admin_views_shop.api_shop_delete_product,   name='ghd_api_shop_product_delete'),
    path('api/shop/orders/<int:order_id>/update-status/', admin_views_shop.api_order_update_status,   name='ghd_api_shop_order_status'),

    # Shop option groups / values / photos
    path('api/shop/products/<int:product_id>/options/add/',    admin_views_shop.api_shop_add_option_group,    name='ghd_api_shop_opt_group_add'),
    path('api/shop/options/<int:group_id>/update/',             admin_views_shop.api_shop_update_option_group, name='ghd_api_shop_opt_group_update'),
    path('api/shop/options/<int:group_id>/delete/',             admin_views_shop.api_shop_delete_option_group, name='ghd_api_shop_opt_group_delete'),
    path('api/shop/options/<int:group_id>/values/add/',         admin_views_shop.api_shop_add_option_value,    name='ghd_api_shop_opt_value_add'),
    path('api/shop/option-values/<int:value_id>/update/',       admin_views_shop.api_shop_update_option_value, name='ghd_api_shop_opt_value_update'),
    path('api/shop/option-values/<int:value_id>/delete/',       admin_views_shop.api_shop_delete_option_value, name='ghd_api_shop_opt_value_delete'),
    path('api/shop/products/<int:product_id>/variants/set/',    admin_views_shop.api_shop_set_variant,         name='ghd_api_shop_variant_set'),
    path('api/shop/products/<int:product_id>/images/add/',      admin_views_shop.api_shop_add_image,           name='ghd_api_shop_image_add'),
    path('api/shop/images/<int:image_id>/update/',              admin_views_shop.api_shop_update_image,        name='ghd_api_shop_image_update'),
    path('api/shop/images/<int:image_id>/delete/',               admin_views_shop.api_shop_delete_image,        name='ghd_api_shop_image_delete'),
]
