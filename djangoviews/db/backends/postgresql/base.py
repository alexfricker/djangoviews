from django.apps import apps
from django.db.backends.postgresql import base
from django.db.models import QuerySet, options, Model

from djangoviews.fields import BaseViewField


class DatabaseSchemaEditor(base.DatabaseSchemaEditor):
    sql_create_materialized_view = (
        "CREATE MATERIALIZED VIEW %(table)s AS %(definition)s"
    )
    sql_delete_materialized_view = "DROP MATERIALIZED VIEW %(table)s"
    sql_refresh_materialized_View = (
        "REFRESH MATERIALIZED VIEW %(concurrently)s %(view)s"
    )
    sql_create_view = "CREATE VIEW %(table)s AS %(definition)s"
    sql_delete_view = "DROP VIEW %(table)s"

    @staticmethod
    def model_meta(model: type[Model]) -> options.Options:
        return model._meta

    def _get_parent_model(self, model: type[Model]):
        """
        Returns the underlying view model that will be used to generate materialized view's SQL.
        """
        parent_model = getattr(self.model_meta(model), "base_model", None)

        if parent_model:
            return apps.get_model(*parent_model.split("."))

    def model_is_materialized_view(self, model: type[Model]) -> bool:
        """Checks if the model class is a materialized view model or a regular django model."""
        return getattr(self.model_meta(model), "materialized", False)

    def model_is_view(self, model: type[Model]) -> bool:
        """Checks if the model class is a view model or a regular django model."""
        return hasattr(self.model_meta(model), "materialized")

    def get_queryset(self, model: Model, extra_field=None):
        """Generates the queryset out of the provided parent model and the provided fields."""

        def append_field(_model_field):

            if _model_field.source is None:
                concrete_fields.append(_model_field.name)
            else:
                annotation_fields.update({_model_field.attname: _model_field.source})

        concrete_fields = []
        annotation_fields = dict()

        for field_name, field in model.__dict__.items():
            if hasattr(field, "field"):
                model_field: BaseViewField = field.field

                if isinstance(model_field, BaseViewField):
                    append_field(model_field)

        if extra_field:
            append_field(extra_field)

        return (
            QuerySet(model=self._get_parent_model(model))
            .only(*concrete_fields)
            .annotate(**annotation_fields)
            .query
        )

    def create_materialized_view(self, model, extra_field=None):
        sql = self.sql_create_materialized_view % {
            "table": self.quote_name(self.model_meta(model).db_table),
            "definition": self.get_queryset(model, extra_field=extra_field),
        }
        self.execute(sql)

    def create_view(self, model, extra_field=None):
        sql = self.sql_create_view % {
            "table": self.quote_name(self.model_meta(model).db_table),
            "definition": self.get_queryset(model, extra_field=extra_field),
        }
        self.execute(sql)

    def create_model(self, model, extra_field=None):
        if self.model_is_materialized_view(model):
            self.create_materialized_view(model, extra_field)
        elif self.model_is_view(model):
            self.create_view(model, extra_field)
        else:
            super().create_model(model)

    def add_field(self, model: Model, field):

        if self.model_is_materialized_view(model) or self.model_is_view(model):
            setattr(model, field.attname, field)
            self.delete_model(model)
            self.create_model(model, extra_field=field)

        else:
            super().add_field(model, field)

    def remove_field(self, model, field):

        if self.model_is_materialized_view(model) or self.model_is_view(model):
            delattr(model, field.attname)
            self.delete_model(model)
            self.create_model(model)
        else:
            super().remove_field(model, field)

    def alter_field(self, model, old_field, new_field, strict=False):

        if self.model_is_materialized_view(model) or self.model_is_view(model):
            delattr(model, old_field.attname)
            self.delete_model(model)
            self.create_model(model, extra_field=new_field)

        else:
            super().alter_field(model, old_field, new_field, strict)

    def delete_materialized_view(self, model):
        self.execute(
            self.sql_delete_materialized_view
            % {"table": self.model_meta(model).db_table}
        )

    def delete_view(self, model):
        self.execute(self.sql_delete_view % {"table": self.model_meta(model).db_table})

    def delete_model(self, model):
        if self.model_is_materialized_view(model):
            self.delete_materialized_view(model)
        elif self.model_is_view:
            self.delete_view(model)
        else:
            super().delete_model(model)

    def refresh_materialized_view(self, model: type[Model], concurrent=False):
        """
        Performs materialized view refresh query if it was desired to
        populate the view data on demand.
        """
        if self.model_is_materialized_view(model):
            self.execute(
                self.sql_refresh_materialized_View
                % {
                    "view": model._meta.db_table,
                    "concurrently": "CONCURRENTLY" if concurrent else "",
                }
            )


class DatabaseWrapper(base.DatabaseWrapper):
    SchemaEditorClass = DatabaseSchemaEditor
