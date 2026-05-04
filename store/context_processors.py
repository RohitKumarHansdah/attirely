from .models import Category

def menu_categories(request):
    # This grabs all categories and makes them available globally as 'menu_categories'
    return {'menu_categories': Category.objects.all()}