"""Initial schema for Pharma QMS complaint management."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "complaints",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("complaint_number", sa.String(32), nullable=False),
        sa.Column("source_type", sa.Enum("email", "pdf", "image", "manual", name="sourcetype"), nullable=False),
        sa.Column("customer_name", sa.String(255), nullable=True),
        sa.Column("product_name", sa.String(255), nullable=True),
        sa.Column("batch_lot_number", sa.String(128), nullable=True),
        sa.Column("mfg_date", sa.Date(), nullable=True),
        sa.Column("date_received", sa.Date(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("contact_info", sa.String(512), nullable=True),
        sa.Column(
            "complaint_type",
            sa.Enum(
                "quality_defect", "packaging_labeling", "adverse_event",
                "counterfeit_suspicion", "oos_related", "unclassified",
                name="complainttype",
            ),
            nullable=True,
        ),
        sa.Column("severity", sa.Enum("Critical", "Major", "Minor", name="severity"), nullable=True),
        sa.Column("classification_rationale", sa.Text(), nullable=True),
        sa.Column("regulatory_reportable", sa.Boolean(), nullable=True),
        sa.Column("risk_assessment", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "Draft", "Open/Triaged", "Under Investigation",
                "CAPA In Progress", "Closed", name="complaintstatus",
            ),
            nullable=False,
        ),
        sa.Column("assigned_to", sa.String(128), nullable=True),
        sa.Column("ai_summary", sa.Text(), nullable=True),
        sa.Column("langgraph_state", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("complaint_number"),
    )
    op.create_index("ix_complaints_complaint_number", "complaints", ["complaint_number"])
    op.create_index("ix_complaints_batch_lot_number", "complaints", ["batch_lot_number"])

    op.create_table(
        "complaint_documents",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("complaint_id", sa.Integer(), nullable=True),
        sa.Column("file_path", sa.String(512), nullable=False),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column("extraction_confidence", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["complaint_id"], ["complaints.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "investigations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("complaint_id", sa.Integer(), nullable=False),
        sa.Column("root_cause", sa.Text(), nullable=True),
        sa.Column("root_cause_ai_suggestion", sa.Text(), nullable=True),
        sa.Column("clarifying_questions", sa.Text(), nullable=True),
        sa.Column("investigator_notes", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("pending", "in_progress", "completed", name="investigationstatus"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["complaint_id"], ["complaints.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("complaint_id"),
    )

    op.create_table(
        "capa",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("complaint_id", sa.Integer(), nullable=False),
        sa.Column("corrective_action", sa.Text(), nullable=True),
        sa.Column("preventive_action", sa.Text(), nullable=True),
        sa.Column("ai_suggested", sa.Boolean(), nullable=False),
        sa.Column("effectiveness_check_date", sa.Date(), nullable=True),
        sa.Column("effectiveness_result", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["complaint_id"], ["complaints.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("complaint_id"),
    )

    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("complaint_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(128), nullable=False),
        sa.Column("actor", sa.String(128), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["complaint_id"], ["complaints.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_log_complaint_id", "audit_log", ["complaint_id"])


def downgrade() -> None:
    op.drop_table("audit_log")
    op.drop_table("capa")
    op.drop_table("investigations")
    op.drop_table("complaint_documents")
    op.drop_table("complaints")
