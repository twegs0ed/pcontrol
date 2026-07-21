# unified_products/urls.py
from django.urls import path
from . import views

app_name = 'unified_products'

urlpatterns = [
    # === Категории ===
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/create/', views.CategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/edit/', views.CategoryUpdateView.as_view(), name='category_edit'),
    path('categories/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='category_delete'),
    
    # === Изделия ===
    path('', views.ProductListView.as_view(), name='product_list'),
    path('create/', views.ProductCreateView.as_view(), name='product_create'),
    path('scan-serial/', views.ScanSerialView.as_view(), name='scan_serial'),
    path('<int:pk>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('edit/<str:serial_number>/', views.ProductUpdateView.as_view(), name='product_edit'),
    path('delete/<int:pk>/', views.ProductDeleteView.as_view(), name='product_delete'),
    path('close/<int:pk>/', views.ProductCloseView.as_view(), name='product_close'),

    # === Экспорт ===
    path('export-pdf/<int:pk>/', views.export_single_product_pdf, name='export_single_pdf'),  
    path('export-word/<int:pk>/', views.export_single_product_word, name='export_single_word'), 
     
    
    # === AJAX ===
    path('ajax/save-image/<int:pk>/<int:field_index>/', views.ajax_save_image, name='ajax_save_image'),
    path('ajax/save-title/<int:pk>/<int:field_index>/', views.ajax_save_title, name='ajax_save_title'),
    path('ajax/delete-image/<int:pk>/<int:field_index>/', views.ajax_delete_image, name='ajax_delete_image'),
    path('ajax/check-completed/<int:pk>/', views.ajax_check_completed, name='ajax_check_completed'),
    path('ajax/search-owners/', views.ajax_search_owners, name='ajax_search_owners'),
]