# VBWD-SDK as a Marketplace Platform

**Document:** Marketplace Architecture for SaaS & Educational Services
**Status:** Planning
**License:** CC0 1.0 Universal (Public Domain)

---

## Executive Summary

This document describes how VBWD-SDK can evolve into a **Marketplace Platform** that enables third-party vendors to offer their SaaS products and educational services to end users. The platform acts as an intermediary, handling payments, subscriptions, access control, and providing a unified discovery experience.

---

## 1. Marketplace Concept

### 1.1 Platform Ecosystem

```
+-------------------------------------------------------------------------+
|                     VBWD Marketplace Ecosystem                           |
+-------------------------------------------------------------------------+
|                                                                          |
|  +-----------------------------+     +-----------------------------+     |
|  |      SERVICE PROVIDERS      |     |        END USERS            |     |
|  +-----------------------------+     +-----------------------------+     |
|  |                             |     |                             |     |
|  | - SaaS Vendors              |     | - Individual Learners       |     |
|  | - Online Course Creators    |     | - Business Professionals    |     |
|  | - Tutors & Instructors      |     | - Companies (B2B)           |     |
|  | - Consultants               |     | - Students                  |     |
|  | - Content Creators          |     |                             |     |
|  +-----------------------------+     +-----------------------------+     |
|               |                               |                          |
|               +---------------+---------------+                          |
|                               |                                          |
|         +--------------------------------------------+                   |
|         |            VBWD MARKETPLACE                |                   |
|         +--------------------------------------------+                   |
|         |                                            |                   |
|         | - Unified Discovery & Search               |                   |
|         | - Subscription Management                  |                   |
|         | - Payment Processing                       |                   |
|         | - Access Control (SSO)                     |                   |
|         | - Reviews & Ratings                        |                   |
|         | - Analytics & Reporting                    |                   |
|         | - Affiliate Program                        |                   |
|         +--------------------------------------------+                   |
|                               |                                          |
|         +--------------------------------------------+                   |
|         |           REVENUE DISTRIBUTION             |                   |
|         |                                            |                   |
|         |  Vendor (80%) <----> Platform (20%)        |                   |
|         +--------------------------------------------+                   |
|                                                                          |
+-------------------------------------------------------------------------+
```

### 1.2 Marketplace Value Proposition

| Stakeholder | Value |
|-------------|-------|
| **End Users** | Single account, unified billing, discovery, trusted reviews |
| **Vendors** | Customer acquisition, payment handling, no infrastructure needed |
| **Platform** | Transaction fees, platform growth, ecosystem network effects |

---

## 2. Vendor & Product Model

### 2.1 Vendor Entity

```sql
CREATE TABLE vendors (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,

    -- Identification
    vendor_code VARCHAR(50) UNIQUE NOT NULL,
    company_name VARCHAR(200) NOT NULL,
    display_name VARCHAR(100) NOT NULL,

    -- Contact
    email VARCHAR(255) NOT NULL,
    support_email VARCHAR(255),
    website_url VARCHAR(500),

    -- Business Details
    business_type ENUM('company', 'individual', 'institution') NOT NULL,
    tax_id VARCHAR(50),
    country VARCHAR(2) NOT NULL,

    -- Branding
    logo_url VARCHAR(500),
    banner_url VARCHAR(500),
    description TEXT,
    short_description VARCHAR(500),

    -- Verification
    is_verified BOOLEAN DEFAULT FALSE,
    verification_date DATETIME,
    verification_level ENUM('basic', 'standard', 'premium', 'enterprise') DEFAULT 'basic',

    -- Payout
    payout_method ENUM('bank_transfer', 'paypal', 'stripe_connect') DEFAULT 'bank_transfer',
    payout_details JSON,
    commission_rate DECIMAL(5,2) DEFAULT 20.00,  -- Platform commission %

    -- Performance
    total_sales DECIMAL(12,2) DEFAULT 0,
    total_customers INT DEFAULT 0,
    average_rating DECIMAL(3,2) DEFAULT 0,
    total_reviews INT DEFAULT 0,

    -- Status
    status ENUM('pending', 'active', 'suspended', 'terminated') DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_vendor_code (vendor_code),
    INDEX idx_status (status),
    INDEX idx_rating (average_rating DESC)
);
```

### 2.2 Product (Listing) Entity

```sql
CREATE TABLE products (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    vendor_id BIGINT REFERENCES vendors(id) ON DELETE CASCADE,

    -- Identification
    product_code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    slug VARCHAR(200) UNIQUE NOT NULL,

    -- Categorization
    category_id BIGINT REFERENCES product_categories(id),
    product_type ENUM('saas', 'course', 'ebook', 'service', 'consultation', 'bundle') NOT NULL,

    -- Description
    short_description VARCHAR(500),
    description TEXT,
    features JSON,  -- List of features
    requirements JSON,  -- Prerequisites

    -- Pricing
    pricing_type ENUM('one_time', 'subscription', 'freemium', 'free', 'pay_what_you_want') NOT NULL,
    base_price DECIMAL(10,2),
    currency VARCHAR(3) DEFAULT 'EUR',

    -- Media
    thumbnail_url VARCHAR(500),
    preview_images JSON,  -- Array of image URLs
    demo_url VARCHAR(500),
    video_url VARCHAR(500),

    -- Access
    access_type ENUM('immediate', 'scheduled', 'approval_required') DEFAULT 'immediate',
    delivery_method ENUM('api_access', 'download', 'streaming', 'booking', 'external_link') NOT NULL,
    external_product_url VARCHAR(500),

    -- Metrics
    total_sales INT DEFAULT 0,
    total_revenue DECIMAL(12,2) DEFAULT 0,
    active_subscribers INT DEFAULT 0,
    average_rating DECIMAL(3,2) DEFAULT 0,
    total_reviews INT DEFAULT 0,

    -- SEO
    meta_title VARCHAR(200),
    meta_description VARCHAR(500),
    tags JSON,  -- Array of tags

    -- Status
    status ENUM('draft', 'pending_review', 'published', 'suspended', 'archived') DEFAULT 'draft',
    published_at DATETIME,
    featured BOOLEAN DEFAULT FALSE,
    featured_until DATETIME,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_vendor (vendor_id),
    INDEX idx_category (category_id),
    INDEX idx_type (product_type),
    INDEX idx_status (status),
    INDEX idx_featured (featured, featured_until),
    INDEX idx_rating (average_rating DESC),
    FULLTEXT idx_search (name, short_description, description)
);
```

### 2.3 Product Pricing Plans

```sql
CREATE TABLE product_pricing_plans (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    product_id BIGINT REFERENCES products(id) ON DELETE CASCADE,

    -- Plan Details
    name VARCHAR(100) NOT NULL,
    description VARCHAR(500),

    -- Pricing
    price DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'EUR',
    billing_period ENUM('one_time', 'monthly', 'quarterly', 'yearly', 'lifetime') NOT NULL,

    -- Trial
    has_trial BOOLEAN DEFAULT FALSE,
    trial_days INT DEFAULT 0,

    -- Features
    features JSON,  -- What's included in this plan
    limits JSON,  -- Usage limits

    -- Display
    is_popular BOOLEAN DEFAULT FALSE,
    sort_order INT DEFAULT 0,

    -- Status
    is_active BOOLEAN DEFAULT TRUE,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_product (product_id),
    INDEX idx_active (is_active)
);
```

### 2.4 Categories

```sql
CREATE TABLE product_categories (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    parent_id BIGINT REFERENCES product_categories(id),

    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    icon VARCHAR(50),

    -- Hierarchy
    level INT DEFAULT 0,
    path VARCHAR(500),  -- e.g., "/1/5/12/"

    -- Display
    sort_order INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    product_count INT DEFAULT 0,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_parent (parent_id),
    INDEX idx_slug (slug)
);

-- Example Categories
INSERT INTO product_categories (name, slug, level) VALUES
('Software & SaaS', 'software-saas', 0),
('Online Courses', 'online-courses', 0),
('Professional Services', 'professional-services', 0),
('Digital Products', 'digital-products', 0);

-- Subcategories
INSERT INTO product_categories (name, slug, parent_id, level) VALUES
('Marketing Tools', 'marketing-tools', 1, 1),
('Productivity', 'productivity', 1, 1),
('Development Tools', 'development-tools', 1, 1),
('Programming', 'programming', 2, 1),
('Business', 'business', 2, 1),
('Design', 'design', 2, 1),
('Consulting', 'consulting', 3, 1),
('Coaching', 'coaching', 3, 1);
```

---

## 3. Educational Services Integration

### 3.1 Course Entity

```sql
CREATE TABLE courses (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    product_id BIGINT UNIQUE REFERENCES products(id) ON DELETE CASCADE,
    vendor_id BIGINT REFERENCES vendors(id),

    -- Course Info
    title VARCHAR(200) NOT NULL,
    subtitle VARCHAR(300),
    language VARCHAR(10) DEFAULT 'en',
    skill_level ENUM('beginner', 'intermediate', 'advanced', 'all_levels') NOT NULL,

    -- Content
    total_duration_minutes INT DEFAULT 0,
    total_lessons INT DEFAULT 0,
    total_sections INT DEFAULT 0,

    -- Instructors
    primary_instructor_id BIGINT REFERENCES instructors(id),

    -- Learning
    learning_objectives JSON,  -- What students will learn
    target_audience JSON,  -- Who this course is for
    prerequisites JSON,

    -- Certification
    has_certificate BOOLEAN DEFAULT FALSE,
    certificate_template_id BIGINT,

    -- Settings
    drip_content BOOLEAN DEFAULT FALSE,  -- Release content over time
    allow_preview BOOLEAN DEFAULT TRUE,
    discussion_enabled BOOLEAN DEFAULT TRUE,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_product (product_id),
    INDEX idx_vendor (vendor_id),
    INDEX idx_level (skill_level)
);

CREATE TABLE course_sections (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    course_id BIGINT REFERENCES courses(id) ON DELETE CASCADE,

    title VARCHAR(200) NOT NULL,
    description TEXT,
    sort_order INT NOT NULL,

    -- Drip settings
    available_after_days INT DEFAULT 0,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_course (course_id)
);

CREATE TABLE course_lessons (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    section_id BIGINT REFERENCES course_sections(id) ON DELETE CASCADE,
    course_id BIGINT REFERENCES courses(id) ON DELETE CASCADE,

    title VARCHAR(200) NOT NULL,
    description TEXT,
    content_type ENUM('video', 'text', 'quiz', 'assignment', 'download', 'live') NOT NULL,

    -- Content
    video_url VARCHAR(500),
    video_duration_seconds INT,
    text_content LONGTEXT,
    attachment_url VARCHAR(500),

    -- Settings
    is_preview BOOLEAN DEFAULT FALSE,
    is_required BOOLEAN DEFAULT TRUE,
    sort_order INT NOT NULL,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_section (section_id),
    INDEX idx_course (course_id)
);
```

### 3.2 Student Progress Tracking

```sql
CREATE TABLE student_enrollments (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    course_id BIGINT REFERENCES courses(id) ON DELETE CASCADE,
    purchase_id BIGINT REFERENCES user_purchases(id),

    -- Progress
    progress_percent DECIMAL(5,2) DEFAULT 0,
    completed_lessons INT DEFAULT 0,
    total_lessons INT DEFAULT 0,

    -- Time
    total_watch_time_seconds INT DEFAULT 0,
    last_accessed_at DATETIME,

    -- Status
    status ENUM('active', 'completed', 'expired', 'refunded') DEFAULT 'active',
    completed_at DATETIME,

    -- Certificate
    certificate_issued BOOLEAN DEFAULT FALSE,
    certificate_url VARCHAR(500),

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY unique_enrollment (user_id, course_id),
    INDEX idx_user (user_id),
    INDEX idx_course (course_id),
    INDEX idx_status (status)
);

CREATE TABLE lesson_progress (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    enrollment_id BIGINT REFERENCES student_enrollments(id) ON DELETE CASCADE,
    lesson_id BIGINT REFERENCES course_lessons(id) ON DELETE CASCADE,

    -- Progress
    is_completed BOOLEAN DEFAULT FALSE,
    completed_at DATETIME,
    progress_seconds INT DEFAULT 0,  -- For videos

    -- Engagement
    notes TEXT,
    bookmarked BOOLEAN DEFAULT FALSE,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY unique_progress (enrollment_id, lesson_id),
    INDEX idx_enrollment (enrollment_id)
);
```

### 3.3 Live Sessions & Consultations

```sql
CREATE TABLE live_sessions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    product_id BIGINT REFERENCES products(id),
    vendor_id BIGINT REFERENCES vendors(id),

    -- Session Info
    title VARCHAR(200) NOT NULL,
    description TEXT,
    session_type ENUM('webinar', 'workshop', 'consultation', 'q_and_a', 'coaching') NOT NULL,

    -- Scheduling
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    timezone VARCHAR(50) DEFAULT 'UTC',

    -- Capacity
    max_participants INT,
    current_participants INT DEFAULT 0,

    -- Platform
    platform ENUM('zoom', 'google_meet', 'teams', 'custom') DEFAULT 'zoom',
    meeting_url VARCHAR(500),
    meeting_password VARCHAR(50),

    -- Pricing (if separate from product)
    price DECIMAL(10,2),
    currency VARCHAR(3) DEFAULT 'EUR',

    -- Recording
    is_recorded BOOLEAN DEFAULT TRUE,
    recording_url VARCHAR(500),

    -- Status
    status ENUM('scheduled', 'live', 'completed', 'cancelled') DEFAULT 'scheduled',

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_vendor (vendor_id),
    INDEX idx_start_time (start_time),
    INDEX idx_status (status)
);
```

---

## 4. Marketplace Transactions

### 4.1 Purchase & Subscription

```sql
CREATE TABLE user_purchases (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    product_id BIGINT REFERENCES products(id),
    pricing_plan_id BIGINT REFERENCES product_pricing_plans(id),
    vendor_id BIGINT REFERENCES vendors(id),

    -- Transaction
    transaction_id VARCHAR(100) UNIQUE NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    payment_method ENUM('card', 'paypal', 'wallet') NOT NULL,
    payment_provider_ref VARCHAR(255),

    -- Fees
    platform_fee DECIMAL(10,2) NOT NULL,  -- Platform's cut
    vendor_amount DECIMAL(10,2) NOT NULL,  -- Vendor's share
    processing_fee DECIMAL(10,2) DEFAULT 0,  -- Payment processor fee

    -- Subscription
    is_subscription BOOLEAN DEFAULT FALSE,
    subscription_id BIGINT,
    billing_period ENUM('one_time', 'monthly', 'quarterly', 'yearly'),
    next_billing_date DATETIME,

    -- Status
    status ENUM('pending', 'completed', 'refunded', 'disputed') DEFAULT 'pending',
    refund_amount DECIMAL(10,2),
    refund_date DATETIME,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_user (user_id),
    INDEX idx_product (product_id),
    INDEX idx_vendor (vendor_id),
    INDEX idx_status (status)
);

CREATE TABLE product_subscriptions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    product_id BIGINT REFERENCES products(id),
    pricing_plan_id BIGINT REFERENCES product_pricing_plans(id),
    vendor_id BIGINT REFERENCES vendors(id),

    -- Subscription Details
    status ENUM('active', 'paused', 'cancelled', 'expired') DEFAULT 'active',
    current_period_start DATETIME NOT NULL,
    current_period_end DATETIME NOT NULL,

    -- Cancellation
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    cancelled_at DATETIME,
    cancellation_reason TEXT,

    -- Payment
    payment_method_id VARCHAR(255),
    last_payment_date DATETIME,
    next_payment_date DATETIME,
    failed_payments INT DEFAULT 0,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_user (user_id),
    INDEX idx_product (product_id),
    INDEX idx_status (status),
    INDEX idx_next_payment (next_payment_date)
);
```

### 4.2 Revenue Distribution

```python
class RevenueDistributionService:
    """Handle marketplace revenue distribution"""

    def __init__(self, payment_provider):
        self.provider = payment_provider

    def process_purchase(self, purchase: UserPurchase) -> dict:
        """Process purchase and distribute revenue"""
        vendor = purchase.vendor
        product = purchase.product

        # Calculate splits
        platform_rate = vendor.commission_rate / 100  # e.g., 0.20 for 20%
        vendor_rate = 1 - platform_rate

        platform_fee = purchase.amount * platform_rate
        vendor_amount = purchase.amount * vendor_rate

        # Deduct processing fee from platform
        processing_fee = self._calculate_processing_fee(purchase.amount)
        platform_net = platform_fee - processing_fee

        # Update purchase record
        purchase.platform_fee = platform_fee
        purchase.vendor_amount = vendor_amount
        purchase.processing_fee = processing_fee
        purchase.status = 'completed'

        # Create payout record
        payout = VendorPayout(
            vendor_id=vendor.id,
            purchase_id=purchase.id,
            amount=vendor_amount,
            status='pending'
        )

        db.session.add(payout)
        db.session.commit()

        return {
            'purchase_id': purchase.id,
            'total': float(purchase.amount),
            'platform_fee': float(platform_fee),
            'vendor_amount': float(vendor_amount),
            'processing_fee': float(processing_fee)
        }

    def _calculate_processing_fee(self, amount: Decimal) -> Decimal:
        """Calculate payment processor fee (e.g., Stripe 2.9% + 0.30)"""
        return (amount * Decimal('0.029')) + Decimal('0.30')


class VendorPayoutService:
    """Handle vendor payouts"""

    def process_payouts(self, frequency: str = 'weekly'):
        """Process pending payouts for all vendors"""
        # Get vendors with pending payouts
        vendors_with_payouts = db.session.query(
            Vendor.id,
            func.sum(VendorPayout.amount).label('total')
        ).join(VendorPayout).filter(
            VendorPayout.status == 'pending'
        ).group_by(Vendor.id).all()

        for vendor_id, total in vendors_with_payouts:
            if total >= Decimal('50.00'):  # Minimum payout threshold
                self._process_vendor_payout(vendor_id, total)

    def _process_vendor_payout(self, vendor_id: int, amount: Decimal):
        """Process payout for a single vendor"""
        vendor = Vendor.query.get(vendor_id)

        if vendor.payout_method == 'stripe_connect':
            # Use Stripe Connect for instant payouts
            transfer = stripe.Transfer.create(
                amount=int(amount * 100),  # cents
                currency=vendor.currency,
                destination=vendor.stripe_account_id,
            )
            payout_ref = transfer.id
        elif vendor.payout_method == 'paypal':
            # PayPal Payouts API
            payout_ref = self._paypal_payout(vendor, amount)
        else:
            # Manual bank transfer
            payout_ref = self._create_bank_transfer(vendor, amount)

        # Update payout records
        VendorPayout.query.filter(
            VendorPayout.vendor_id == vendor_id,
            VendorPayout.status == 'pending'
        ).update({
            'status': 'processed',
            'payout_ref': payout_ref,
            'processed_at': datetime.utcnow()
        })

        db.session.commit()
```

---

## 5. Discovery & Search

### 5.1 Search Service

```python
from elasticsearch import Elasticsearch

class ProductSearchService:
    """Elasticsearch-powered product search"""

    def __init__(self):
        self.es = Elasticsearch([ELASTICSEARCH_URL])
        self.index = 'products'

    def search(
        self,
        query: str = None,
        category: str = None,
        product_type: str = None,
        price_min: float = None,
        price_max: float = None,
        rating_min: float = None,
        vendor_id: int = None,
        sort_by: str = 'relevance',
        page: int = 1,
        limit: int = 20
    ) -> dict:
        """Search products with filters"""
        must = []
        filter_clauses = []

        # Full-text search
        if query:
            must.append({
                'multi_match': {
                    'query': query,
                    'fields': ['name^3', 'short_description^2', 'description', 'tags'],
                    'fuzziness': 'AUTO'
                }
            })

        # Filters
        filter_clauses.append({'term': {'status': 'published'}})

        if category:
            filter_clauses.append({'term': {'category_slug': category}})

        if product_type:
            filter_clauses.append({'term': {'product_type': product_type}})

        if price_min is not None or price_max is not None:
            price_range = {}
            if price_min is not None:
                price_range['gte'] = price_min
            if price_max is not None:
                price_range['lte'] = price_max
            filter_clauses.append({'range': {'base_price': price_range}})

        if rating_min is not None:
            filter_clauses.append({'range': {'average_rating': {'gte': rating_min}}})

        if vendor_id:
            filter_clauses.append({'term': {'vendor_id': vendor_id}})

        # Build query
        body = {
            'query': {
                'bool': {
                    'must': must or [{'match_all': {}}],
                    'filter': filter_clauses
                }
            },
            'from': (page - 1) * limit,
            'size': limit
        }

        # Sorting
        sort_options = {
            'relevance': ['_score'],
            'newest': [{'created_at': 'desc'}],
            'price_low': [{'base_price': 'asc'}],
            'price_high': [{'base_price': 'desc'}],
            'rating': [{'average_rating': 'desc'}],
            'popular': [{'total_sales': 'desc'}]
        }
        body['sort'] = sort_options.get(sort_by, ['_score'])

        # Execute search
        result = self.es.search(index=self.index, body=body)

        return {
            'products': [hit['_source'] for hit in result['hits']['hits']],
            'total': result['hits']['total']['value'],
            'page': page,
            'limit': limit
        }

    def get_recommendations(self, user_id: int, limit: int = 10) -> list:
        """Get personalized product recommendations"""
        # Get user's purchase history
        purchases = UserPurchase.query.filter_by(user_id=user_id).all()
        purchased_ids = [p.product_id for p in purchases]
        categories = [p.product.category_id for p in purchases]

        # More Like This query
        body = {
            'query': {
                'bool': {
                    'must': {
                        'terms': {'category_id': list(set(categories))}
                    },
                    'must_not': {
                        'ids': {'values': [str(id) for id in purchased_ids]}
                    },
                    'filter': {'term': {'status': 'published'}}
                }
            },
            'size': limit,
            'sort': [{'average_rating': 'desc'}, {'total_sales': 'desc'}]
        }

        result = self.es.search(index=self.index, body=body)
        return [hit['_source'] for hit in result['hits']['hits']]
```

### 5.2 Featured & Trending

```python
class FeaturedProductsService:
    """Manage featured and trending products"""

    @staticmethod
    def get_featured(limit: int = 10) -> list:
        """Get featured products"""
        now = datetime.utcnow()
        return Product.query.filter(
            Product.featured == True,
            Product.featured_until > now,
            Product.status == 'published'
        ).order_by(Product.average_rating.desc()).limit(limit).all()

    @staticmethod
    def get_trending(period_days: int = 7, limit: int = 10) -> list:
        """Get trending products based on recent sales"""
        since = datetime.utcnow() - timedelta(days=period_days)

        trending = db.session.query(
            Product,
            func.count(UserPurchase.id).label('recent_sales')
        ).join(UserPurchase).filter(
            UserPurchase.created_at >= since,
            Product.status == 'published'
        ).group_by(Product.id).order_by(
            desc('recent_sales')
        ).limit(limit).all()

        return [product for product, _ in trending]

    @staticmethod
    def get_new_releases(limit: int = 10) -> list:
        """Get recently published products"""
        return Product.query.filter(
            Product.status == 'published'
        ).order_by(Product.published_at.desc()).limit(limit).all()

    @staticmethod
    def get_top_rated(min_reviews: int = 5, limit: int = 10) -> list:
        """Get top-rated products with minimum reviews"""
        return Product.query.filter(
            Product.status == 'published',
            Product.total_reviews >= min_reviews
        ).order_by(Product.average_rating.desc()).limit(limit).all()
```

---

## 6. Reviews & Ratings

### 6.1 Review System

```sql
CREATE TABLE product_reviews (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    product_id BIGINT REFERENCES products(id) ON DELETE CASCADE,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    purchase_id BIGINT REFERENCES user_purchases(id),

    -- Rating
    rating INT NOT NULL CHECK (rating >= 1 AND rating <= 5),

    -- Review Content
    title VARCHAR(200),
    content TEXT,

    -- For courses: detailed ratings
    content_rating INT,
    instructor_rating INT,
    value_rating INT,

    -- Engagement
    helpful_count INT DEFAULT 0,
    reported_count INT DEFAULT 0,

    -- Vendor Response
    vendor_response TEXT,
    vendor_response_at DATETIME,

    -- Status
    status ENUM('pending', 'published', 'hidden', 'removed') DEFAULT 'pending',
    is_verified_purchase BOOLEAN DEFAULT FALSE,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY unique_review (product_id, user_id),
    INDEX idx_product (product_id),
    INDEX idx_rating (rating),
    INDEX idx_status (status)
);

CREATE TABLE review_helpful_votes (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    review_id BIGINT REFERENCES product_reviews(id) ON DELETE CASCADE,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    is_helpful BOOLEAN NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    UNIQUE KEY unique_vote (review_id, user_id)
);
```

### 6.2 Review Service

```python
class ReviewService:
    """Manage product reviews"""

    @staticmethod
    def create_review(
        user_id: int,
        product_id: int,
        rating: int,
        title: str = None,
        content: str = None
    ) -> ProductReview:
        """Create a new review"""
        # Verify purchase
        purchase = UserPurchase.query.filter_by(
            user_id=user_id,
            product_id=product_id,
            status='completed'
        ).first()

        if not purchase:
            raise ValueError("Must purchase product before reviewing")

        # Check for existing review
        existing = ProductReview.query.filter_by(
            user_id=user_id,
            product_id=product_id
        ).first()

        if existing:
            raise ValueError("Already reviewed this product")

        review = ProductReview(
            product_id=product_id,
            user_id=user_id,
            purchase_id=purchase.id,
            rating=rating,
            title=title,
            content=content,
            is_verified_purchase=True,
            status='published'  # Or 'pending' for moderation
        )

        db.session.add(review)

        # Update product average rating
        ReviewService._update_product_rating(product_id)

        db.session.commit()
        return review

    @staticmethod
    def _update_product_rating(product_id: int):
        """Recalculate product average rating"""
        result = db.session.query(
            func.avg(ProductReview.rating),
            func.count(ProductReview.id)
        ).filter(
            ProductReview.product_id == product_id,
            ProductReview.status == 'published'
        ).first()

        avg_rating, total_reviews = result

        Product.query.filter_by(id=product_id).update({
            'average_rating': avg_rating or 0,
            'total_reviews': total_reviews or 0
        })
```

---

## 7. Vendor Portal

### 7.1 Vendor Dashboard API

```python
class VendorDashboardService:
    """Analytics and management for vendors"""

    def get_dashboard_stats(self, vendor_id: int, period_days: int = 30) -> dict:
        """Get vendor dashboard statistics"""
        since = datetime.utcnow() - timedelta(days=period_days)

        # Revenue
        revenue = db.session.query(
            func.sum(UserPurchase.vendor_amount)
        ).filter(
            UserPurchase.vendor_id == vendor_id,
            UserPurchase.status == 'completed',
            UserPurchase.created_at >= since
        ).scalar() or 0

        # Sales count
        sales_count = UserPurchase.query.filter(
            UserPurchase.vendor_id == vendor_id,
            UserPurchase.status == 'completed',
            UserPurchase.created_at >= since
        ).count()

        # Active subscribers
        active_subs = ProductSubscription.query.filter(
            ProductSubscription.vendor_id == vendor_id,
            ProductSubscription.status == 'active'
        ).count()

        # New customers
        new_customers = db.session.query(
            func.count(func.distinct(UserPurchase.user_id))
        ).filter(
            UserPurchase.vendor_id == vendor_id,
            UserPurchase.created_at >= since
        ).scalar() or 0

        # Reviews
        reviews = ProductReview.query.join(Product).filter(
            Product.vendor_id == vendor_id,
            ProductReview.created_at >= since
        ).count()

        # Top products
        top_products = db.session.query(
            Product,
            func.count(UserPurchase.id).label('sales')
        ).join(UserPurchase).filter(
            Product.vendor_id == vendor_id,
            UserPurchase.created_at >= since
        ).group_by(Product.id).order_by(
            desc('sales')
        ).limit(5).all()

        return {
            'period_days': period_days,
            'revenue': float(revenue),
            'sales_count': sales_count,
            'active_subscribers': active_subs,
            'new_customers': new_customers,
            'new_reviews': reviews,
            'top_products': [
                {'product': p.to_dict(), 'sales': s}
                for p, s in top_products
            ]
        }

    def get_revenue_chart(self, vendor_id: int, period_days: int = 30) -> list:
        """Get daily revenue for chart"""
        since = datetime.utcnow() - timedelta(days=period_days)

        daily_revenue = db.session.query(
            func.date(UserPurchase.created_at).label('date'),
            func.sum(UserPurchase.vendor_amount).label('revenue')
        ).filter(
            UserPurchase.vendor_id == vendor_id,
            UserPurchase.status == 'completed',
            UserPurchase.created_at >= since
        ).group_by(
            func.date(UserPurchase.created_at)
        ).order_by('date').all()

        return [{'date': str(d), 'revenue': float(r)} for d, r in daily_revenue]
```

---

## 8. Affiliate Program

### 8.1 Affiliate Model

```sql
CREATE TABLE affiliates (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT UNIQUE REFERENCES users(id),

    -- Affiliate Info
    affiliate_code VARCHAR(50) UNIQUE NOT NULL,
    commission_rate DECIMAL(5,2) DEFAULT 10.00,  -- Percentage

    -- Payment
    payout_method ENUM('bank_transfer', 'paypal') DEFAULT 'paypal',
    payout_details JSON,

    -- Stats
    total_referrals INT DEFAULT 0,
    total_earnings DECIMAL(12,2) DEFAULT 0,
    pending_earnings DECIMAL(12,2) DEFAULT 0,

    -- Status
    status ENUM('pending', 'active', 'suspended') DEFAULT 'pending',

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_code (affiliate_code),
    INDEX idx_user (user_id)
);

CREATE TABLE affiliate_referrals (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    affiliate_id BIGINT REFERENCES affiliates(id),
    referred_user_id BIGINT REFERENCES users(id),
    purchase_id BIGINT REFERENCES user_purchases(id),

    -- Commission
    purchase_amount DECIMAL(10,2) NOT NULL,
    commission_amount DECIMAL(10,2) NOT NULL,
    commission_rate DECIMAL(5,2) NOT NULL,

    -- Status
    status ENUM('pending', 'approved', 'paid', 'rejected') DEFAULT 'pending',
    paid_at DATETIME,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_affiliate (affiliate_id),
    INDEX idx_status (status)
);
```

---

## 9. API Endpoints

### 9.1 Public Marketplace API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/marketplace/products` | Search/list products |
| GET | `/api/v1/marketplace/products/:slug` | Get product details |
| GET | `/api/v1/marketplace/categories` | List categories |
| GET | `/api/v1/marketplace/vendors/:code` | Get vendor profile |
| GET | `/api/v1/marketplace/featured` | Get featured products |
| GET | `/api/v1/marketplace/trending` | Get trending products |

### 9.2 User API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/purchases` | Purchase product |
| GET | `/api/v1/purchases` | List user purchases |
| GET | `/api/v1/library` | User's product library |
| POST | `/api/v1/reviews` | Create review |
| GET | `/api/v1/enrollments` | Course enrollments |
| PUT | `/api/v1/lessons/:id/progress` | Update lesson progress |

### 9.3 Vendor API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/vendor/dashboard` | Dashboard stats |
| POST | `/api/v1/vendor/products` | Create product |
| PUT | `/api/v1/vendor/products/:id` | Update product |
| GET | `/api/v1/vendor/sales` | List sales |
| GET | `/api/v1/vendor/payouts` | List payouts |
| POST | `/api/v1/vendor/courses/:id/sections` | Add course section |

---

## 10. Implementation Roadmap

### Phase 1: Vendor Foundation (4 weeks)
- [ ] Vendor registration & verification
- [ ] Product listing CRUD
- [ ] Basic pricing plans

### Phase 2: Marketplace Core (4 weeks)
- [ ] Category system
- [ ] Search & filtering
- [ ] Product discovery pages

### Phase 3: Transactions (3 weeks)
- [ ] Purchase flow
- [ ] Revenue splitting
- [ ] Vendor payouts

### Phase 4: Education Features (4 weeks)
- [ ] Course structure (sections, lessons)
- [ ] Video hosting integration
- [ ] Progress tracking
- [ ] Certificates

### Phase 5: Engagement (3 weeks)
- [ ] Reviews & ratings
- [ ] Recommendations
- [ ] Affiliate program

### Phase 6: Analytics (2 weeks)
- [ ] Vendor analytics dashboard
- [ ] Platform analytics
- [ ] Reporting tools

---

## 11. Revenue Model

### 11.1 Platform Revenue Streams

| Stream | Rate | Description |
|--------|------|-------------|
| Transaction Fee | 20% | Commission on every sale |
| Featured Listings | $99-499/mo | Promoted visibility |
| Vendor Subscription | $49-299/mo | Premium vendor features |
| Processing Fee Pass-through | 2.9% + $0.30 | Payment processor fees |

### 11.2 Projected Economics

For a $100 product sale:
- **Customer pays:** $100
- **Processing fee:** $3.20 (passed to platform)
- **Platform commission:** $20 (20%)
- **Vendor receives:** $76.80

---

## Related Documentation

- [SaaS Architecture](./README_SAAS.md)
- [Backend Architecture](./architecture_backend/README.md)
- [Payment Architecture](./architecture_backend/payment-architecture.md)
- [Booking & Ticket System](./architecture_backend/booking-ticket-system.md)
