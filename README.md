# Django Views AF
Adds support for views and materialized views in a django app. Currently only support default Django postgres backend.

## Installing
1. Install via `pip` (coming soon):
```python
pip install djangoviews
```
or install by copying `djangoviews` directory into your app.

2. Add to top of `INSTALLED_APPS`:
```python
INSTALLED_APPS = [
    "djangoviews",  # <----
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    ...
]
```
3. Add the database backend to your settings file:
```python
DATABASES = {
    "default": {
        "ENGINE": "djangoviews.db.backends.postgresql",  # <----
        ...
    }
}
```
4. Update your root app `__init__.py` file to allow custom `Meta` class attributes:
```python
# my_app/__init__.py
import django.db.models.options as options  

options.DEFAULT_NAMES += ('materialized', 'base_model',)
```

## Creating a View Model
Define the view model by inheriting the `ViewBaseModel` class and specifying the `base_model` and whether the view should be `materialized`:
```python
class MyModelView(ViewBaseModel):

    class Meta:
        base_model = "my_app.MyModel"
        materialized = False
```

## Defining the View fields
Define each view field using the `BaseViewField` class, and specify the `source` if renaming a field or performing a calculation.The `child` attribute denotes what data type to assign to the field. For example:
```python
    class MyModelView(ViewBaseModel):
        class Meta:
            base_model = "my_app.MyModel"
            materialized = False

        name = BaseViewField(child=models.CharField())
        unique_id = BaseViewField(source="pk",  child=models.IntegerField())
        tags = BaseViewField(
            source=aggregates.StringAgg('tags__name', delimiter="'; '", distinct=True),
            child=models.CharField()
```

## Filtering View Results
Filter the results of a view the same way you would with other ORM objects:
```python
results = MyModelView.objects.filter(unique_id__in=[1,2,3])
```