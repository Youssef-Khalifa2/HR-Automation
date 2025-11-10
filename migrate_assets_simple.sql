-- Migration script to simplify assets table
-- This removes individual item tracking and replaces with simple yes/no + notes

-- Step 1: Add new columns
ALTER TABLE assets ADD COLUMN assets_returned BOOLEAN DEFAULT FALSE;
ALTER TABLE assets ADD COLUMN notes TEXT;

-- Step 2: Migrate existing data (optional - convert old data to new format)
-- If approved was true, mark assets as returned
UPDATE assets SET assets_returned = approved WHERE approved IS NOT NULL;

-- Combine old fields into notes
UPDATE assets SET notes =
    CASE
        WHEN laptop = TRUE OR mouse = TRUE OR headphones = TRUE OR others IS NOT NULL THEN
            'Items: ' ||
            CASE WHEN laptop = TRUE THEN 'Laptop, ' ELSE '' END ||
            CASE WHEN mouse = TRUE THEN 'Mouse, ' ELSE '' END ||
            CASE WHEN headphones = TRUE THEN 'Headphones, ' ELSE '' END ||
            COALESCE(others, '')
        ELSE NULL
    END
WHERE laptop IS NOT NULL OR mouse IS NOT NULL OR headphones IS NOT NULL OR others IS NOT NULL;

-- Step 3: Drop old columns
ALTER TABLE assets DROP COLUMN laptop;
ALTER TABLE assets DROP COLUMN mouse;
ALTER TABLE assets DROP COLUMN headphones;
ALTER TABLE assets DROP COLUMN others;
ALTER TABLE assets DROP COLUMN approved;

-- Note: The table now has only:
-- - id, res_id (foreign key to submissions)
-- - assets_returned (boolean)
-- - notes (text)
-- - created_at, updated_at (timestamps)
