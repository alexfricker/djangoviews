from django.apps import apps
from django.db import connection
from django.db.models import Model
from django.core.checks import Error


class ViewBaseModel(Model):
    """
    ## ViewBaseModel
    The `ViewBaseModel` represents a database view and is defined as a collection
    of fields and annotations from a base `model` class. This allows access, filtering, etc
    view data via the normal Django ORM framework. Schema changes are also managed via
    the `manage.py migrations` and `manage.py migrate` commands.
    ---

    ### `Meta` class
    The `Meta` subclass defines the base model upon which the query is built and specifies
    whether the view should be materialized:

    ```
    class MyDbView(ViewBaseModel):
        class Meta:
            model = MyAppModel
            materialized = True  # or False - must be specified
    ```

    ### Base model
    The base model (`ViewBaseModel.Meta.model`) is the lowest-grain model available on the view and is the starting point
    for generating the view SQL. The view can select fields from this base model, it's related
    models that are not 1:n (TODO: actually test this), or an aggregate across 1:n relations:

    ```
    class MyDbView(ViewBaseModel):
        class Meta:
            model = MyAppModel
            materialized = False

        name = BaseViewField(child=models.CharField())
        unique_id = BaseViewField(source="pk", child=models.IntegerField())
        tags = BaseViewField(
            source=aggregates.StringAgg('tags__name', delimiter="'; '", distinct=True),
            child=models.CharField()
        )
    )
    ```
    """

    class Meta:
        abstract = True

    @classmethod
    def check(cls, **kwargs):
        errors = super().check(**kwargs)

        if not hasattr(cls._meta, "materialized"):
            errors.append(
                Error(
                    "The `materialized` attribute is required in view meta class.",
                    obj=cls,
                    id="models.E100",
                )
            )

        view_parent_model = getattr(cls._meta, "base_model", None)

        if view_parent_model:
            try:
                apps.get_model(*getattr(cls._meta, "base_model").split("."))
            except (LookupError, ValueError) as e:
                errors.append(
                    Error(
                        f"Invalid `base_model` format, {e}",
                        obj=cls,
                        id="models.E101",
                    )
                )
        else:
            errors.append(
                Error(
                    "The `base_model` attribute is required in materialized view meta class.",
                    obj=cls,
                    id="models.E101",
                )
            )

        return errors

    @classmethod
    def refresh(cls, concurrent=False):
        if getattr(cls._meta, "materialized", False) is True:
            with connection.cursor() as cursor:
                editor = cursor.db.schema_editor()
                editor.refresh_materialized_view(cls, concurrent=concurrent)
