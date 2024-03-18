from django.db.models import fields
from django.db.models.expressions import Combinable, ExpressionWrapper, F


class BaseViewField(fields.Field):

    def __init__(self, child, source=None, **kwargs):
        super().__init__(**kwargs)
        self.child = child

        if isinstance(source, Combinable) or source is None:
            self.source = source

        elif isinstance(source, str):
            self.source = ExpressionWrapper(F(source), output_field=child)

        else:
            self.source = None

    def deconstruct(self):
        """
        Overriding the deconstruct method to include the custom field attributes in
        migration files while executing `makemigrations` command on the materialized view model.
        """
        name, path, args, keywords = super().deconstruct()

        keywords.update(source=self.source, child=self.child)

        return name, path, args, keywords
