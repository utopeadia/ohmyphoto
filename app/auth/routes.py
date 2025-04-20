from flask import render_template, redirect, url_for, flash, request
from urllib.parse import urlparse, urljoin
from . import bp
from app.models import User
from .forms import LoginForm, RegistrationForm
from flask_login import current_user, login_user, logout_user # login_required can be added later if needed
from app import db

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        # Security check: ensure next_page is a relative path and not an external URL
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('main.index')
        # Additional check to prevent open redirect vulnerability
        elif not urlparse(next_page).path.startswith(url_for('main.index')): # Ensure it's within our app
             next_page = url_for('main.index')

        flash(f'Welcome back, {user.username}!')
        return redirect(next_page)
    # For now, we don't have templates, return JSON or simple message
    # return render_template('auth/login.html', title='Sign In', form=form)
    # Temporary response until templates are added
    if form.errors:
        flash(f"Login failed: {form.errors}")
    return f'''
        <h1>Sign In</h1>
        <form method="post">
            {form.hidden_tag()}
            <p>{form.username.label}<br>{form.username(size=32)}</p>
            <p>{form.password.label}<br>{form.password(size=32)}</p>
            <p>{form.remember_me()} {form.remember_me.label}</p>
            <p>{form.submit()}</p>
        </form>
        <p>New User? <a href="{url_for('auth.register')}">Click to Register!</a></p>
    '''

@bp.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('main.index'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        # We need the database to be created and migrated first for this to work
        try:
            db.session.commit()
            flash('Congratulations, you are now a registered user!')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Registration failed: {e}. Database might need initialization/migration.')
            # Log the error e for debugging
    # For now, we don't have templates, return JSON or simple message
    # return render_template('auth/register.html', title='Register', form=form)
    # Temporary response until templates are added
    if form.errors:
        flash(f"Registration failed: {form.errors}")
    return f'''
        <h1>Register</h1>
        <form method="post">
            {form.hidden_tag()}
            <p>{form.username.label}<br>{form.username(size=32)}</p>
            <p>{form.email.label}<br>{form.email(size=64)}</p>
            <p>{form.password.label}<br>{form.password(size=32)}</p>
            <p>{form.password2.label}<br>{form.password2(size=32)}</p>
            <p>{form.submit()}</p>
        </form>
        <p>Already have an account? <a href="{url_for('auth.login')}">Click to Login!</a></p>
    '''

# Add other auth routes like password reset later
