import streamlit as st
import sqlite3
import hashlib
from datetime import datetime


# ============================================================
# PAGE SETTINGS
# ============================================================

st.set_page_config(
    page_title="CS Clothing Store",
    page_icon="👗",
    layout="wide"
)


# ============================================================
# DATABASE
# ============================================================

DB_NAME = "store.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def init_database():
    conn = get_connection()
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)

    # Products table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            inventory INTEGER NOT NULL,
            image TEXT,
            description TEXT
        )
    """)

    # Orders table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            total REAL NOT NULL,
            order_date TEXT NOT NULL,
            payment_status TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Order items table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)

    # ========================================================
    # ALWAYS MAKE SURE THE ADMIN ACCOUNT IS CORRECT
    # Username: admin
    # Password: admin123
    # ========================================================

    admin_password = hash_password("admin123")

    cursor.execute(
        "SELECT id FROM users WHERE username = ?",
        ("admin",)
    )

    admin = cursor.fetchone()

    if admin:
        cursor.execute(
            """
            UPDATE users
            SET password = ?, role = ?
            WHERE username = ?
            """,
            (admin_password, "admin", "admin")
        )
    else:
        cursor.execute(
            """
            INSERT INTO users (username, password, role)
            VALUES (?, ?, ?)
            """,
            ("admin", admin_password, "admin")
        )

    # ========================================================
    # ADD SAMPLE PRODUCTS IF THERE ARE NO PRODUCTS
    # ========================================================

    cursor.execute("SELECT COUNT(*) FROM products")
    product_count = cursor.fetchone()[0]

    if product_count == 0:

        products = [
            (
                "Classic White T-Shirt",
                25.00,
                20,
                "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab",
                "A simple and comfortable white T-shirt."
            ),
            (
                "Denim Jacket",
                55.00,
                15,
                "https://images.unsplash.com/photo-1551028719-00167b16eac5",
                "A stylish denim jacket for everyday wear."
            ),
            (
                "Black Dress",
                60.00,
                10,
                "https://images.unsplash.com/photo-1566174053879-31528523f8ae",
                "A simple and elegant black dress."
            ),
            (
                "Fashion Sneakers",
                70.00,
                12,
                "https://images.unsplash.com/photo-1542291026-7eec264c27ff",
                "Comfortable sneakers for casual outfits."
            )
        ]

        cursor.executemany(
            """
            INSERT INTO products
            (name, price, inventory, image, description)
            VALUES (?, ?, ?, ?, ?)
            """,
            products
        )

    conn.commit()
    conn.close()


# Initialize database
init_database()


# ============================================================
# SESSION STATE
# ============================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "username" not in st.session_state:
    st.session_state.username = ""

if "role" not in st.session_state:
    st.session_state.role = ""

if "cart" not in st.session_state:
    st.session_state.cart = {}


# ============================================================
# LOGIN FUNCTION
# ============================================================

def login_user(username, password):

    conn = get_connection()
    cursor = conn.cursor()

    password_hash = hash_password(password)

    cursor.execute(
        """
        SELECT id, username, role
        FROM users
        WHERE username = ? AND password = ?
        """,
        (username, password_hash)
    )

    user = cursor.fetchone()

    conn.close()

    if user:
        st.session_state.logged_in = True
        st.session_state.user_id = user[0]
        st.session_state.username = user[1]
        st.session_state.role = user[2]
        return True

    return False


# ============================================================
# LOGOUT
# ============================================================

def logout():
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.username = ""
    st.session_state.role = ""
    st.session_state.cart = {}
    st.rerun()


# ============================================================
# HEADER
# ============================================================

st.title("👗 CS Clothing Store")
st.write("Welcome to our online clothing store!")


# ============================================================
# NOT LOGGED IN
# ============================================================

if not st.session_state.logged_in:

    login_tab, register_tab = st.tabs(
        ["🔐 Login", "📝 Customer Registration"]
    )

    # ========================================================
    # LOGIN
    # ========================================================

    with login_tab:

        st.header("Login")

        username = st.text_input(
            "Username",
            key="login_username"
        )

        password = st.text_input(
            "Password",
            type="password",
            key="login_password"
        )

        if st.button(
            "Login",
            use_container_width=True
        ):

            if username.strip() == "" or password.strip() == "":
                st.error("Please enter both username and password.")

            elif login_user(username, password):
                st.success("Login successful!")
                st.rerun()

            else:
                st.error("Incorrect username or password.")

        st.info(
            "Demo Admin Login: username = admin, password = admin123"
        )

    # ========================================================
    # CUSTOMER REGISTRATION
    # ========================================================

    with register_tab:

        st.header("Create Customer Account")

        new_username = st.text_input(
            "Choose a username",
            key="register_username"
        )

        new_password = st.text_input(
            "Choose a password",
            type="password",
            key="register_password"
        )

        confirm_password = st.text_input(
            "Confirm password",
            type="password",
            key="confirm_password"
        )

        if st.button(
            "Create Account",
            use_container_width=True
        ):

            if new_username.strip() == "":
                st.error("Please enter a username.")

            elif new_password.strip() == "":
                st.error("Please enter a password.")

            elif new_password != confirm_password:
                st.error("Passwords do not match.")

            elif new_username.lower() == "admin":
                st.error("This username is reserved.")

            else:

                conn = get_connection()
                cursor = conn.cursor()

                cursor.execute(
                    "SELECT id FROM users WHERE username = ?",
                    (new_username,)
                )

                existing_user = cursor.fetchone()

                if existing_user:
                    st.error("Username already exists.")

                else:

                    cursor.execute(
                        """
                        INSERT INTO users
                        (username, password, role)
                        VALUES (?, ?, ?)
                        """,
                        (
                            new_username,
                            hash_password(new_password),
                            "customer"
                        )
                    )

                    conn.commit()

                    st.success(
                        "Account created successfully! "
                        "You can now login."
                    )

                conn.close()


# ============================================================
# LOGGED IN
# ============================================================

else:

    # ========================================================
    # SIDEBAR
    # ========================================================

    st.sidebar.success(
        "Logged in as: " + st.session_state.username
    )

    st.sidebar.write(
        "Role: " + st.session_state.role.title()
    )

    if st.sidebar.button(
        "🚪 Logout",
        use_container_width=True
    ):
        logout()

    # ========================================================
    # ADMIN DASHBOARD
    # ========================================================

    if st.session_state.role == "admin":

        st.header("👑 Admin Dashboard")

        admin_tabs = st.tabs(
            [
                "📦 Products & Inventory",
                "➕ Add Product",
                "📋 Orders"
            ]
        )

        # ====================================================
        # PRODUCTS AND INVENTORY
        # ====================================================

        with admin_tabs[0]:

            st.subheader("Manage Products & Inventory")

            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT id, name, price, inventory, image, description
                FROM products
                ORDER BY id
                """
            )

            products = cursor.fetchall()

            conn.close()

            if not products:
                st.info("No products available.")

            for product in products:

                product_id = product[0]
                product_name = product[1]
                product_price = product[2]
                product_inventory = product[3]
                product_image = product[4] or ""
                product_description = product[5] or ""

                with st.expander(
                    f"{product_name} | ${product_price:.2f} | "
                    f"Inventory: {product_inventory}"
                ):

                    edit_name = st.text_input(
                        "Product Name",
                        value=product_name,
                        key=f"name_{product_id}"
                    )

                    edit_price = st.number_input(
                        "Price",
                        min_value=0.0,
                        value=float(product_price),
                        step=1.0,
                        key=f"price_{product_id}"
                    )

                    edit_inventory = st.number_input(
                        "Inventory",
                        min_value=0,
                        value=int(product_inventory),
                        step=1,
                        key=f"inventory_{product_id}"
                    )

                    edit_image = st.text_input(
                        "Image URL",
                        value=product_image,
                        key=f"image_{product_id}"
                    )

                    edit_description = st.text_area(
                        "Description",
                        value=product_description,
                        key=f"description_{product_id}"
                    )

                    col1, col2 = st.columns(2)

                    with col1:

                        if st.button(
                            "💾 Save Changes",
                            key=f"save_{product_id}",
                            use_container_width=True
                        ):

                            conn = get_connection()
                            cursor = conn.cursor()

                            cursor.execute(
                                """
                                UPDATE products
                                SET name = ?,
                                    price = ?,
                                    inventory = ?,
                                    image = ?,
                                    description = ?
                                WHERE id = ?
                                """,
                                (
                                    edit_name,
                                    edit_price,
                                    edit_inventory,
                                    edit_image,
                                    edit_description,
                                    product_id
                                )
                            )

                            conn.commit()
                            conn.close()

                            st.success("Product updated!")
                            st.rerun()

                    with col2:

                        if st.button(
                            "🗑️ Delete Product",
                            key=f"delete_{product_id}",
                            use_container_width=True
                        ):

                            conn = get_connection()
                            cursor = conn.cursor()

                            cursor.execute(
                                """
                                DELETE FROM products
                                WHERE id = ?
                                """,
                                (product_id,)
                            )

                            conn.commit()
                            conn.close()

                            st.success("Product deleted!")
                            st.rerun()

        # ====================================================
        # ADD PRODUCT
        # ====================================================

        with admin_tabs[1]:

            st.subheader("Add New Product")

            new_product_name = st.text_input(
                "Product Name",
                key="new_product_name"
            )

            new_product_price = st.number_input(
                "Price",
                min_value=0.0,
                value=25.0,
                step=1.0,
                key="new_product_price"
            )

            new_product_inventory = st.number_input(
                "Inventory Quantity",
                min_value=0,
                value=10,
                step=1,
                key="new_product_inventory"
            )

            new_product_image = st.text_input(
                "Image URL",
                key="new_product_image"
            )

            new_product_description = st.text_area(
                "Description",
                key="new_product_description"
            )

            if st.button(
                "➕ Add Product",
                use_container_width=True
            ):

                if new_product_name.strip() == "":
                    st.error("Please enter a product name.")

                else:

                    conn = get_connection()
                    cursor = conn.cursor()

                    cursor.execute(
                        """
                        INSERT INTO products
                        (name, price, inventory, image, description)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            new_product_name,
                            new_product_price,
                            new_product_inventory,
                            new_product_image,
                            new_product_description
                        )
                    )

                    conn.commit()
                    conn.close()

                    st.success(
                        "Product added successfully!"
                    )

                    st.rerun()

        # ====================================================
        # ADMIN ORDERS
        # ====================================================

        with admin_tabs[2]:

            st.subheader("All Customer Orders")

            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT
                    orders.id,
                    users.username,
                    orders.total,
                    orders.order_date,
                    orders.payment_status
                FROM orders
                JOIN users
                    ON orders.user_id = users.id
                ORDER BY orders.id DESC
                """
            )

            orders = cursor.fetchall()

            conn.close()

            if not orders:
                st.info("No orders have been placed yet.")

            else:

                for order in orders:

                    order_id = order[0]
                    customer = order[1]
                    total = order[2]
                    order_date = order[3]
                    payment_status = order[4]

                    with st.expander(
                        f"Order #{order_id} | "
                        f"{customer} | "
                        f"${total:.2f}"
                    ):

                        st.write(
                            "Date: " + str(order_date)
                        )

                        st.write(
                            "Payment: " + str(payment_status)
                        )

                        conn = get_connection()
                        cursor = conn.cursor()

                        cursor.execute(
                            """
                            SELECT
                                products.name,
                                order_items.quantity,
                                order_items.price
                            FROM order_items
                            JOIN products
                                ON order_items.product_id = products.id
                            WHERE order_items.order_id = ?
                            """,
                            (order_id,)
                        )

                        items = cursor.fetchall()

                        conn.close()

                        for item in items:

                            st.write(
                                f"- {item[0]} | "
                                f"Quantity: {item[1]} | "
                                f"Price: ${item[2]:.2f}"
                            )

    # ========================================================
    # CUSTOMER
    # ========================================================

    else:

        st.header("🛍️ Customer Store")

        customer_tabs = st.tabs(
            [
                "🛍️ Shop",
                "🛒 Shopping Cart",
                "📜 Order History"
            ]
        )

        # ====================================================
        # SHOP
        # ====================================================

        with customer_tabs[0]:

            st.subheader("Available Products")

            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT
                    id,
                    name,
                    price,
                    inventory,
                    image,
                    description
                FROM products
                ORDER BY id
                """
            )

            products = cursor.fetchall()

            conn.close()

            if not products:
                st.info("No products are currently available.")

            for product in products:

                product_id = product[0]
                product_name = product[1]
                product_price = product[2]
                product_inventory = product[3]
                product_image = product[4]
                product_description = product[5]

                col1, col2 = st.columns(
                    [1, 2]
                )

                with col1:

                    if product_image:
                        try:
                            st.image(
                                product_image,
                                use_container_width=True
                            )
                        except:
                            st.write("Image unavailable.")

                with col2:

                    st.subheader(product_name)

                    st.write(product_description)

                    st.write(
                        f"### ${product_price:.2f}"
                    )

                    st.write(
                        f"Available inventory: "
                        f"{product_inventory}"
                    )

                    if product_inventory > 0:

                        quantity = st.number_input(
                            "Quantity",
                            min_value=1,
                            max_value=product_inventory,
                            value=1,
                            step=1,
                            key=f"quantity_{product_id}"
                        )

                        if st.button(
                            "🛒 Add to Cart",
                            key=f"add_{product_id}",
                            use_container_width=True
                        ):

                            if product_id in st.session_state.cart:

                                current_quantity = (
                                    st.session_state.cart[
                                        product_id
                                    ]["quantity"]
                                )

                                new_quantity = (
                                    current_quantity + quantity
                                )

                                if new_quantity <= product_inventory:

                                    st.session_state.cart[
                                        product_id
                                    ]["quantity"] = new_quantity

                                    st.success(
                                        "Product added to cart!"
                                    )

                                else:

                                    st.error(
                                        "Not enough inventory."
                                    )

                            else:

                                st.session_state.cart[
                                    product_id
                                ] = {
                                    "name": product_name,
                                    "price": product_price,
                                    "quantity": quantity
                                }

                                st.success(
                                    "Product added to cart!"
                                )

                    else:

                        st.error("Out of stock.")

                st.divider()

        # ====================================================
        # SHOPPING CART
        # ====================================================

        with customer_tabs[1]:

            st.subheader("🛒 Your Shopping Cart")

            if not st.session_state.cart:

                st.info("Your shopping cart is empty.")

            else:

                total = 0.0

                for product_id in list(
                    st.session_state.cart.keys()
                ):

                    item = st.session_state.cart[
                        product_id
                    ]

                    item_total = (
                        item["price"] * item["quantity"]
                    )

                    total += item_total

                    col1, col2, col3, col4 = st.columns(
                        [3, 1, 1, 1]
                    )

                    with col1:
                        st.write(
                            f"**{item['name']}**"
                        )

                    with col2:
                        st.write(
                            f"${item['price']:.2f}"
                        )

                    with col3:
                        st.write(
                            f"Qty: {item['quantity']}"
                        )

                    with col4:

                        if st.button(
                            "Remove",
                            key=f"remove_{product_id}"
                        ):

                            del st.session_state.cart[
                                product_id
                            ]

                            st.rerun()

                st.divider()

                st.subheader(
                    f"Total: ${total:.2f}"
                )

                # =================================================
                # CHECKOUT
                # =================================================

                st.markdown("### 💳 Checkout")

                payment_method = st.selectbox(
                    "Payment Method",
                    [
                        "Credit Card (Demo)",
                        "PayPal (Demo)"
                    ]
                )

                st.info(
                    "This is a school-project demo payment. "
                    "No real money is charged."
                )

                if st.button(
                    "💳 Complete Payment & Place Order",
                    use_container_width=True
                ):

                    conn = get_connection()
                    cursor = conn.cursor()

                    # ---------------------------------------------
                    # Check inventory again before completing order
                    # ---------------------------------------------

                    inventory_problem = False

                    for product_id in st.session_state.cart:

                        quantity = st.session_state.cart[
                            product_id
                        ]["quantity"]

                        cursor.execute(
                            """
                            SELECT inventory
                            FROM products
                            WHERE id = ?
                            """,
                            (product_id,)
                        )

                        result = cursor.fetchone()

                        if result is None:
                            inventory_problem = True
                            break

                        current_inventory = result[0]

                        if quantity > current_inventory:
                            inventory_problem = True
                            break

                    if inventory_problem:

                        conn.close()

                        st.error(
                            "There is not enough inventory "
                            "for one or more products."
                        )

                    else:

                        # -----------------------------------------
                        # Create order
                        # -----------------------------------------

                        order_date = datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )

                        cursor.execute(
                            """
                            INSERT INTO orders
                            (
                                user_id,
                                total,
                                order_date,
                                payment_status
                            )
                            VALUES (?, ?, ?, ?)
                            """,
                            (
                                st.session_state.user_id,
                                total,
                                order_date,
                                "Paid - Demo"
                            )
                        )

                        order_id = cursor.lastrowid

                        # -----------------------------------------
                        # Add order items
                        # -----------------------------------------

                        for product_id in st.session_state.cart:

                            item = st.session_state.cart[
                                product_id
                            ]

                            quantity = item["quantity"]
                            price = item["price"]

                            cursor.execute(
                                """
                                INSERT INTO order_items
                                (
                                    order_id,
                                    product_id,
                                    quantity,
                                    price
                                )
                                VALUES (?, ?, ?, ?)
                                """,
                                (
                                    order_id,
                                    product_id,
                                    quantity,
                                    price
                                )
                            )

                            # -------------------------------------
                            # Deduct inventory
                            # -------------------------------------

                            cursor.execute(
                                """
                                UPDATE products
                                SET inventory = inventory - ?
                                WHERE id = ?
                                """,
                                (
                                    quantity,
                                    product_id
                                )
                            )

                        conn.commit()
                        conn.close()

                        # Clear shopping cart
                        st.session_state.cart = {}

                        st.success(
                            "🎉 Payment successful! "
                            f"Your order #{order_id} has been placed."
                        )

                        st.rerun()

        # ====================================================
        # ORDER HISTORY
        # ====================================================

        with customer_tabs[2]:

            st.subheader("📜 Your Order History")

            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT
                    id,
                    total,
                    order_date,
                    payment_status
                FROM orders
                WHERE user_id = ?
                ORDER BY id DESC
                """,
                (st.session_state.user_id,)
            )

            orders = cursor.fetchall()

            conn.close()

            if not orders:

                st.info(
                    "You have not placed any orders yet."
                )

            else:

                for order in orders:

                    order_id = order[0]
                    total = order[1]
                    order_date = order[2]
                    payment_status = order[3]

                    with st.expander(
                        f"Order #{order_id} | "
                        f"${total:.2f} | "
                        f"{order_date}"
                    ):

                        st.write(
                            "Payment Status: "
                            + payment_status
                        )

                        conn = get_connection()
                        cursor = conn.cursor()

                        cursor.execute(
                            """
                            SELECT
                                products.name,
                                order_items.quantity,
                                order_items.price
                            FROM order_items
                            JOIN products
                                ON order_items.product_id =
                                   products.id
                            WHERE order_items.order_id = ?
                            """,
                            (order_id,)
                        )

                        items = cursor.fetchall()

                        conn.close()

                        st.write("Items:")

                        for item in items:

                            st.write(
                                f"- {item[0]} | "
                                f"Quantity: {item[1]} | "
                                f"${item[2]:.2f}"
                            )
