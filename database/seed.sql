-- ==========================================================================
-- Optional static seed for the channel reference dimension.
-- --------------------------------------------------------------------------
-- The full database is normally loaded from data/processed/ by
-- src/load_database.py (which also loads dim_channel from its CSV). This file
-- documents the small, static channel reference set and lets you seed it
-- manually. It uses INSERT OR IGNORE so it is safe to run more than once.
--
-- channel_id order matches config.ACQUISITION_CHANNELS.
-- ==========================================================================

INSERT OR IGNORE INTO dim_channel (channel_id, channel_name, channel_type) VALUES
    (1, 'Organic Search', 'Organic'),
    (2, 'Paid Search',    'Paid'),
    (3, 'Social Ads',     'Paid'),
    (4, 'Email',          'Owned'),
    (5, 'Referral',       'Referral'),
    (6, 'Direct',         'Direct');
