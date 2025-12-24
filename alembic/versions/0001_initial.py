"""initial

Revision ID: 0001_initial
Revises: 
Create Date: 2025-12-23 00:00:00.000000
"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Attempt to create all tables from SQLModel metadata
    bind = op.get_bind()
    try:
        import sys
        from sqlmodel import SQLModel

        # Ensure models are imported so metadata is populated
        try:
            import importlib, pkgutil
            import app.models as models_pkg
            pkg_path = getattr(models_pkg, "__path__", None)
            if pkg_path is not None:
                for finder, name, ispkg in pkgutil.iter_modules(pkg_path):
                    importlib.import_module(f"app.models.{name}")
        except Exception as e:
            print(f"Warning: failed to import app.models: {e}", file=sys.stderr)

        # Debug: print tables present in metadata
        try:
            print("SQLModel.metadata tables:", list(SQLModel.metadata.tables.keys()), file=sys.stderr)
        except Exception:
            pass

        SQLModel.metadata.create_all(bind=bind)
    except Exception:
        # If models cannot be imported, skip.
        pass


def downgrade() -> None:
    bind = op.get_bind()
    try:
        from sqlmodel import SQLModel

        SQLModel.metadata.drop_all(bind=bind)
    except Exception:
        pass
