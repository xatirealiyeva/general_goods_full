import django_filters
from .models import Product


class ProductFilter(django_filters.FilterSet):
    category = django_filters.UUIDFilter(field_name="category__id")
    min_price = django_filters.NumberFilter(field_name="base_price", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="base_price", lookup_expr="lte")
    q = django_filters.CharFilter(field_name="name", lookup_expr="icontains")
    status = django_filters.CharFilter(field_name="status")

    class Meta:
        model = Product
        fields = ["category", "min_price", "max_price", "q", "status"]
