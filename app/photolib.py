import os
import logging
from flask import current_app
import os
import logging
import hashlib
from datetime import datetime
from flask import current_app
from PIL import Image, ExifTags # Import ExifTags for orientation handling
import exifread # For EXIF data
from app import db
from app.models import Photo

# Configure logging if not already configured by Flask/app
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__) # Use app logger if available

SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'} # Pillow might need plugins for HEIC/HEIF
THUMBNAIL_SIZE = (400, 400) # Target thumbnail size (width, height)

# --- Helper Functions ---

def calculate_hash(filepath):
    """Calculates the SHA256 hash of a file."""
    hasher = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            while True:
                chunk = f.read(4096) # Read in chunks
                if not chunk:
                    break
                hasher.update(chunk)
        return hasher.hexdigest()
    except IOError as e:
        log.error(f"Error reading file for hashing {filepath}: {e}")
        return None

def get_exif_data(filepath):
    """Extracts EXIF data using exifread."""
    try:
        with open(filepath, 'rb') as f:
            tags = exifread.process_file(f, stop_tag='JPEGThumbnail') # Don't need thumbnail data here
            return tags
    except Exception as e:
        log.warning(f"Could not read EXIF data for {filepath}: {e}")
        return {}

def get_timestamp_from_exif(exif_data):
    """Attempts to get the creation timestamp from EXIF data."""
    # Try different EXIF tags for date/time
    date_tags = ['EXIF DateTimeOriginal', 'Image DateTime', 'EXIF DateTimeDigitized']
    for tag in date_tags:
        if tag in exif_data:
            try:
                # EXIF format is typically 'YYYY:MM:DD HH:MM:SS'
                return datetime.strptime(str(exif_data[tag]), '%Y:%m:%d %H:%M:%S')
            except (ValueError, TypeError) as e:
                log.warning(f"Could not parse timestamp from EXIF tag '{tag}' ({exif_data[tag]}): {e}")
    return None

def generate_thumbnail(source_path, photo_hash):
    """Generates a thumbnail for the image and saves it."""
    thumbnail_dir = current_app.config['THUMBNAIL_DIR']
    # Use hash to create a unique filename, potentially nested
    # Example: /path/to/thumbnails/ab/cd/abcdef123...jpg
    hash_prefix = photo_hash[:2]
    hash_suffix = photo_hash[2:4]
    thumb_subdir = os.path.join(thumbnail_dir, hash_prefix, hash_suffix)
    os.makedirs(thumb_subdir, exist_ok=True)
    thumb_filename = f"{photo_hash}.jpg" # Always save thumbs as JPG?
    thumb_path = os.path.join(thumb_subdir, thumb_filename)

    if os.path.exists(thumb_path):
        # log.debug(f"Thumbnail already exists for {photo_hash}")
        return True # Assume success if it exists

    try:
        with Image.open(source_path) as img:
            # Handle image orientation based on EXIF data
            try:
                for orientation in ExifTags.TAGS.keys():
                    if ExifTags.TAGS[orientation] == 'Orientation':
                        break
                exif = dict(img._getexif().items())

                if exif[orientation] == 3:
                    img = img.rotate(180, expand=True)
                elif exif[orientation] == 6:
                    img = img.rotate(270, expand=True)
                elif exif[orientation] == 8:
                    img = img.rotate(90, expand=True)
            except (AttributeError, KeyError, IndexError):
                # Cases: image doesn't have getexif or orientation tag
                pass

            img.thumbnail(THUMBNAIL_SIZE)
            # Ensure conversion to RGB before saving as JPEG
            if img.mode in ("RGBA", "P"):
                 img = img.convert("RGB")
            img.save(thumb_path, "JPEG", quality=85) # Save with reasonable quality
            log.info(f"Generated thumbnail for {photo_hash} at {thumb_path}")
            return True
    except Exception as e:
        log.error(f"Failed to generate thumbnail for {source_path} (hash: {photo_hash}): {e}")
        # Clean up potentially corrupted file?
        if os.path.exists(thumb_path):
            try:
                os.remove(thumb_path)
            except OSError:
                pass
        return False

# --- Main Scanning Function ---

def scan_photo_library():
    """
    Scans the photo library directory, extracts metadata, generates thumbnails,
    and adds new photos to the database.
    """
    # Ensure paths are configured
    photo_library_path = current_app.config.get('PHOTO_LIBRARY_PATH')
    data_storage_path = current_app.config.get('DATA_STORAGE_PATH')
    thumbnail_dir = current_app.config.get('THUMBNAIL_DIR')

    if not photo_library_path or not data_storage_path or not thumbnail_dir:
        log.error("Storage paths (PHOTO_LIBRARY_PATH, DATA_STORAGE_PATH, THUMBNAIL_DIR) must be configured.")
        return

    # Ensure directories exist
    if not os.path.isdir(photo_library_path):
        log.warning(f"Photo library path does not exist: {photo_library_path}. Creating it.")
        try:
            os.makedirs(photo_library_path, exist_ok=True)
        except OSError as e:
            log.error(f"Failed to create photo library path {photo_library_path}: {e}")
            return # Cannot proceed without the library path
    os.makedirs(data_storage_path, exist_ok=True)
    # thumbnail_dir base path is checked/created by generate_thumbnail's subdir creation logic
    # os.makedirs(thumbnail_dir, exist_ok=True)

    log.info(f"Starting scan of photo library: {photo_library_path}")
    added_count = 0
    updated_count = 0 # Count photos whose metadata might be updated
    skipped_count = 0
    error_count = 0
    commit_batch_size = 100 # Commit after processing this many new photos

    # Get existing photos (hash and path) for checking
    # Consider fetching in batches if the DB is very large
    existing_photos = {p.relative_path: p.file_hash for p in Photo.query.with_entities(Photo.relative_path, Photo.file_hash).all()}
    log.info(f"Found {len(existing_photos)} existing photos in database.")

    processed_in_batch = 0
    for root, _, files in os.walk(photo_library_path):
        for filename in files:
            file_ext = os.path.splitext(filename)[1].lower()
            if file_ext not in SUPPORTED_EXTENSIONS:
                continue # Skip unsupported files

            full_path = os.path.join(root, filename)
            relative_path = os.path.relpath(full_path, photo_library_path).replace('\\', '/')

            try:
                # 1. Calculate file hash
                current_hash = calculate_hash(full_path)
                if not current_hash:
                    error_count += 1
                    continue # Skip if hashing failed

                # 2. Check if photo exists and if hash matches
                existing_hash = existing_photos.get(relative_path)
                if existing_hash:
                    if existing_hash == current_hash:
                        # log.debug(f"Skipping unchanged photo: {relative_path}")
                        skipped_count += 1
                        continue
                    else:
                        log.warning(f"File changed, updating metadata for: {relative_path}")
                        # Find the existing Photo object to update
                        photo = Photo.query.filter_by(relative_path=relative_path).first()
                        if not photo: # Should not happen if existing_hash was found, but check anyway
                           log.error(f"Consistency error: Hash found for {relative_path} but no DB record.")
                           error_count += 1
                           continue
                        is_update = True
                        updated_count += 1
                else:
                    log.info(f"Found new photo: {relative_path}")
                    # Check if hash already exists (duplicate file elsewhere?)
                    # duplicate = Photo.query.filter_by(file_hash=current_hash).first()
                    # if duplicate:
                    #     log.warning(f"Duplicate hash found for {relative_path} (matches {duplicate.relative_path}). Skipping add.")
                    #     skipped_count += 1
                    #     continue # Or link it somehow? For now, skip.
                    photo = Photo(relative_path=relative_path)
                    is_update = False
                    added_count += 1

                # 3. Extract Metadata
                filesize = os.path.getsize(full_path)
                width, height = None, None
                timestamp = None
                exif_text = ""

                try:
                    with Image.open(full_path) as img:
                        width, height = img.size
                        # Try getting EXIF via Pillow first (might be faster/simpler for basic tags)
                        exif_pillow = img.getexif()
                        exif_data_dict = {ExifTags.TAGS[k]: v for k, v in exif_pillow.items() if k in ExifTags.TAGS}
                        exif_text = str(exif_data_dict) # Simple string representation for now
                        # Try getting timestamp from Pillow's EXIF interpretation
                        # Example: timestamp = exif_data_dict.get('DateTimeOriginal') or exif_data_dict.get('DateTime')
                        # If not found, fall back to exifread
                except Exception as img_err:
                     log.warning(f"Could not get dimensions/basic EXIF for {relative_path} via Pillow: {img_err}")

                # Use exifread for more robust EXIF parsing, especially timestamp
                exif_data_exifread = get_exif_data(full_path)
                if exif_data_exifread:
                    timestamp = get_timestamp_from_exif(exif_data_exifread)
                    # Optionally merge/override exif_text
                    # exif_text = str(exif_data_exifread) # Or a more structured format

                # Fallback timestamp to file modification time if EXIF fails
                if not timestamp:
                    try:
                        mtime = os.path.getmtime(full_path)
                        timestamp = datetime.fromtimestamp(mtime)
                        log.debug(f"Using file modification time for {relative_path}")
                    except Exception as time_err:
                        log.warning(f"Could not get file modification time for {relative_path}: {time_err}")
                        timestamp = datetime.utcnow() # Fallback to now

                # 4. Update Photo Object
                photo.filename = filename
                photo.file_hash = current_hash
                photo.timestamp = timestamp
                photo.width = width
                photo.height = height
                photo.filesize = filesize
                photo.exif_data = exif_text # Store extracted EXIF
                photo.thumbnail_generated = False # Reset on update, regenerate below

                # 5. Generate Thumbnail
                thumb_success = generate_thumbnail(full_path, current_hash)
                if thumb_success:
                    photo.thumbnail_generated = True

                # 6. Add to session if new
                if not is_update:
                    db.session.add(photo)
                    processed_in_batch += 1

                # 7. Commit periodically
                if processed_in_batch >= commit_batch_size:
                    try:
                        db.session.commit()
                        log.info(f"Committed batch of {processed_in_batch} photos.")
                        processed_in_batch = 0 # Reset batch counter
                    except Exception as commit_err:
                        log.error(f"Batch commit failed: {commit_err}")
                        db.session.rollback()
                        # Potentially stop the scan or handle differently
                        error_count += processed_in_batch # Count these as errors for now
                        processed_in_batch = 0

            except Exception as e:
                log.error(f"Error processing file {relative_path}: {e}", exc_info=True) # Log traceback
                error_count += 1
                db.session.rollback() # Rollback potential partial add/update

    # Final commit for any remaining items in the last batch
    try:
        if processed_in_batch > 0:
            db.session.commit()
            log.info(f"Committed final batch of {processed_in_batch} photos.")
    except Exception as e:
        log.error(f"Final commit failed: {e}")
        db.session.rollback()
        error_count += processed_in_batch

    log.info(f"Scan complete. Added: {added_count}, Updated: {updated_count}, Skipped (Unchanged): {skipped_count}, Errors: {error_count}")
