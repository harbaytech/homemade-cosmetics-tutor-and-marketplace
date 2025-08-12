from app import app
from flask import render_template, redirect, url_for, flash, request, g
from flask_login import login_required, current_user, logout_user, login_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from app import db
from app.model import  User, Product, Tutorial, Comment, Order, Notification
from .forms import RegistrationForm, ProductForm, TutorialForm, LoginForm
from flask import abort




@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if the email or username already exists
        existing_user = User.query.filter((User.email == form.email.data) | (User.username == form.username.data)).first()
        if existing_user:
            flash('Username or email already exists. Please choose a different one.', 'danger')
            return redirect(url_for('register'))

        # Create a new user
        hashed_password = generate_password_hash(form.password.data)
        new_user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=hashed_password,
            role='learner'  # Default role
        )
        db.session.add(new_user)
        db.session.commit()

        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # Check if the user exists
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            # Log in the user
            login_user(user)
            flash('You have successfully logged in!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')
    return render_template('login.html', form=form)
from werkzeug.utils import secure_filename
import os

@app.route('/upload-product', methods=['GET', 'POST'])
@login_required
def upload_product():
    form = ProductForm()
    if form.validate_on_submit():
        image_file = form.image.data
        if image_file:
            # Save to root/static/images, not app/static/images
            # Get the absolute path to the project root
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            root_static = os.path.join(project_root, 'static', 'images')
            if not os.path.exists(root_static):
                os.makedirs(root_static)

            filename = secure_filename(image_file.filename)
            image_path = os.path.join(root_static, filename)
            image_file.save(image_path)

            new_product = Product(
                name=form.name.data,
                description=form.description.data,
                image_filename=filename,
                whatsapp_link=form.whatsapp_link.data,
                user_id=current_user.id
            )
            db.session.add(new_product)
            db.session.commit()
            # Notify admin (if not uploader)
            if not current_user.is_admin:
                from app.model import User, Notification
                admin = User.query.filter_by(is_admin=True).first()
                if admin:
                    notif = Notification(
                        user_id=admin.id,
                        message=f"{current_user.username} uploaded a new product: '{form.name.data}'."
                    )
                    db.session.add(notif)
                    db.session.commit()
            flash("Product uploaded successfully!", "success")
            return redirect(url_for('view_products'))
    return render_template('upload_product.html', form=form)


@app.route('/upload-tutorial', methods=['GET', 'POST'])
@login_required
def upload_tutorial():
    # Ensure only facilitators and admins can access this route
    if not (current_user.is_admin or current_user.role == 'facilitator'):
        flash('You do not have permission to upload tutorials.', 'danger')
        return redirect(url_for('dashboard'))

    form = TutorialForm()
    if request.method == 'POST':
        filename = None
        youtube_link = form.youtube_link.data.strip() if form.youtube_link.data else None
        pdf_file = request.files.get('file')
        video_file = request.files.get('video_file')
        allowed_video_exts = {'mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv', 'webm'}
        allowed_pdf_ext = 'pdf'
        # Enforce only one of PDF, video, or YouTube link
        pdf_uploaded = pdf_file and pdf_file.filename != ''
        video_uploaded = video_file and video_file.filename != ''
        link_provided = bool(youtube_link)
        if sum([bool(pdf_uploaded), bool(video_uploaded), bool(link_provided)]) != 1:
            flash('Please upload only one: a PDF file, a video file, or provide a YouTube link.', 'danger')
            return render_template('upload_tutorial.html', form=form)
        if pdf_uploaded:
            ext = pdf_file.filename.rsplit('.', 1)[-1].lower()
            if ext != allowed_pdf_ext:
                flash('Invalid file type. Please upload a PDF file.', 'danger')
                return render_template('upload_tutorial.html', form=form)
            filename = secure_filename(pdf_file.filename)
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            root_tutorials = os.path.join(project_root, 'static', 'tutorials')
            if not os.path.exists(root_tutorials):
                os.makedirs(root_tutorials)
            file_path = os.path.join(root_tutorials, filename)
            pdf_file.save(file_path)
        elif video_uploaded:
            ext = video_file.filename.rsplit('.', 1)[-1].lower()
            if ext not in allowed_video_exts:
                flash('Invalid file type. Please upload a supported video file (mp4, avi, mov, wmv, flv, mkv, webm).', 'danger')
                return render_template('upload_tutorial.html', form=form)
            filename = secure_filename(video_file.filename)
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            root_tutorials = os.path.join(project_root, 'static', 'tutorials')
            if not os.path.exists(root_tutorials):
                os.makedirs(root_tutorials)
            file_path = os.path.join(root_tutorials, filename)
            video_file.save(file_path)
        # Create a new tutorial
        new_tutorial = Tutorial(
            title=form.title.data,
            category=form.category.data,
            description=form.description.data,
            file_path=filename if (pdf_uploaded or video_uploaded) else None,
            youtube_link=youtube_link if link_provided else None,
            uploaded_by=current_user.id
        )
        db.session.add(new_tutorial)
        db.session.commit()
        # Notify admin (if not uploader)
        if not current_user.is_admin:
            from app.model import User, Notification
            admin = User.query.filter_by(is_admin=True).first()
            if admin:
                notif = Notification(
                    user_id=admin.id,
                    message=f"{current_user.username} uploaded a new tutorial: '{form.title.data}'."
                )
                db.session.add(notif)
                db.session.commit()
        flash('Your tutorial has been uploaded successfully!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('upload_tutorial.html', form=form)
@app.route('/add-comment/<int:tutorial_id>', methods=['POST'])
@login_required
def add_comment(tutorial_id):
    comment_text = request.form.get('comment')
    if not comment_text:
        flash('Comment cannot be empty.', 'danger')
        return redirect(url_for('tutorials'))

    # Create a new comment
    new_comment = Comment(
        text=comment_text,
        tutorial_id=tutorial_id,
        user_id=current_user.id
    )
    db.session.add(new_comment)
    db.session.commit()
    # Notify tutorial uploader
    tutorial = Tutorial.query.get(tutorial_id)
    if tutorial and tutorial.uploaded_by != current_user.id:
        from app.model import Notification
        notif = Notification(
            user_id=tutorial.uploaded_by,
            message=f"{current_user.username} commented on your tutorial '{tutorial.title}'."
        )
        db.session.add(notif)
        db.session.commit()
    flash('Comment added successfully!', 'success')
    return redirect(url_for('tutorials', tutorial_id=tutorial_id))

@app.route('/add-reply/<int:comment_id>', methods=['POST'])
@login_required
def add_reply(comment_id):
    reply_text = request.form.get('reply')
    if not reply_text:
        flash('Reply cannot be empty.', 'danger')
        return redirect(url_for('tutorials'))

    # Fetch the parent comment
    parent_comment = Comment.query.get_or_404(comment_id)

    # Create a new reply
    new_reply = Comment(
        text=reply_text,
        tutorial_id=parent_comment.tutorial_id,  # Use the tutorial_id from the parent comment
        user_id=current_user.id,
        parent_id=parent_comment.id  # Set the parent_id to the parent comment's ID
    )
    db.session.add(new_reply)
    db.session.commit()
    # Notify parent comment owner
    if parent_comment.user_id != current_user.id:
        from app.model import Notification, Tutorial, User
        tutorial = Tutorial.query.get(parent_comment.tutorial_id)
        poster = User.query.get(tutorial.uploaded_by) if tutorial else None
        poster_name = poster.username if poster else "Unknown"
        notif = Notification(
            user_id=parent_comment.user_id,
            message=f"{current_user.username} replied to your comment on tutorial posted by {poster_name}.",
            comment_id=new_reply.id,
            is_read=False
        )
        db.session.add(notif)
        db.session.commit()
    flash('Reply added successfully!', 'success')
    return redirect(url_for('tutorials', tutorial_id=parent_comment.tutorial_id))  
# ...existing code...

# Notifications route
@app.route('/notifications')
@login_required
def notifications():
    from app.model import Notification, Comment
    notifs = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.timestamp.desc()).all()
    # Build a dict of comment_id -> comment for fast lookup
    comment_ids = [n.comment_id for n in notifs if n.comment_id]
    comments = Comment.query.filter(Comment.id.in_(comment_ids)).all() if comment_ids else []
    comments_dict = {c.id: c for c in comments}
    return render_template('notifications.html', notifications=notifs, comments_dict=comments_dict)

@app.route('/dashboard')
@login_required
def dashboard():
    # Fetch user-specific content (e.g., products and tutorials uploaded by the user)
    user_products = Product.query.filter_by(user_id=current_user.id).all()
    user_tutorials = Tutorial.query.filter_by(uploaded_by=current_user.id).all()

    return render_template('dashboard.html', user=current_user, products=user_products, tutorials=user_tutorials)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))

@app.route('/tutorials', methods=['GET'])
def tutorials():
    category = request.args.get('category', None)
    if category:
        tutorials = Tutorial.query.filter_by(category=category).all()
    else:
        tutorials = Tutorial.query.all()
    return render_template('tutorial.html', tutorials=tutorials)

@app.route('/tutorial/<int:tutorial_id>', methods=['GET', 'POST'])
def tutorial_detail(tutorial_id):
    tutorial = Tutorial.query.get_or_404(tutorial_id)  # Fetch the tutorial by ID
    comments = Comment.query.filter_by(tutorial_id=tutorial_id).all()  # Fetch comments for the tutorial

    if request.method == 'POST':
        # Handle adding a comment
        comment_text = request.form.get('comment')
        if not comment_text:
            flash('Comment cannot be empty.', 'danger')
        else:
            new_comment = Comment(
                text=comment_text,
                tutorial_id=tutorial_id,
                user_id=current_user.id
            )
            db.session.add(new_comment)
            db.session.commit()
            flash('Comment added successfully!', 'success')
        return redirect(url_for('tutorial_detail', tutorial_id=tutorial_id))

    return render_template('tutorial_detail.html', tutorial=tutorial, comments=comments)

@app.route('/products', methods=['GET'])
def view_products():
    all_products = Product.query.all()
    for product in all_products:
        print("Product Image Filename:", product.image_filename)  # Debugging
    print("Products:", all_products)
    return render_template('product.html', products=all_products)


@app.route('/test-static')
def test_static():
    return '<img src="/static/images/test.jpg>'

@app.route('/admin-dashboard', methods=['GET', 'POST'])
@login_required
def admin_dashboard():
    print("Current User Admin Status:", current_user.is_admin)  # Debugging
    # Ensure only admin users can access this route
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('home'))

    # Fetch all tutorials and products
    tutorials = Tutorial.query.all()
    products = Product.query.all()

    return render_template('admin_dashboard.html', tutorials=tutorials, products=products)

@app.route('/delete-tutorial/<int:tutorial_id>', methods=['POST'])
@login_required
def delete_tutorial(tutorial_id):
    # Ensure only admin users can delete tutorials
    if not current_user.is_admin:
        flash('You do not have permission to perform this action.', 'danger')
        return redirect(url_for('home'))

    tutorial = Tutorial.query.get_or_404(tutorial_id)
    db.session.delete(tutorial)
    db.session.commit()
    flash('Tutorial deleted successfully.', 'success')
    return redirect(url_for('tutorials'))

@app.route('/delete-product/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    # Ensure only admin users can delete products
    if not current_user.is_admin:
        flash('You do not have permission to perform this action.', 'danger')
        return redirect(url_for('home'))

    # Fetch the product by ID
    product = Product.query.get_or_404(product_id)

    # Delete the product
    db.session.delete(product)
    db.session.commit()

    # Flash success message and redirect
    flash('Product deleted successfully.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/register-facilitator', methods=['GET', 'POST'])
@login_required
def register_facilitator():
    # Ensure only admin users can access this route
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('home'))

    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if the email or username already exists
        existing_user = User.query.filter((User.email == form.email.data) | (User.username == form.username.data)).first()
        if existing_user:
            flash('Username or email already exists. Please choose a different one.', 'danger')
            return redirect(url_for('register_facilitator'))

        # Create a new facilitator
        hashed_password = generate_password_hash(form.password.data)
        new_facilitator = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=hashed_password,
            role='facilitator',  # Set role to 'facilitator'
            is_admin=False  # Facilitators are not admins
        )
        db.session.add(new_facilitator)
        db.session.commit()

        flash('Facilitator account has been created successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('register_facilitator.html', form=form)

@app.route('/delete-comment/<int:comment_id>', methods=['POST'])
@login_required
def delete_comment(comment_id):
    # Ensure only admin users can delete comments/replies
    if not current_user.is_admin:
        flash('You do not have permission to perform this action.', 'danger')
        return redirect(url_for('home'))

    comment = Comment.query.get_or_404(comment_id)
    tutorial_id = comment.tutorial_id
    db.session.delete(comment)
    db.session.commit()
    flash('Comment/reply deleted successfully.', 'success')
    return redirect(url_for('tutorial_detail', tutorial_id=tutorial_id))

@app.route('/notification/<int:notif_id>/read', methods=['POST'])
@login_required
def mark_read(notif_id):
    from app.model import Notification
    notif = Notification.query.get_or_404(notif_id)
    if notif.user_id != current_user.id:
        abort(403)
    notif.is_read = True
    db.session.commit()
    flash('Notification marked as read.', 'success')
    return redirect(url_for('notifications'))

@app.route('/notification/<int:notif_id>/unread', methods=['POST'])
@login_required
def mark_unread(notif_id):
    from app.model import Notification
    notif = Notification.query.get_or_404(notif_id)
    if notif.user_id != current_user.id:
        abort(403)
    notif.is_read = False
    db.session.commit()
    flash('Notification marked as unread.', 'info')
    return redirect(url_for('notifications'))

@app.route('/notification/<int:notif_id>/delete', methods=['POST'])
@login_required
def delete_notification(notif_id):
    from app.model import Notification
    notif = Notification.query.get_or_404(notif_id)
    if notif.user_id != current_user.id:
        abort(403)
    db.session.delete(notif)
    db.session.commit()
    flash('Notification deleted.', 'warning')
    return redirect(url_for('notifications'))

# API endpoint for unread notification count
from flask import jsonify

@app.route('/api/unread_notification_count')
@login_required
def unread_notification_count():
    count = current_user.notifications.filter_by(is_read=False).count()
    return jsonify({'count': count})

@app.route('/place-order/<int:product_id>', methods=['POST'])
@login_required
def place_order(product_id):
    product = Product.query.get_or_404(product_id)
    if product.user_id == current_user.id:
        flash('You cannot order your own product.', 'warning')
        return redirect(url_for('view_products'))

    # Prevent duplicate orders by the same user for the same product if still pending
    existing_order = Order.query.filter_by(product_id=product_id, buyer_id=current_user.id, status='pending').first()
    if existing_order:
        flash('You have already placed an order for this product. Please wait for the seller to respond.', 'info')
        return redirect(url_for('view_products'))

    # Create the order
    order = Order(product_id=product_id, buyer_id=current_user.id, seller_id=product.user_id)
    db.session.add(order)
    db.session.commit()

    # Notify the seller
    notif = Notification(
        user_id=product.user_id,
        message=f"{current_user.username} placed an order for your product '{product.name}'.",
    )
    db.session.add(notif)
    db.session.commit()

    flash('Order placed successfully! The seller will be notified.', 'success')
    return redirect(url_for('view_products'))

@app.route('/seller/orders')
@login_required
def seller_orders():
    # Only show orders where the current user is the seller
    orders = Order.query.filter_by(seller_id=current_user.id).order_by(Order.timestamp.desc()).all()
    return render_template('seller_orders.html', orders=orders)

@app.route('/order/<int:order_id>/accept', methods=['POST'])
@login_required
def accept_order(order_id):
    order = Order.query.get_or_404(order_id)
    if order.seller_id != current_user.id:
        flash('You do not have permission to accept this order.', 'danger')
        return redirect(url_for('seller_orders'))
    order.status = 'accepted'
    db.session.commit()
    # Notify the buyer
    notif = Notification(
        user_id=order.buyer_id,
        message=f"Your order for '{order.product.name}' has been accepted!"
    )
    db.session.add(notif)
    db.session.commit()
    flash('Order accepted.', 'success')
    return redirect(url_for('seller_orders'))

@app.route('/order/<int:order_id>/reject', methods=['POST'])
@login_required
def reject_order(order_id):
    order = Order.query.get_or_404(order_id)
    if order.seller_id != current_user.id:
        flash('You do not have permission to reject this order.', 'danger')
        return redirect(url_for('seller_orders'))
    order.status = 'rejected'
    db.session.commit()
    # Notify the buyer
    notif = Notification(
        user_id=order.buyer_id,
        message=f"Your order for '{order.product.name}' has been rejected."
    )
    db.session.add(notif)
    db.session.commit()
    flash('Order rejected.', 'info')
    return redirect(url_for('seller_orders'))