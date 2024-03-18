# Django Views AF
Adds support for views and materialized views in a django app. Currently only support default Django postgres backend.

## Installing
1. Install via `pip`:
```python
pip install djangoviews_af
```
2. Add to top of `INSTALLED_APPS`:
```python
INSTALLED_APPS = [
    "djangoviews_af",  # <----
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
        "ENGINE": "djangoviews_af.db.backends.postgresql",  # <----
        ...
    }
}
```
4. Update your root app `__init__.py` file to allow custom `Meta` class attributes:
```python
# my_app/__init__.py
import django.db.models.options as options  

options.DEFAULT_NAMES += ('materialized_view', 'view_parent_model',)
```