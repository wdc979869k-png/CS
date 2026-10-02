import streamlit as st
import sqlite3
import hashlib
from datetime import datetime

# =========================================================
# PAGE SETTINGS
# =========================================================

st.set_page_config(
    page_title="CS Clothing Store",
    page_icon="👗",
    layout="wide"
)

DB_NAME = "store.db"


# =========================================================
# DATABASE
# =========================================================

def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)


def create_database():
    conn = get_connection()
    cursor = conn.cursor()

    # Users
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)

    # Products
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            inventory INTEGER NOT NULL,
            image TEXT NOT NULL,
            description TEXT
        )
    """)

    # Orders
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            total REAL NOT NULL,
            order_date TEXT NOT NULL,
            payment_status TEXT NOT NULL
        )
    """)

    # Order items
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL
        )
    """)

    # Create default admin account
    admin_password = hashlib.sha256(
        "admin123".encode()
    ).hexdigest()

    cursor.execute(
        "SELECT * FROM users WHERE username = ?",
        ("admin",)
    )

    if cursor.fetchone() is None:
        cursor.execute(
            """
            INSERT INTO users (username, password, role)
            VALUES (?, ?, ?)
            """,
            ("admin", admin_password, "admin")
        )

    # Create sample products if there are no products
    cursor.execute("SELECT COUNT(*) FROM products")
    product_count = cursor.fetchone()[0]

    if product_count == 0:

        sample_products = [
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
                "https://images.unsplash.com/photo-1595777457583-95e059d581b8",
                "A simple and elegant black dress."
            ),
            (
                "Fashion Sneakers",
                70.00,
                12,
                "https://images.unsplash.com/photo-1542291026-7eec264c27ff",
                "Comfortable sneakers for everyday use."
            )
        ]

        cursor.executemany(
            """
            INSERT INTO products
            (name, price, inventory, image, description)
            VALUES (?, ?, ?, ?, ?)
            """,
            sample_products
        )

    conn.commit()
    conn.close()


create_database()


# =========================================================
# PASSWORD
# =========================================================

def hash_password(password):
    return hashlib.sha256(
        password.encode()
    ).hexdigest()


# =========================================================
# LOGIN
# =========================================================

def login_user(username, password):

    conn = get_connection()
    cursor = conn.cursor()

    hashed_password = hash_password(password)

    cursor.execute(
        """
        SELECT id, username, role
        FROM users
        WHERE username = ? AND password = ?
        """,
        (username, hashed_password)
    )

    user = cursor.fetchone()

    conn.close()

    return user


# =========================================================
# SESSION STATE
# =========================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "username" not in st.session_state:
    st.session_state.username = None

if "role" not in st.session_state:
    st.session_state.role = None

if "cart" not in st.session_state:
    st.session_state.cart = {}


# =========================================================
# LOGOUT
# =========================================================

def logout():
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.username = None
    st.session_state.role = None
    st.session_state.cart = {}


# =========================================================
# LOGIN / REGISTER PAGE
# =========================================================

if not st.session_state.logged_in:

    st.title("👗 CS Clothing Store")

    st.write(
        "Welcome to our online clothing store!"
    )

    login_tab, register_tab = st.tabs(
        ["🔐 Login", "📝 Customer Registration"]
    )

    # -----------------------------------------------------
    # LOGIN
    # -----------------------------------------------------

    with login_tab:

        st.subheader("Login")

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

            if username and password:

                user = login_user(
                    username,
                    password
                )

                if user:

                    st.session_state.logged_in = True
                    st.session_state.user_id = user[0]
                    st.session_state.username = user[1]
                    st.session_state.role = user[2]

                    st.success(
                        "Login successful!"
                    )

                    st.rerun()

                else:

                    st.error(
                        "Incorrect username or password."
                    )

            else:

                st.warning(
                    "Please enter your username and password."
                )

        st.info(
            "Demo Admin Login: username = admin, "
            "password = admin123"
        )

    # -----------------------------------------------------
    # CUSTOMER REGISTRATION
    # -----------------------------------------------------

    with register_tab:

        st.subheader(
            "Create a Customer Account"
        )

        new_username = st.text_input(
            "Choose a username",
            key="new_username"
        )

        new_password = st.text_input(
            "Choose a password",
            type="password",
            key="new_password"
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

            if not new_username or not new_password:

                st.warning(
                    "Please complete all fields."
                )

            elif new_password != confirm_password:

                st.error(
                    "Passwords do not match."
                )

            else:

                conn = get_connection()
                cursor = conn.cursor()

                try:

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
                        "Account created! "
                        "You can now log in."
                    )

                except sqlite3.IntegrityError:

                    st.error(
                        "That username already exists."
                    )

                conn.close()

    st.stop()


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("👗 CS Clothing Store")

st.sidebar.write(
    f"Logged in as: **{st.session_state.username}**"
)

st.sidebar.write(
    f"Account type: **{st.session_state.role.title()}**"
)

st.sidebar.divider()

if st.sidebar.button(
    "🚪 Logout",
    use_container_width=True
):
    logout()
    st.rerun()


# =========================================================
# ADMIN PANEL
# =========================================================

if st.session_state.role == "admin":

    st.title("👑 Admin Dashboard")

    admin_tab1, admin_tab2, admin_tab3 = st.tabs(
        [
            "📦 Products & Inventory",
            "➕ Add Product",
            "📋 Orders"
        ]
    )

    # -----------------------------------------------------
    # PRODUCTS / INVENTORY
    # -----------------------------------------------------

    with admin_tab1:

        st.header(
            "Manage Products & Inventory"
        )

        conn = get_connection()

        products = conn.execute(
            """
            SELECT id, name, price, inventory,
                   image, description
            FROM products
            ORDER BY id
            """
        ).fetchall()

        conn.close()

        if not products:

            st.info("No products found.")

        for product in products:

            product_id = product[0]
            name = product[1]
            price = product[2]
            inventory = product[3]
            image = product[4]
            description = product[5]

            with st.expander(
                f"{name} — ${price:.2f} — Stock: {inventory}"
            ):

                col1, col2 = st.columns([1, 2])

                with col1:

                    st.image(
                        image,
                        use_container_width=True
                    )

                with col2:

                    edited_name = st.text_input(
                        "Product name",
                        value=name,
                        key=f"name_{product_id}"
                    )

                    edited_price = st.number_input(
                        "Price",
                        min_value=0.0,
                        value=float(price),
                        step=1.0,
                        key=f"price_{product_id}"
                    )

                    edited_inventory = st.number_input(
                        "Inventory",
                        min_value=0,
                        value=int(inventory),
                        step=1,
                        key=f"inventory_{product_id}"
                    )

                    edited_image = st.text_input(
                        "Image URL",
                        value=image,
                        key=f"image_{product_id}"
                    )

                    edited_description = st.text_area(
                        "Description",
                        value=description or "",
                        key=f"description_{product_id}"
                    )

                    save_col, delete_col = st.columns(2)

                    with save_col:

                        if st.button(
                            "💾 Save Changes",
                            key=f"save_{product_id}",
                            use_container_width=True
                        ):

                            conn = get_connection()

                            conn.execute(
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
                                    edited_name,
                                    edited_price,
                                    edited_inventory,
                                    edited_image,
                                    edited_description,
                                    product_id
                                )
                            )

                            conn.commit()
                            conn.close()

                            st.success(
                                "Product updated!"
                            )

                            st.rerun()

                    with delete_col:

                        if st.button(
                            "🗑️ Delete",
                            key=f"delete_{product_id}",
                            use_container_width=True
                        ):

                            conn = get_connection()

                            conn.execute(
                                """
                                DELETE FROM products
                                WHERE id = ?
                                """,
                                (product_id,)
                            )

                            conn.commit()
                            conn.close()

                            st.success(
                                "Product deleted."
                            )

                            st.rerun()

    # -----------------------------------------------------
    # ADD PRODUCT
    # -----------------------------------------------------

    with admin_tab2:

        st.header("➕ Add New Product")

        new_name = st.text_input(
            "Product name"
        )

        new_price = st.number_input(
            "Price",
            min_value=0.0,
            value=20.0,
            step=1.0
        )

        new_inventory = st.number_input(
            "Inventory quantity",
            min_value=0,
            value=10,
            step=1
        )

        new_image = st.text_input(
            "Product image URL"
        )

        new_description = st.text_area(
            "Product description"
        )

        if st.button(
            "➕ Add Product",
            use_container_width=True
        ):

            if not new_name or not new_image:

                st.warning(
                    "Please enter a product name "
                    "and image URL."
                )

            else:

                conn = get_connection()

                conn.execute(
                    """
                    INSERT INTO products
                    (name, price, inventory, image, description)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        new_name,
                        new_price,
                        new_inventory,
                        new_image,
                        new_description
                    )
                )

                conn.commit()
                conn.close()

                st.success(
                    "Product added successfully!"
                )

                st.rerun()

    # -----------------------------------------------------
    # ADMIN ORDERS
    # -----------------------------------------------------

    with admin_tab3:

        st.header("📋 Customer Orders")

        conn = get_connection()

        orders = conn.execute(
            """
            SELECT orders.id,
                   users.username,
                   orders.total,
                   orders.order_date,
                   orders.payment_status
            FROM orders
            JOIN users
            ON orders.user_id = users.id
            ORDER BY orders.id DESC
            """
        ).fetchall()

        conn.close()

        if not orders:

            st.info("No orders have been placed yet.")

        else:

            for order in orders:

                st.write(
                    f"**Order #{order[0]}**"
                )

                st.write(
                    f"Customer: {order[1]}"
                )

                st.write(
                    f"Total: ${order[2]:.2f}"
                )

                st.write(
                    f"Date: {order[3]}"
                )

                st.write(
                    f"Payment: {order[4]}"
                )

                st.divider()


# =========================================================
# CUSTOMER STORE
# =========================================================

else:

    st.title("👗 CS Clothing Store")

    st.write(
        f"Welcome, **{st.session_state.username}**!"
    )

    store_tab, cart_tab, history_tab = st.tabs(
        [
            "🛍️ Shop",
            "🛒 Shopping Cart",
            "📋 Order History"
        ]
    )

    # =====================================================
    # SHOP
    # =====================================================

    with store_tab:

        st.header("🛍️ Our Clothing")

        conn = get_connection()

        products = conn.execute(
            """
            SELECT id, name, price, inventory,
                   image, description
            FROM products
            ORDER BY id
            """
        ).fetchall()

        conn.close()

        if not products:

            st.info(
                "There are currently no products."
            )

        else:

            columns = st.columns(4)

            for index, product in enumerate(products):

                product_id = product[0]
                name = product[1]
                price = product[2]
                inventory = product[3]
                image = product[4]
                description = product[5]

                with columns[index % 4]:

                    st.image(
                        image,
                        use_container_width=True
                    )

                    st.subheader(name)

                    st.write(
                        f"**${price:.2f}**"
                    )

                    st.write(
                        description
                    )

                    if inventory > 0:

                        st.write(
                            f"Available: {inventory}"
                        )

                        quantity = st.number_input(
                            "Quantity",
                            min_value=1,
                            max_value=inventory,
                            value=1,
                            key=f"quantity_{product_id}"
                        )

                        if st.button(
                            "🛒 Add to Cart",
                            key=f"customer_add_{product_id}",
                            use_container_width=True
                        ):

                            current_quantity = (
                                st.session_state.cart.get(
                                    product_id,
                                    0
                                )
                            )

                            if (
                                current_quantity + quantity
                                <= inventory
                            ):

                                st.session_state.cart[
                                    product_id
                                ] = (
                                    current_quantity
                                    + quantity
                                )

                                st.success(
                                    "Added to cart!"
                                )

                            else:

                                st.error(
                                    "Not enough inventory."
                                )

                    else:

                        st.error(
                            "Out of stock"
                        )


    # =====================================================
    # CART
    # =====================================================

    with cart_tab:

        st.header("🛒 Shopping Cart")

        if not st.session_state.cart:

            st.info(
                "Your shopping cart is empty."
            )

        else:

            total = 0

            for product_id, quantity in list(
                st.session_state.cart.items()
            ):

                conn = get_connection()

                product = conn.execute(
                    """
                    SELECT id, name, price, inventory
                    FROM products
                    WHERE id = ?
                    """,
                    (product_id,)
                ).fetchone()

                conn.close()

                if product is None:

                    del st.session_state.cart[
                        product_id
                    ]

                    continue

                product_price = product[2]
                subtotal = product_price * quantity

                total += subtotal

                col1, col2, col3, col4 = st.columns(
                    [3, 1, 1, 1]
                )

                with col1:

                    st.write(
                        f"**{product[1]}**"
                    )

                with col2:

                    st.write(
                        f"${product_price:.2f}"
                    )

                with col3:

                    st.write(
                        f"Quantity: {quantity}"
                    )

                with col4:

                    if st.button(
                        "Remove",
                        key=f"cart_remove_{product_id}"
                    ):

                        del st.session_state.cart[
                            product_id
                        ]

                        st.rerun()

            st.divider()

            st.subheader(
                f"💰 Total: ${total:.2f}"
            )

            # -------------------------------------------------
            # CHECKOUT
            # -------------------------------------------------

            st.header("💳 Checkout")

            st.write(
                "This checkout demonstrates the payment "
                "process for the store."
            )

            payment_method = st.selectbox(
                "Payment method",
                [
                    "Credit Card (Demo)",
                    "PayPal (Demo)"
                ]
            )

            if payment_method:

                if st.button(
                    "💳 Complete Payment & Place Order",
                    use_container_width=True
                ):

                    conn = get_connection()

                    # Verify inventory one more time
                    inventory_ok = True

                    for product_id, quantity in (
                        st.session_state.cart.items()
                    ):

                        product = conn.execute(
                            """
                            SELECT inventory
                            FROM products
                            WHERE id = ?
                            """,
                            (product_id,)
                        ).fetchone()

                        if (
                            product is None
                            or product[0] < quantity
                        ):

                            inventory_ok = False
                            break

                    if not inventory_ok:

                        conn.close()

                        st.error(
                            "Some products no longer "
                            "have enough inventory."
                        )

                    else:

                        # Create order
                        cursor = conn.cursor()

                        cursor.execute(
                            """
                            INSERT INTO orders
                            (user_id, total, order_date,
                             payment_status)
                            VALUES (?, ?, ?, ?)
                            """,
                            (
                                st.session_state.user_id,
                                total,
                                datetime.now().strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                ),
                                "Paid - Demo"
                            )
                        )

                        order_id = cursor.lastrowid

                        # Save each item
                        for product_id, quantity in (
                            st.session_state.cart.items()
                        ):

                            product = conn.execute(
                                """
                                SELECT price
                                FROM products
                                WHERE id = ?
                                """,
                                (product_id,)
                            ).fetchone()

                            price = product[0]

                            cursor.execute(
                                """
                                INSERT INTO order_items
                                (order_id, product_id,
                                 quantity, price)
                                VALUES (?, ?, ?, ?)
                                """,
                                (
                                    order_id,
                                    product_id,
                                    quantity,
                                    price
                                )
                            )

                            # Deduct inventory
                            cursor.execute(
                                """
                                UPDATE products
                                SET inventory =
                                    inventory - ?
                                WHERE id = ?
                                """,
                                (
                                    quantity,
                                    product_id
                                )
                            )

                        conn.commit()
                        conn.close()

                        # Empty cart
                        st.session_state.cart = {}

                        st.success(
                            f"🎉 Payment successful! "
                            f"Your order #{order_id} "
                            f"has been placed."
                        )

                        st.info(
                            "Inventory has been updated "
                            "and your order has been saved."
                        )

                        st.rerun()


    # =====================================================
    # ORDER HISTORY
    # =====================================================

    with history_tab:

        st.header("📋 My Order History")

        conn = get_connection()

        orders = conn.execute(
            """
            SELECT id, total, order_date,
                   payment_status
            FROM orders
            WHERE user_id = ?
            ORDER BY id DESC
            """,
            (st.session_state.user_id,)
        ).fetchall()

        conn.close()

        if not orders:

            st.info(
                "You have not placed any orders yet."
            )

        else:

            for order in orders:

                with st.expander(
                    f"Order #{order[0]} "
                    f"- ${order[1]:.2f}"
                ):

                    st.write(
                        f"Date: {order[2]}"
                    )

                    st.write(
                        f"Payment: {order[3]}"
                    )

                    conn = get_connection()

                    items = conn.execute(
                        """
                        SELECT products.name,
                               order_items.quantity,
                               order_items.price
                        FROM order_items
                        JOIN products
                        ON order_items.product_id =
                           products.id
                        WHERE order_items.order_id = ?
                        """,
                        (order[0],)
                    ).fetchall()

                    conn.close()

                    st.write("**Items:**")

                    for item in items:

                        st.write(
                            f"- {item[0]} "
                            f"x {item[1]} "
                            f"(${item[2]:.2f} each)"
                        )
