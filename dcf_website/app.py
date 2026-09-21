from flask import Flask, render_template, request, redirect, url_for, flash, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dcf-hq-secure-key-2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dcf_database.db'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- Brand Identity Constants ---
COLOR_PRIMARY = "#0F2D23"    # Deep Forest Green
COLOR_ACCENT = "#C27A3F"     # Warm Gold / Amber
COLOR_BG = "#F8F5EF"         # Soft Cream / Off-White
COLOR_TEXT = "#1A1A1A"       # Charcoal Black

# --- Database Models ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    is_admin = db.Column(db.Boolean, default=False)

class SiteSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bg_color = db.Column(db.String(50), default=COLOR_BG)
    primary_color = db.Column(db.String(50), default=COLOR_PRIMARY)
    accent_color = db.Column(db.String(50), default=COLOR_ACCENT)
    text_color = db.Column(db.String(50), default=COLOR_TEXT)
    publication_status = db.Column(db.String(50), default="LOCKED") # LOCKED / PUBLISHED
    custom_ad_code = db.Column(db.Text, default='<div class="p-4 bg-amber-100 border border-amber-300 rounded text-center text-xs text-amber-800">Verified Retailer Ad Space</div>')

class Store(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    description = db.Column(db.Text)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    asin = db.Column(db.String(100))
    model = db.Column(db.String(100))
    target_market = db.Column(db.String(10), default="US") # US, EG, SA, UAE
    features = db.Column(db.Text)
    reasons_to_buy = db.Column(db.Text)
    overall_score = db.Column(db.Float, default=6.71)
    score_value = db.Column(db.Float, default=6.70)
    score_utility = db.Column(db.Float, default=6.80)
    score_practicality = db.Column(db.Float, default=6.70)
    score_content = db.Column(db.Float, default=6.50)
    score_demand = db.Column(db.Float, default=6.90)
    score_women_appeal = db.Column(db.Float, default=6.40)
    status = db.Column(db.String(50), default="CONTENT READY")
    store_id = db.Column(db.Integer, db.ForeignKey('store.id'))
    image_url = db.Column(db.String(500))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Context Processor for Global Variables ---
@app.context_processor
def inject_settings():
    return dict(settings=SiteSettings.query.first())

# --- Routes ---
@app.route('/')
def index():
    selected_market = request.args.get('market', 'US')
    products = Product.query.filter_by(target_market=selected_market).all()
    if not products:
        products = Product.query.all()
    return render_template('index.html', products=products, current_market=selected_market)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/stores')
def stores():
    all_stores = Store.query.all()
    return render_template('stores.html', stores=all_stores)

@app.route('/product/<int:id>')
def product(id):
    prod = Product.query.get_or_404(id)
    return render_template('product.html', product=prod)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('admin'))
        flash('Invalid authorization credentials.')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if not current_user.is_admin:
        return "Access Denied: Founder Authorization Required", 403
    
    settings = SiteSettings.query.first()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'update_settings':
            settings.bg_color = request.form.get('bg_color')
            settings.primary_color = request.form.get('primary_color')
            settings.accent_color = request.form.get('accent_color')
            db.session.commit()
            flash('Brand palette updated successfully!')
        elif action == 'toggle_launch':
            auth_phrase = request.form.get('auth_phrase', '').strip()
            if auth_phrase == "AUTHORIZE PUBLIC LAUNCH":
                settings.publication_status = "PUBLISHED"
                db.session.commit()
                flash('Public launch authorized successfully!')
            else:
                flash('Incorrect authorization phrase. Launch remains locked.')
    
    products = Product.query.all()
    return render_template('admin.html', products=products)

@app.route('/accept-cookies', methods=['POST'])
def accept_cookies():
    resp = make_response(redirect(request.referrer or url_for('index')))
    resp.set_cookie('dcf_analytics_consent', 'allowed', max_age=60*60*24*365)
    return resp

# --- Database Setup & Seeding ---
def init_db():
    with app.app_context():
        db.create_all()
        # Admin Account Setup
        if not User.query.filter_by(email='comfortablefinds@gmail.com').first():
            admin = User(
                email='comfortablefinds@gmail.com',
                password=generate_password_hash('Password@1'),
                is_admin=True
            )
            db.session.add(admin)
        
        # Site Settings Initialization
        if not SiteSettings.query.first():
            db.session.add(SiteSettings())

        # 20 Stores Setup
        store_list = [
            ("Amazon (Global)", "The world's largest online retailer, marketplace, and cloud service provider."),
            ("AliExpress / Alibaba (Global)", "Massive global retail and wholesale marketplace connecting buyers with manufacturers."),
            ("eBay (Global)", "The pioneer of online auctions and consumer-to-consumer e-commerce."),
            ("JD.com (China)", "One of the largest B2C online retailers in the world, known for its massive logistics network."),
            ("Walmart.com (Global)", "The retail giant's massive e-commerce platform, serving as Amazon's direct competitor."),
            ("Mercado Libre (Latin America)", "The undisputed e-commerce and digital payments giant of South America."),
            ("Rakuten (Japan)", "Japan's largest e-commerce platform, often called the 'Amazon of Japan'."),
            ("Shopee (Southeast Asia)", "The dominant mobile-first online marketplace across Southeast Asia and Taiwan."),
            ("Shein (Global)", "The world's largest online-only fast-fashion retailer."),
            ("Temu (Global)", "A rapidly growing cross-border marketplace known for ultra-low factory-direct prices."),
            ("Etsy (Global)", "The premier online marketplace focused exclusively on handmade, vintage, and craft goods."),
            ("Flipkart (India)", "India's leading e-commerce marketplace (majority-owned by Walmart)."),
            ("Coupang (South Korea)", "South Korea's largest online retailer, famous for its ultra-fast 'Rocket Delivery'."),
            ("Pinduoduo (China)", "A major e-commerce platform that pioneered the 'team purchase' model."),
            ("ASOS (Global)", "A major British online fashion and cosmetic retailer aimed at young adults."),
            ("Zalando (Europe)", "Europe's leading online platform for fashion and lifestyle products."),
            ("Wayfair (Global)", "The world's largest online-only retailer specializing in home furniture and decor."),
            ("Noon (Middle East)", "The leading homegrown e-commerce marketplace in the Arab world."),
            ("Trendyol (Turkey/Europe)", "Turkey's largest e-commerce platform and rapidly growing fashion player."),
            ("Ozon (Russia)", "One of the region's oldest and largest online marketplaces.")
        ]
        if Store.query.count() == 0:
            for name, desc in store_list:
                db.session.add(Store(name=name, description=desc))
        
        # Seed Product #001
        if Product.query.count() == 0:
            p1 = Product(
                name="MCGOR 10-inch Rechargeable Motion-Sensor Under-Cabinet Lights, 2 Pack",
                asin="B0BDF8CVBN",
                model="GLS-C010",
                target_market="US",
                features="Motion activated, magnetic mounting, USB-C rechargeable, 5 brightness levels, 2-pack",
                reasons_to_buy="Passes all six DCF utility tests. Exceptional motion-activation speed, tool-free magnetic installation, zero recurring battery cost via USB-C charging, and high practical utility for kitchens and dark cabinets.",
                overall_score=6.71,
                score_value=6.70,
                score_utility=6.80,
                score_practicality=6.70,
                score_content=6.50,
                score_demand=6.90,
                score_women_appeal=6.40,
                status="CONTENT READY",
                store_id=1,
                image_url="https://images.unsplash.com/photo-1565814636199-ae8133055c1c?auto=format&fit=crop&w=800&q=80"
            )
            db.session.add(p1)
        
        db.session.commit()

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
