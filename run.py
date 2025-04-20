import click
from app import create_app, db # Import db if needed by commands
from app.photolib import scan_photo_library
# Import models if needed by commands
# from app.models import User, Photo

app = create_app()

# --- CLI Commands ---

@app.cli.command("scan-library")
def scan_library_command():
    """Scans the photo library for new images."""
    click.echo("Starting photo library scan...")
    # The scan function uses app context implicitly via current_app
    scan_photo_library()
    click.echo("Photo library scan finished.")

# Add other CLI commands here if needed
# e.g., flask create-user, flask reset-db

# --- Run Server ---

if __name__ == '__main__':
    # Note: Debug mode should be False in production
    # Consider using a production WSGI server like Gunicorn or Waitress
    app.run(debug=True, host='0.0.0.0', port=5000)
