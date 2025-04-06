"""Initial migration

Revision ID: 20240315_0001
Revises: 
Create Date: 2024-03-15 00:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20240315_0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types
    op.execute("CREATE TYPE auctionstatus AS ENUM ('active', 'ended', 'cancelled', 'sold')")
    op.execute("CREATE TYPE auctionsource AS ENUM ('ebay', 'local', 'other')")
    op.execute("CREATE TYPE productcondition AS ENUM ('new', 'like_new', 'very_good', 'good', 'acceptable', 'for_parts')")
    op.execute("CREATE TYPE listingstatus AS ENUM ('draft', 'active', 'ended', 'sold', 'cancelled')")
    op.execute("CREATE TYPE listingplatform AS ENUM ('ebay', 'amazon', 'other')")
    op.execute("CREATE TYPE modeltype AS ENUM ('price_prediction', 'profit_analysis', 'listing_optimization', 'search_ranking')")
    op.execute("CREATE TYPE modelstatus AS ENUM ('training', 'active', 'deprecated', 'failed')")

    # Create auction table
    op.create_table(
        'auction',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(length=1000), nullable=True),
        sa.Column('source', postgresql.ENUM('ebay', 'local', 'other', name='auctionsource'), nullable=False),
        sa.Column('source_id', sa.String(length=100), nullable=False),
        sa.Column('url', sa.String(length=500), nullable=False),
        sa.Column('status', postgresql.ENUM('active', 'ended', 'cancelled', 'sold', name='auctionstatus'), nullable=False),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('current_price', sa.Float(), nullable=False),
        sa.Column('starting_price', sa.Float(), nullable=False),
        sa.Column('buy_now_price', sa.Float(), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('condition', sa.String(length=50), nullable=False),
        sa.Column('brand', sa.String(length=100), nullable=True),
        sa.Column('model', sa.String(length=100), nullable=True),
        sa.Column('location', sa.String(length=200), nullable=True),
        sa.Column('seller_rating', sa.Float(), nullable=True),
        sa.Column('num_bids', sa.Integer(), nullable=False, default=0),
        sa.Column('shipping_info', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('raw_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('source', 'source_id', name='uq_auction_source_id')
    )

    # Create auction_image table
    op.create_table(
        'auctionimage',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('auction_id', sa.Integer(), nullable=False),
        sa.Column('url', sa.String(length=500), nullable=False),
        sa.Column('order', sa.Integer(), nullable=False),
        sa.Column('is_primary', sa.Boolean(), nullable=False, default=False),
        sa.ForeignKeyConstraint(['auction_id'], ['auction.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create auction_bid table
    op.create_table(
        'auctionbid',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('auction_id', sa.Integer(), nullable=False),
        sa.Column('bidder_id', sa.String(length=100), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('bid_time', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['auction_id'], ['auction.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create product table
    op.create_table(
        'product',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('condition', postgresql.ENUM('new', 'like_new', 'very_good', 'good', 'acceptable', 'for_parts', name='productcondition'), nullable=False),
        sa.Column('brand', sa.String(length=100), nullable=True),
        sa.Column('model', sa.String(length=100), nullable=True),
        sa.Column('sku', sa.String(length=100), nullable=True),
        sa.Column('upc', sa.String(length=50), nullable=True),
        sa.Column('features', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('specifications', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('dimensions', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('weight', sa.Float(), nullable=True),
        sa.Column('current_market_price', sa.Float(), nullable=True),
        sa.Column('lowest_market_price', sa.Float(), nullable=True),
        sa.Column('highest_market_price', sa.Float(), nullable=True),
        sa.Column('average_market_price', sa.Float(), nullable=True),
        sa.Column('price_history', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create product_image table
    op.create_table(
        'productimage',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('url', sa.String(length=500), nullable=False),
        sa.Column('order', sa.Integer(), nullable=False),
        sa.Column('is_primary', sa.Boolean(), nullable=False, default=False),
        sa.ForeignKeyConstraint(['product_id'], ['product.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create market_data table
    op.create_table(
        'marketdata',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('source', sa.String(length=50), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('condition', postgresql.ENUM('new', 'like_new', 'very_good', 'good', 'acceptable', 'for_parts', name='productcondition'), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('url', sa.String(length=500), nullable=True),
        sa.Column('seller_rating', sa.Float(), nullable=True),
        sa.Column('shipping_cost', sa.Float(), nullable=True),
        sa.Column('raw_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['product.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create listing table
    op.create_table(
        'listing',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('platform', postgresql.ENUM('ebay', 'amazon', 'other', name='listingplatform'), nullable=False),
        sa.Column('status', postgresql.ENUM('draft', 'active', 'ended', 'sold', 'cancelled', name='listingstatus'), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('condition', sa.String(length=50), nullable=False),
        sa.Column('brand', sa.String(length=100), nullable=True),
        sa.Column('model', sa.String(length=100), nullable=True),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('shipping_cost', sa.Float(), nullable=True),
        sa.Column('tax_rate', sa.Float(), nullable=True),
        sa.Column('promotion_discount', sa.Float(), nullable=True),
        sa.Column('duration', sa.Integer(), nullable=False),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('auto_relist', sa.Boolean(), nullable=False, default=False),
        sa.Column('auto_price_adjust', sa.Boolean(), nullable=False, default=False),
        sa.Column('keywords', postgresql.JSON(astext_type=sa.Text()), nullable=False, default=list),
        sa.Column('seo_score', sa.Float(), nullable=True),
        sa.Column('policy_compliance', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('platform_listing_id', sa.String(length=100), nullable=True),
        sa.Column('platform_url', sa.String(length=500), nullable=True),
        sa.Column('platform_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['product.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create listing_image table
    op.create_table(
        'listingimage',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('listing_id', sa.Integer(), nullable=False),
        sa.Column('url', sa.String(length=500), nullable=False),
        sa.Column('order', sa.Integer(), nullable=False),
        sa.Column('is_primary', sa.Boolean(), nullable=False, default=False),
        sa.ForeignKeyConstraint(['listing_id'], ['listing.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create listing_analytics table
    op.create_table(
        'listinganalytics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('listing_id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('views', sa.Integer(), nullable=False, default=0),
        sa.Column('watchers', sa.Integer(), nullable=False, default=0),
        sa.Column('impressions', sa.Integer(), nullable=False, default=0),
        sa.Column('clicks', sa.Integer(), nullable=False, default=0),
        sa.Column('conversion_rate', sa.Float(), nullable=True),
        sa.Column('search_rank', sa.Integer(), nullable=True),
        sa.Column('search_terms', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['listing_id'], ['listing.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create ml_model table
    op.create_table(
        'mlmodel',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('type', postgresql.ENUM('price_prediction', 'profit_analysis', 'listing_optimization', 'search_ranking', name='modeltype'), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=False),
        sa.Column('status', postgresql.ENUM('training', 'active', 'deprecated', 'failed', name='modelstatus'), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('parameters', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('features', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('hyperparameters', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('accuracy', sa.Float(), nullable=True),
        sa.Column('precision', sa.Float(), nullable=True),
        sa.Column('recall', sa.Float(), nullable=True),
        sa.Column('f1_score', sa.Float(), nullable=True),
        sa.Column('mse', sa.Float(), nullable=True),
        sa.Column('mae', sa.Float(), nullable=True),
        sa.Column('training_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('training_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('training_samples', sa.Integer(), nullable=True),
        sa.Column('validation_samples', sa.Integer(), nullable=True),
        sa.Column('model_path', sa.String(length=500), nullable=False),
        sa.Column('scaler_path', sa.String(length=500), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create training_data table
    op.create_table(
        'trainingdata',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('model_id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('features', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('target', sa.Float(), nullable=False),
        sa.Column('weight', sa.Float(), nullable=True, default=1.0),
        sa.Column('source', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['model_id'], ['mlmodel.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create model_prediction table
    op.create_table(
        'modelprediction',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('model_id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('features', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('prediction', sa.Float(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('actual_value', sa.Float(), nullable=True),
        sa.Column('error', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['model_id'], ['mlmodel.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    # Drop tables
    op.drop_table('modelprediction')
    op.drop_table('trainingdata')
    op.drop_table('mlmodel')
    op.drop_table('listinganalytics')
    op.drop_table('listingimage')
    op.drop_table('listing')
    op.drop_table('marketdata')
    op.drop_table('productimage')
    op.drop_table('product')
    op.drop_table('auctionbid')
    op.drop_table('auctionimage')
    op.drop_table('auction')

    # Drop enum types
    op.execute('DROP TYPE modelstatus')
    op.execute('DROP TYPE modeltype')
    op.execute('DROP TYPE listingplatform')
    op.execute('DROP TYPE listingstatus')
    op.execute('DROP TYPE productcondition')
    op.execute('DROP TYPE auctionsource')
    op.execute('DROP TYPE auctionstatus') 