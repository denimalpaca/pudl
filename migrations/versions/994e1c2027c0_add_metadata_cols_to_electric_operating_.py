"""Add metadata cols to electric_operating_revenues_ferc1.

Revision ID: 994e1c2027c0
Revises: 29d443aadf25
Create Date: 2023-05-08 16:48:29.336530
"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "994e1c2027c0"
down_revision = "29d443aadf25"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table(
        "denorm_electric_operating_revenues_ferc1", schema=None
    ) as batch_op:
        batch_op.add_column(
            sa.Column(
                "ferc_account",
                sa.Text(),
                nullable=True,
                comment="Actual FERC Account number (e.g. '359.1') if available, or a PUDL assigned ID when FERC accounts have been split or combined in reporting.",
            )
        )
        batch_op.add_column(
            sa.Column(
                "row_type_xbrl",
                sa.Enum("calculated_value", "reported_value"),
                nullable=True,
                comment="Indicates whether the value reported in the row is calculated, or uniquely reported within the table.",
            )
        )

    with op.batch_alter_table(
        "electric_operating_revenues_ferc1", schema=None
    ) as batch_op:
        batch_op.add_column(
            sa.Column(
                "ferc_account",
                sa.Text(),
                nullable=True,
                comment="Actual FERC Account number (e.g. '359.1') if available, or a PUDL assigned ID when FERC accounts have been split or combined in reporting.",
            )
        )
        batch_op.add_column(
            sa.Column(
                "row_type_xbrl",
                sa.Enum("calculated_value", "reported_value"),
                nullable=True,
                comment="Indicates whether the value reported in the row is calculated, or uniquely reported within the table.",
            )
        )

    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table(
        "electric_operating_revenues_ferc1", schema=None
    ) as batch_op:
        batch_op.drop_column("row_type_xbrl")
        batch_op.drop_column("ferc_account")

    with op.batch_alter_table(
        "denorm_electric_operating_revenues_ferc1", schema=None
    ) as batch_op:
        batch_op.drop_column("row_type_xbrl")
        batch_op.drop_column("ferc_account")

    # ### end Alembic commands ###
