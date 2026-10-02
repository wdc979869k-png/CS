import streamlit as st
import sqlite3
import hashlib
from datetime import datetime
from groq import Groq


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
            image TEXT,
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
            payment_status TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Order items
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
    # ADMIN ACCOUNT
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
    # SAMPLE PRODUCTS
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

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []


# ============================================================
# LOGIN
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
    st.session_state.chat_messages = []

    st.rerun()


# ============================================================
# GET CURRENT PRODUCTS FROM DATABASE
# ============================================================

def get_all_products():

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

    return products


# ============================================================
# CREATE STORE DATABASE CONTEXT FOR AI
# ============================================================

def get_store_context():

    products = get_all_products()

    if not products:
        return "There are currently no products in the store."

    lines = []

    for product in products:

        product_id = product[0]
        name = product[1]
        price = product[2]
        inventory = product[3]
        description = product[5] or ""

        if inventory > 0:
            availability = "IN STOCK"
        else:
            availability = "OUT OF STOCK"

        lines.append(
            f"""
Product ID: {product_id}
Product name: {name}
Current price: ${price:.2f}
Current inventory: {inventory}
Availability: {availability}
Description: {description}
"""
        )

    return "\n".join(lines)


# ============================================================
# AI STORE CHATBOT
# ============================================================

def ask_store_ai(user_question):

    # Get the REAL current data from the database
    store_context = get_store_context()

    try:

        api_key = st.secrets["GROQ_API_KEY"]

    except Exception:

        return (
            "The AI assistant is not configured yet. "
            "Please add GROQ_API_KEY to Streamlit Secrets."
        )

    try:

        client = Groq(api_key=api_key)

        system_prompt = f"""
You are the AI Store Assistant for CS Clothing Store.

Your job is to help customers using ONLY the real store
information supplied below.

STORE DATABASE INFORMATION:
{store_context}

IMPORTANT RULES:

1. Never invent a product.
2. Never invent a price.
3. Never invent inventory.
4. Never claim something is in stock unless the database says
   its inventory is greater than 0.
5. Never claim something is out of stock unless the database
   says its inventory is 0.
6. Always use the CURRENT price from the database.
7. Always use the CURRENT inventory from the database.
8. If the requested product is not in the database, say that
   the product is not currently listed in the store.
9. If asked for recommendations, recommend only products
   that exist in the database.
10. For recommendations, prefer products that are currently
    in stock.
11. You can use product names and descriptions to explain
    why products are related.
12. Do not make up product features that are not in the
    database.
13. Keep answers clear and helpful.
14. You may answer simple general questions about the products
    using the supplied descriptions.
15. If there is not enough information in the database, say so.

Examples:

Customer:
"Do you have black shoes?"

You should check the database and report the actual matching
product, inventory, and price.

Customer:
"How much is the denim jacket?"

Use the exact current database price.

Customer:
"Recommend something similar."

Use actual products from the database and prefer products
currently in stock.

Remember:
The database is the source of truth.
"""

        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_question
                }
            ],
            temperature=0.2,
            max_tokens=500
        )

        return response.choices[0].message.content

    except Exception as e:

        return (
            "Sorry, I could not connect to the AI service.\n\n"
            f"Error: {str(e)}"
        )


# ============================================================
# HEADER
# ============================================================

st.title("👗 CS Clothing Store")
st.write(
    "Welcome to our online clothing store!"
)


# ============================================================
# NOT LOGGED IN
# ============================================================

if not st.session_state.logged_in:

    login_tab, register_tab = st.tabs(
        [
            "🔐 Login",
            "📝 Customer Registration"
        ]
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

            if (
                username.strip() == ""
                or password.strip() == ""
            ):

                st.error(
                    "Please enter both username and password."
                )

            elif login_user(username, password):

                st.success("Login successful!")
                st.rerun()

            else:

                st.error(
                    "Incorrect username or password."
                )

        st.info(
            "Demo Admin Login: "
            "username = admin, password = admin123"
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

                    st.error(
                        "Username already exists."
                    )

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
        "Logged in as: "
        + st.session_state.username
    )

    st.sidebar.write(
        "Role: "
        + st.session_state.role.title()
    )

    if st.sidebar.button(
        "🚪 Logout",
        use_container_width=True
    ):

        logout()

    # ========================================================
    # ADMIN
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
        # PRODUCTS & INVENTORY
        # ====================================================

        with admin_tabs[0]:

            st.subheader(
                "Manage Products & Inventory"
            )

            products = get_all_products()

            if not products:

                st.info(
                    "No products available."
                )

            for product in products:

                product_id = product[0]
                product_name = product[1]
                product_price = product[2]
                product_inventory = product[3]
                product_image = product[4] or ""
                product_description = product[5] or ""

                with st.expander(
                    f"{product_name} | "
                    f"${product_price:.2f} | "
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

                            st.success(
                                "Product updated!"
                            )

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

                            st.success(
                                "Product deleted!"
                            )

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

                    st.error(
                        "Please enter a product name."
                    )

                else:

                    conn = get_connection()
                    cursor = conn.cursor()

                    cursor.execute(
                        """
                        INSERT INTO products
                        (
                            name,
                            price,
                            inventory,
                            image,
                            description
                        )
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

            st.subheader(
                "All Customer Orders"
            )

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

                st.info(
                    "No orders have been placed yet."
                )

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
                            "Date: "
                            + str(order_date)
                        )

                        st.write(
                            "Payment: "
                            + str(payment_status)
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
                "📜 Order History",
                "🤖 AI Store Assistant"
            ]
        )

        # ====================================================
        # SHOP
        # ====================================================

        with customer_tabs[0]:

            st.subheader(
                "Available Products"
            )

            products = get_all_products()

            if not products:

                st.info(
                    "No products are currently available."
                )

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

                            st.write(
                                "Image unavailable."
                            )

                with col2:

                    st.subheader(
                        product_name
                    )

                    st.write(
                        product_description
                    )

                    st.write(
                        f"### ${product_price:.2f}"
                    )

                    st.write(
                        "Available inventory: "
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
                                    current_quantity
                                    + quantity
                                )

                                if (
                                    new_quantity
                                    <= product_inventory
                                ):

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

                        st.error(
                            "Out of stock."
                        )

                st.divider()

        # ====================================================
        # SHOPPING CART
        # ====================================================

        with customer_tabs[1]:

            st.subheader(
                "🛒 Your Shopping Cart"
            )

            if not st.session_state.cart:

                st.info(
                    "Your shopping cart is empty."
                )

            else:

                total = 0.0

                for product_id in list(
                    st.session_state.cart.keys()
                ):

                    item = st.session_state.cart[
                        product_id
                    ]

                    item_total = (
                        item["price"]
                        * item["quantity"]
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

                st.markdown(
                    "### 💳 Checkout"
                )

                payment_method = st.selectbox(
                    "Payment Method",
                    [
                        "Credit Card (Demo)",
                        "PayPal (Demo)"
                    ]
                )

                st.info(
                    "This is a school-project demo "
                    "payment. No real money is charged."
                )

                if st.button(
                    "💳 Complete Payment & Place Order",
                    use_container_width=True
                ):

                    conn = get_connection()
                    cursor = conn.cursor()

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

                        if (
                            quantity
                            > current_inventory
                        ):

                            inventory_problem = True
                            break

                    if inventory_problem:

                        conn.close()

                        st.error(
                            "There is not enough inventory "
                            "for one or more products."
                        )

                    else:

                        order_date = (
                            datetime.now().strftime(
                                "%Y-%m-%d %H:%M:%S"
                            )
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

                        for product_id in (
                            st.session_state.cart
                        ):

                            item = st.session_state.cart[
                                product_id
                            ]

                            quantity = item[
                                "quantity"
                            ]

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

                        st.session_state.cart = {}

                        st.success(
                            "🎉 Payment successful! "
                            f"Your order #{order_id} "
                            "has been placed."
                        )

                        st.rerun()

        # ====================================================
        # ORDER HISTORY
        # ====================================================

        with customer_tabs[2]:

            st.subheader(
                "📜 Your Order History"
            )

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

        # ====================================================
        # AI STORE ASSISTANT
        # ====================================================

        with customer_tabs[3]:

            st.subheader(
                "🤖 AI Store Assistant"
            )

            st.write(
                "Ask me about products, prices, "
                "availability, inventory, or recommendations."
            )

            st.info(
                "I use the current store database "
                "to answer your questions."
            )

            # Show previous messages
            for message in st.session_state.chat_messages:

                with st.chat_message(
                    message["role"]
                ):

                    st.markdown(
                        message["content"]
                    )

            user_question = st.chat_input(
                "Example: Do you have black shoes in stock?"
            )

            if user_question:

                # Save user question
                st.session_state.chat_messages.append(
                    {
                        "role": "user",
                        "content": user_question
                    }
                )

                with st.chat_message("user"):

                    st.markdown(
                        user_question
                    )

                # Ask AI using current database
                with st.chat_message("assistant"):

                    with st.spinner(
                        "Checking the store database..."
                    ):

                        answer = ask_store_ai(
                            user_question
                        )

                    st.markdown(answer)

                # Save AI answer
                st.session_state.chat_messages.append(
                    {
                        "role": "assistant",
                        "content": answer
                    }
                )
