import os
import logging
from flask import (
    render_template, jsonify, current_app, send_from_directory,
    abort, url_for, flash, get_flashed_messages
)
from flask_login import login_required, current_user # Require login for main views
from . import bp
from app.models import Photo
from app import db # Might be needed for more complex queries

log = logging.getLogger(__name__) # Use app logger

@bp.route('/')
@bp.route('/index')
@login_required # Protect the main view
def index():
    """Displays the main photo timeline."""
    # Fetch photos ordered by timestamp (newest first)
    # Add pagination later for performance
    photos = Photo.query.order_by(Photo.timestamp.desc()).all()

    # Temporary HTML response until templates are added
    photo_html = "<h2>Photo Timeline</h2><ul>"
    if not photos:
        photo_html += "<p>No photos found. Run 'flask scan-library' to scan your library.</p>"
    else:
        for p in photos:
            thumb_url = url_for('main.get_thumbnail', photo_hash=p.file_hash) if p.thumbnail_generated and p.file_hash else '#'
            # Link to original image (implement later if needed)
            # img_link_url = url_for('main.get_image', relative_path=p.relative_path)
            img_tag = f'<img src="{thumb_url}" alt="{p.filename}" loading="lazy" width="200">' if thumb_url != '#' else '[No Thumbnail]'
            photo_html += f'<li>{img_tag} {p.filename} ({p.timestamp})</li>' # Add link later
    photo_html += "</ul>"

    # Add user info and logout link
    user_info = f"<p>Logged in as: {current_user.username} | <a href='{url_for('auth.logout')}'>Logout</a></p>"

    # Display flash messages
    flashes = ""
    messages = get_flashed_messages(with_categories=True)
    if messages:
        flashes = "<div><h3>Messages:</h3><ul>"
        for category, message in messages:
            flashes += f"<li class='flash-{category or 'message'}'>{message}</li>" # Add default category
        flashes += "</ul></div><hr>"

    return flashes + user_info + photo_html


@bp.route('/image/<path:relative_path>')
@login_required
def get_image(relative_path):
    """Serves an original image file."""
    photo_library_path = current_app.config.get('PHOTO_LIBRARY_PATH')
    if not photo_library_path:
        log.error("Photo library path not configured.")
        abort(500)

    # Basic security check: ensure the path is relative and within the library
    safe_path = os.path.normpath(os.path.join(photo_library_path, relative_path))

    # Check if the normalized path is still within the photo library
    # Use realpath to resolve symlinks before checking prefix
    real_library_path = os.path.realpath(photo_library_path)
    real_safe_path = os.path.realpath(safe_path)

    if not real_safe_path.startswith(real_library_path + os.sep) and real_safe_path != real_library_path:
         log.warning(f"Attempted access outside library: {relative_path} resolved to {real_safe_path}")
         abort(404) # Path traversal attempt or invalid path

    # Check if the photo exists in DB (optional, but good for consistency)
    # Normalize path separators in DB query if needed
    normalized_relative_path = relative_path.replace('\\', '/')
    photo = Photo.query.filter_by(relative_path=normalized_relative_path).first()
    if not photo:
        log.warning(f"Image not found in DB: {normalized_relative_path}")
        abort(404)

    # Use send_from_directory for safer file serving
    directory = os.path.dirname(safe_path)
    filename = os.path.basename(safe_path)

    # Final check on directory before sending
    if not os.path.realpath(directory).startswith(real_library_path):
         log.error(f"Directory mismatch after path processing: {directory} vs {real_library_path}")
         abort(404) # Should not happen if previous checks passed

    try:
        log.debug(f"Serving image: directory='{directory}', filename='{filename}'")
        return send_from_directory(directory, filename)
    except FileNotFoundError:
        log.error(f"File not found by send_from_directory: {filename} in {directory}")
        abort(404)


@bp.route('/thumbnail/<string:photo_hash>')
@login_required
def get_thumbnail(photo_hash):
    """Serves a thumbnail image."""
    thumbnail_dir = current_app.config.get('THUMBNAIL_DIR')
    if not thumbnail_dir:
        log.error("Thumbnail directory not configured.")
        abort(500)

    # Construct the expected path based on the hash structure
    hash_prefix = photo_hash[:2]
    hash_suffix = photo_hash[2:4]
    thumb_subdir_name = os.path.join(hash_prefix, hash_suffix) # Relative subdir path
    thumb_filename = f"{photo_hash}.jpg"
    relative_thumb_path = os.path.join(thumb_subdir_name, thumb_filename)

    try:
        log.debug(f"Serving thumbnail: directory='{thumbnail_dir}', path='{relative_thumb_path}'")
        return send_from_directory(thumbnail_dir, relative_thumb_path)
    except FileNotFoundError:
        log.warning(f"Thumbnail not found for hash: {photo_hash} at path {relative_thumb_path}")
        # Optionally, return a placeholder image
        # placeholder_path = os.path.join(current_app.static_folder, 'images')
        # placeholder_file = 'placeholder_thumb.png'
        # if os.path.exists(os.path.join(placeholder_path, placeholder_file)):
        #     return send_from_directory(placeholder_path, placeholder_file)
        abort(404)

# Add route for viewing/editing EXIF later
# @bp.route('/photo/<int:photo_id>/exif', methods=['GET', 'POST'])
# @login_required
# def photo_exif(photo_id):
#     photo = Photo.query.get_or_404(photo_id)
#     # ... logic to display and potentially update EXIF ...
#     return f"EXIF data for {photo.filename}"
