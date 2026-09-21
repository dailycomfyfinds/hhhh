import os
import zipfile

# --- 1. Define updated website files and brand assets ---

files = {}

files['requirements.txt'] = """Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-Login==0.6.3
Werkzeug==3.0.0"""

files['app.py'] = r"""from flask import Flask, render_template, request, redirect, url_for, flash, make_response
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
"""

# --- HTML Templates with Integrated Brand Palette & Logo SVG ---

files['templates/base.html'] = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daily Comfy Finds (DCF) | Smart Finds for Everyday Life</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        :root {
            --color-primary: {{ settings.primary_color }};
            --color-accent: {{ settings.accent_color }};
            --color-bg: {{ settings.bg_color }};
            --color-text: {{ settings.text_color }};
        }
        body { background-color: var(--color-bg); color: var(--color-text); font-family: system-ui, -apple-system, sans-serif; }
        .bg-dcf-primary { background-color: var(--color-primary); }
        .bg-dcf-accent { background-color: var(--color-accent); }
        .text-dcf-primary { color: var(--color-primary); }
        .text-dcf-accent { color: var(--color-accent); }
        .border-dcf-accent { border-color: var(--color-accent); }
        .border-dcf-primary { border-color: var(--color-primary); }
    </style>
</head>
<body class="min-h-screen flex flex-col">
    <!-- Status Bar -->
    <div class="bg-black text-amber-300 text-xs py-1 px-4 text-center font-mono flex justify-between items-center">
        <span>STATUS: <strong class="uppercase text-white">{{ settings.publication_status }}</strong></span>
        <span>الكمال لله — Perfection Belongs to Allah</span>
        <span>MARKETS: 🇺🇸 US | 🇪🇬 EG | 🇸🇦 SA | 🇦🇪 UAE</span>
    </div>

    <!-- Header Navigation -->
    <header class="bg-dcf-primary text-white border-b-4 border-dcf-accent shadow-lg">
        <div class="container mx-auto px-4 py-3 flex justify-between items-center">
            <!-- Brand Logo Emblem -->
            <a href="/" class="flex items-center space-x-3 group">
                <svg class="w-12 h-12 rounded-full border-2 border-dcf-accent shadow-md transition transform group-hover:scale-105" viewBox="0 0 200 200" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="100" cy="100" r="96" fill="#0F2D23" stroke="#C27A3F" stroke-width="8"/>
                    <!-- Handle / Bag Loop -->
                    <path d="M70 70 C70 45, 130 45, 130 70" stroke="#C27A3F" stroke-width="10" fill="none" stroke-linecap="round"/>
                    <!-- Bag Silhouette -->
                    <rect x="50" y="70" width="100" height="85" rx="12" fill="#0F2D23" stroke="#F8F5EF" stroke-width="6"/>
                    <!-- DCF Stylized Monogram -->
                    <text x="100" y="122" font-family="Arial, sans-serif" font-weight="900" font-size="34" fill="#C27A3F" text-anchor="middle">DCF</text>
                    <!-- Leaf Accents -->
                    <path d="M135 60 Q160 50 165 75 Q140 85 135 60 Z" fill="#C27A3F"/>
                    <path d="M145 72 Q170 70 170 90 Q145 95 145 72 Z" fill="#A4622D"/>
                </svg>
                <div>
                    <span class="text-2xl font-black tracking-wide block leading-none text-white">Daily Comfy Finds</span>
                    <span class="text-xs tracking-wider text-amber-200 uppercase font-semibold">Smart Finds for Everyday Life</span>
                </div>
            </a>

            <!-- Nav Links -->
            <nav class="hidden md:flex items-center space-x-6 text-sm font-medium">
                <a href="/" class="hover:text-amber-300 transition">Home</a>
                <a href="/stores" class="hover:text-amber-300 transition">20 Global Stores</a>
                <a href="/about" class="hover:text-amber-300 transition">DCF Methodology</a>
                {% if current_user.is_authenticated %}
                    <a href="/admin" class="bg-amber-600 px-3 py-1 rounded text-white font-bold hover:bg-amber-700">Admin Control</a>
                    <a href="/logout" class="text-gray-300 hover:text-white">Logout</a>
                {% else %}
                    <a href="/login" class="text-gray-300 hover:text-white">Admin Login</a>
                {% endif %}
            </nav>
        </div>
    </header>

    <!-- Main Content Body -->
    <main class="container mx-auto flex-grow px-4 py-6">
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                {% for message in messages %}
                    <div class="bg-amber-100 border-l-4 border-amber-600 text-amber-900 p-4 mb-4 rounded shadow text-sm font-semibold">
                        {{ message }}
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        {% block content %}{% endblock %}
    </main>

    <!-- Pillar Motto Bar -->
    <section class="bg-stone-200 border-t border-b border-stone-300 py-4 text-center text-xs font-bold text-stone-700 tracking-wider">
        <div class="container mx-auto grid grid-cols-1 md:grid-cols-3 gap-2">
            <div>🏠 BETTER HOME</div>
            <div>🛒 EASIER LIFE</div>
            <div>🌿 BRIGHTER DAYS</div>
        </div>
    </section>

    <!-- Footer -->
    <footer class="bg-dcf-primary text-gray-300 py-8 border-t-4 border-dcf-accent text-sm">
        <div class="container mx-auto px-4 grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
                <h4 class="text-white font-bold mb-2">Daily Comfy Finds (DCF)</h4>
                <p class="text-xs text-stone-300 leading-relaxed">
                    Global product discovery and recommendation brand. DCF refers visitors to official retailers and does not take payments or sell products directly.
                </p>
                <p class="text-xs text-amber-300 mt-2 font-semibold">الكمال لله — Perfection Belongs to Allah</p>
            </div>
            <div>
                <h4 class="text-white font-bold mb-2">Standard & Discipline</h4>
                <p class="text-xs text-stone-300 leading-relaxed">
                    Trust before commission. Unsupported claims are never presented as fact. Retailer pages control final price, availability, shipping, and returns.
                </p>
            </div>
            <div>
                <h4 class="text-white font-bold mb-2">Social Channels</h4>
                <p class="text-xs text-stone-300 mb-2">Instagram • TikTok • YouTube • Facebook • Pinterest • Snapchat</p>
                <p class="text-xs text-stone-400">Contact: comfortablefinds@gmail.com</p>
            </div>
        </div>
        <div class="text-center text-xs text-stone-400 mt-6 pt-4 border-t border-stone-800">
            &copy; 2026 Daily Comfy Finds (DCF-HQ). All rights reserved.
        </div>
    </footer>

    <!-- Cookie Consent Popup -->
    {% if not request.cookies.get('dcf_analytics_consent') %}
    <div class="fixed bottom-0 left-0 right-0 bg-stone-900 text-stone-200 p-4 border-t-2 border-dcf-accent shadow-2xl z-50 flex flex-col md:flex-row justify-between items-center text-xs space-y-2 md:space-y-0">
        <p class="md:w-3/4">
            <strong>Analytics Notice:</strong> Non-essential analytics (Google Analytics) activate only after user consent. Retailers may receive visit attribution information upon referral.
        </p>
        <div class="space-x-2">
            <form method="POST" action="/accept-cookies" class="inline">
                <button type="submit" class="bg-dcf-accent text-white px-4 py-2 rounded font-bold hover:opacity-90">Allow Analytics</button>
            </form>
            <button onclick="this.parentElement.parentElement.style.display='none'" class="bg-stone-700 text-stone-300 px-4 py-2 rounded hover:bg-stone-600">Decline</button>
        </div>
    </div>
    {% endif %}
</body>
</html>"""

files['templates/index.html'] = """{% extends "base.html" %}
{% block content %}
<!-- Market Selector & Search Hero -->
<div class="bg-dcf-primary text-white p-8 rounded-xl shadow-xl mb-8 border border-amber-900/30">
    <div class="max-w-2xl mx-auto text-center">
        <h1 class="text-3xl md:text-4xl font-extrabold mb-2">Products Worth Discovering.</h1>
        <p class="text-amber-200 text-sm mb-6">AI-Powered Multi-Store Aggregator Across 20 Global Retailers</p>
        
        <!-- Search Input -->
        <div class="flex gap-2">
            <input type="text" placeholder="Search by intent, problem, or product type..." class="w-full p-3 rounded-lg text-stone-900 shadow focus:ring-2 focus:ring-amber-500 outline-none">
            <button class="bg-dcf-accent px-6 py-3 rounded-lg font-bold hover:bg-amber-700 transition shadow">Search</button>
        </div>

        <!-- Target Market Switcher -->
        <div class="mt-6 flex justify-center items-center space-x-3 text-xs font-semibold">
            <span class="text-stone-300">Target Market:</span>
            <a href="/?market=US" class="px-3 py-1 rounded-full {% if current_market == 'US' %}bg-dcf-accent text-white{% else %}bg-stone-800 text-stone-300{% endif %}">🇺🇸 United States</a>
            <a href="/?market=EG" class="px-3 py-1 rounded-full {% if current_market == 'EG' %}bg-dcf-accent text-white{% else %}bg-stone-800 text-stone-300{% endif %}">🇪🇬 Egypt</a>
            <a href="/?market=SA" class="px-3 py-1 rounded-full {% if current_market == 'SA' %}bg-dcf-accent text-white{% else %}bg-stone-800 text-stone-300{% endif %}">🇸🇦 Saudi Arabia</a>
            <a href="/?market=UAE" class="px-3 py-1 rounded-full {% if current_market == 'UAE' %}bg-dcf-accent text-white{% else %}bg-stone-800 text-stone-300{% endif %}">🇦🇪 UAE</a>
        </div>
    </div>
</div>

<!-- Current Candidates / Product Grid -->
<div class="flex justify-between items-center mb-4">
    <h2 class="text-2xl font-bold text-dcf-primary">Evaluated Finds (Market: {{ current_market }})</h2>
    <span class="text-xs bg-amber-100 text-amber-800 font-bold px-3 py-1 rounded-full border border-amber-300">DCF Quality Gate Passed</span>
</div>

<div class="grid grid-cols-1 md:grid-cols-3 gap-6">
    {% for product in products %}
    <div class="bg-white rounded-xl shadow-md border border-stone-200 overflow-hidden flex flex-col hover:shadow-xl transition">
        <div class="relative">
            <img src="{{ product.image_url }}" alt="{{ product.name }}" class="w-full h-52 object-cover">
            <span class="absolute top-2 right-2 bg-dcf-primary text-amber-300 font-bold text-xs px-2 py-1 rounded shadow">
                DCF Score: {{ product.overall_score }}/7
            </span>
        </span>
        </div>
        <div class="p-5 flex-grow flex flex-col justify-between">
            <div>
                <span class="text-xs font-bold text-dcf-accent uppercase tracking-wider block mb-1">ASIN: {{ product.asin }}</span>
                <h3 class="font-bold text-lg text-stone-900 mb-2 leading-snug">{{ product.name }}</h3>
                <p class="text-stone-600 text-xs mb-4 line-clamp-3">{{ product.features }}</p>
            </div>
            
            <div>
                <div class="bg-stone-100 p-3 rounded-lg mb-4 text-xs space-y-1">
                    <div class="flex justify-between"><span>Real Utility Score:</span> <strong>{{ product.score_utility }}/7</strong></div>
                    <div class="flex justify-between"><span>Value for Money:</span> <strong>{{ product.score_value }}/7</strong></div>
                </div>
                <a href="/product/{{ product.id }}" class="block w-full text-center bg-dcf-primary text-white font-bold py-2 rounded-lg hover:bg-stone-800 transition text-sm">
                    View Full Evaluation
                </a>
            </div>
        </div>
    </div>
    {% endfor %}
</div>
{% endblock %}"""

files['templates/product.html'] = """{% extends "base.html" %}
{% block content %}
<a href="/" class="text-dcf-accent font-bold hover:underline mb-4 inline-block text-sm">&larr; Return to Global Finds</a>

<div class="bg-white rounded-xl shadow-lg border border-stone-200 p-6 md:p-8 grid grid-cols-1 md:grid-cols-2 gap-8">
    <!-- Left Column: Product Image & Creative Visualization Notice -->
    <div>
        <img src="{{ product.image_url }}" alt="{{ product.name }}" class="w-full rounded-lg shadow border border-stone-200">
        <p class="text-xs text-stone-400 mt-2 italic text-center">
            * Note: Image is a DCF creative visualization, not a retailer photo.
        </p>
    </div>

    <!-- Right Column: Scores & Evaluation -->
    <div class="flex flex-col justify-between">
        <div>
            <div class="flex items-center justify-between mb-2">
                <span class="bg-amber-100 text-amber-800 text-xs font-bold px-2.5 py-1 rounded border border-amber-300">Status: {{ product.status }}</span>
                <span class="text-xs text-stone-500 font-mono">ASIN: {{ product.asin }} | Model: {{ product.model }}</span>
            </div>
            
            <h1 class="text-2xl font-black text-dcf-primary mb-4 leading-tight">{{ product.name }}</h1>

            <!-- DCF SEXY SCORE CARD -->
            <div class="bg-stone-900 text-white p-4 rounded-xl mb-6 border-l-4 border-dcf-accent">
                <div class="flex justify-between items-center mb-3">
                    <span class="text-xs font-bold uppercase tracking-wider text-amber-300">DCF Evaluation Score</span>
                    <span class="text-2xl font-black text-amber-400">{{ product.overall_score }} <span class="text-sm font-normal text-stone-400">/ 7</span></span>
                </div>
                <div class="grid grid-cols-2 gap-x-4 gap-y-2 text-xs">
                    <div>Value for Money: <strong>{{ product.score_value }}</strong></div>
                    <div>Real Utility: <strong>{{ product.score_utility }}</strong></div>
                    <div>Practicality: <strong>{{ product.score_practicality }}</strong></div>
                    <div>Content Potential: <strong>{{ product.score_content }}</strong></div>
                    <div>Demand Evidence: <strong>{{ product.score_demand }}</strong></div>
                    <div>Women Appeal: <strong>{{ product.score_women_appeal }}</strong></div>
                </div>
            </div>

            <h3 class="font-bold text-md text-dcf-primary border-b pb-1 mb-2">Key Features</h3>
            <p class="text-stone-700 text-sm mb-6 leading-relaxed">{{ product.features }}</p>

            <h3 class="font-bold text-md text-dcf-primary border-b pb-1 mb-2">Why Buy This? (DCF Evaluation)</h3>
            <p class="text-stone-700 text-sm mb-6 leading-relaxed">{{ product.reasons_to_buy }}</p>

            <!-- Custom Ad Space -->
            <div class="mb-6">
                {{ settings.custom_ad_code | safe }}
            </div>
        </div>

        <!-- Referral CTA -->
        <div>
            <button class="w-full bg-dcf-accent text-white font-extrabold py-3.5 rounded-xl shadow-lg hover:bg-amber-700 transition text-center block text-md uppercase tracking-wider">
                Check Availability at Official Retailer
            </button>
            <p class="text-xs text-stone-500 mt-2 text-center leading-normal">
                DCF does not sell the product or process the purchase. The retailer controls price, availability, payment, shipping, returns, and warranty.
            </p>
        </div>
    </div>
</div>
{% endblock %}"""

files['templates/stores.html'] = """{% extends "base.html" %}
{% block content %}
<div class="mb-6">
    <h1 class="text-3xl font-black text-dcf-primary">Supported Retailers & Marketplaces (20)</h1>
    <p class="text-stone-600 text-sm">Official sources referenced across global regions.</p>
</div>

<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
    {% for store in stores %}
    <div class="bg-white p-5 rounded-xl shadow border-l-4 border-dcf-accent border-y border-r border-stone-200">
        <h3 class="font-bold text-lg text-dcf-primary mb-1">{{ store.name }}</h3>
        <p class="text-xs text-stone-600 leading-relaxed">{{ store.description }}</p>
    </div>
    {% endfor %}
</div>
{% endblock %}"""

files['templates/about.html'] = """{% extends "base.html" %}
{% block content %}
<div class="bg-white p-8 rounded-xl shadow-md max-w-4xl mx-auto space-y-8 text-stone-800">
    <div class="border-b pb-4">
        <h1 class="text-3xl font-black text-dcf-primary">The DCF Standard & Methodology</h1>
        <p class="text-amber-700 font-semibold text-sm mt-1">Trust before commission. Unsupported claims are never presented as fact.</p>
    </div>

    <section>
        <h2 class="text-xl font-bold text-dcf-primary mb-3">1. AI Integration & Search Engine</h2>
        <p class="text-sm leading-relaxed text-stone-700">
            Daily Comfy Finds utilizes natural language intent mapping across 20 global online store indexes. Instead of relying purely on search keywords, our AI engine matches user complaints and daily routines directly to verified product solutions.
        </p>
    </section>

    <section>
        <h2 class="text-xl font-bold text-dcf-primary mb-3">2. The DCF Method: Six Evaluation Questions</h2>
        <ul class="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
            <li class="bg-stone-50 p-3 rounded border"><strong>Value for Money:</strong> Does the value make sense relative to price?</li>
            <li class="bg-stone-50 p-3 rounded border"><strong>Real Utility:</strong> Does it solve a real, recurring problem?</li>
            <li class="bg-stone-50 p-3 rounded border"><strong>Practicality:</strong> Is it easy enough to live with?</li>
            <li class="bg-stone-50 p-3 rounded border"><strong>Content Potential:</strong> Can it be explained honestly and clearly?</li>
            <li class="bg-stone-50 p-3 rounded border"><strong>Demand:</strong> Is there evidence people want this solution?</li>
            <li class="bg-stone-50 p-3 rounded border"><strong>Women Appeal:</strong> Does it solve a meaningful everyday need?</li>
        </ul>
        <p class="text-xs font-bold text-stone-500 mt-2">Evaluation Outcomes: PASS / REVIEW / REJECT. Commission never overrides quality.</p>
    </section>

    <section>
        <h2 class="text-xl font-bold text-dcf-primary mb-3">3. Community-Powered Discovery Rules</h2>
        <p class="text-sm mb-2 font-semibold text-stone-700">What we will NEVER do:</p>
        <ul class="list-disc ml-6 text-sm text-stone-600 space-y-1">
            <li>Invent a customer review</li>
            <li>Delete honest negative feedback</li>
            <li>Present sponsored opinion as independent</li>
            <li>Require a positive review for a reward</li>
            <li>Turn one unusual experience into a universal claim</li>
            <li>Use testimonials without required disclosures</li>
        </ul>
    </section>

    <section>
        <h2 class="text-xl font-bold text-dcf-primary mb-3">4. Trust Center & Legal Disclosures</h2>
        <div class="bg-stone-100 p-4 rounded-lg text-xs leading-relaxed space-y-3 border border-stone-300">
            <p><strong>Referral Model:</strong> DCF is a product discovery and recommendation brand. It refers visitors to official retailers and is not the seller, payment processor, or fulfiller.</p>
            <p><strong>Affiliate Disclosure:</strong> DCF may receive a commission on qualifying purchases at no extra cost to the visitor. Commission status does not guarantee a positive recommendation.</p>
            <p><strong>Contact:</strong> comfortablefinds@gmail.com — Reports of inaccurate claims or broken links are treated immediately as verification issues.</p>
        </div>
    </section>
</div>
{% endblock %}"""

files['templates/login.html'] = """{% extends "base.html" %}
{% block content %}
<div class="max-w-md mx-auto bg-white p-8 rounded-xl shadow-lg mt-8 border border-stone-200">
    <h1 class="text-2xl font-black text-dcf-primary mb-2 text-center">DCF Founder Login</h1>
    <p class="text-xs text-stone-500 text-center mb-6">Restricted System Access</p>

    <form method="POST">
        <div class="mb-4">
            <label class="block text-xs font-bold uppercase text-stone-700 mb-1">Founder Account</label>
            <input type="email" name="email" value="comfortablefinds@gmail.com" class="w-full border p-2.5 rounded-lg text-sm bg-stone-50 focus:ring-2 focus:ring-amber-500 outline-none" required>
        </div>
        <div class="mb-6">
            <label class="block text-xs font-bold uppercase text-stone-700 mb-1">Password</label>
            <input type="password" name="password" placeholder="••••••••" class="w-full border p-2.5 rounded-lg text-sm focus:ring-2 focus:ring-amber-500 outline-none" required>
        </div>
        <button type="submit" class="w-full bg-dcf-primary text-white font-bold py-3 rounded-lg hover:bg-stone-800 transition">
            Authenticate System Access
        </button>
    </form>
</div>
{% endblock %}"""

files['templates/admin.html'] = """{% extends "base.html" %}
{% block content %}
<div class="mb-6 flex justify-between items-center">
    <div>
        <h1 class="text-3xl font-black text-dcf-primary">DCF HQ Execution Dashboard</h1>
        <p class="text-xs text-stone-500">System Verification & Launch Control</p>
    </div>
    <div class="bg-stone-900 text-amber-300 px-4 py-2 rounded-lg text-xs font-mono font-bold">
        Launch Gate Status: {{ settings.publication_status }}
    </div>
</div>

<div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
    <!-- Brand Identity & Color Controls -->
    <div class="bg-white p-6 rounded-xl shadow border border-stone-200">
        <h2 class="text-lg font-bold text-dcf-primary mb-4 border-b pb-2">Brand Palette Settings</h2>
        <form method="POST" class="space-y-4">
            <input type="hidden" name="action" value="update_settings">
            <div>
                <label class="block text-xs font-bold mb-1">Primary Color (Deep Green)</label>
                <input type="color" name="primary_color" value="{{ settings.primary_color }}" class="w-full h-10 rounded cursor-pointer">
            </div>
            <div>
                <label class="block text-xs font-bold mb-1">Accent Color (Warm Gold)</label>
                <input type="color" name="accent_color" value="{{ settings.accent_color }}" class="w-full h-10 rounded cursor-pointer">
            </div>
            <div>
                <label class="block text-xs font-bold mb-1">Background Canvas</label>
                <input type="color" name="bg_color" value="{{ settings.bg_color }}" class="w-full h-10 rounded cursor-pointer">
            </div>
            <button type="submit" class="bg-dcf-primary text-white text-xs font-bold px-4 py-2.5 rounded hover:bg-stone-800">
                Update Canvas Palette
            </button>
        </form>
    </div>

    <!-- Launch Authorization Gate -->
    <div class="bg-white p-6 rounded-xl shadow border border-stone-200">
        <h2 class="text-lg font-bold text-dcf-primary mb-2 border-b pb-2">Publication Gate Lock</h2>
        <p class="text-xs text-stone-600 mb-4 leading-relaxed">
            Public launch remains strictly locked until all verification criteria pass. Enter the exact founder phrase to authorize public launch.
        </p>
        <form method="POST" class="space-y-4">
            <input type="hidden" name="action" value="toggle_launch">
            <div>
                <label class="block text-xs font-bold mb-1">Launch Phrase Authorization</label>
                <input type="text" name="auth_phrase" placeholder="AUTHORIZE PUBLIC LAUNCH" class="w-full border p-2.5 rounded text-xs font-mono">
            </div>
            <button type="submit" class="bg-amber-600 text-white text-xs font-bold px-4 py-2.5 rounded hover:bg-amber-700">
                Submit Launch Key
            </button>
        </form>
    </div>
</div>

<!-- Product Master List -->
<div class="bg-white p-6 rounded-xl shadow border border-stone-200">
    <h2 class="text-lg font-bold text-dcf-primary mb-4">Evaluated Products Master List</h2>
    <div class="overflow-x-auto">
        <table class="w-full text-left text-xs text-stone-700">
            <thead class="bg-stone-100 uppercase text-stone-600 font-bold">
                <tr>
                    <th class="p-3">ID</th>
                    <th class="p-3">Product Name</th>
                    <th class="p-3">ASIN</th>
                    <th class="p-3">Market</th>
                    <th class="p-3">Score</th>
                    <th class="p-3">Status</th>
                </tr>
            </thead>
            <tbody class="divide-y">
                {% for p in products %}
                <tr>
                    <td class="p-3 font-bold">#{{ "%03d" % p.id }}</td>
                    <td class="p-3 font-semibold text-stone-900">{{ p.name }}</td>
                    <td class="p-3 font-mono">{{ p.asin }}</td>
                    <td class="p-3 font-bold">{{ p.target_market }}</td>
                    <td class="p-3 font-bold text-amber-700">{{ p.overall_score }}/7</td>
                    <td class="p-3"><span class="bg-green-100 text-green-800 px-2 py-0.5 rounded text-xs font-bold">{{ p.status }}</span></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endblock %}"""

# --- 2. Build Directory Structure and Archive ---

project_dir = "dcf_website"
os.makedirs(f"{project_dir}/templates", exist_ok=True)

for filepath, content in files.items():
    with open(f"{project_dir}/{filepath}", "w", encoding="utf-8") as f:
        f.write(content)

zip_filename = "dcf_website.zip"
with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, filenames in os.walk(project_dir):
        for file in filenames:
            file_path = os.path.join(root, file)
            arcname = os.path.relpath(file_path, project_dir)
            zipf.write(file_path, arcname)

print(f"Success! Updated brand system generated in {zip_filename}.")