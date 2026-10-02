import streamlit as st

st.set_page_config(
    page_title="CS Clothing Store",
    page_icon="👗",
    layout="wide"
)

# Store title
st.title("👗 CS Clothing Store")
st.write("Welcome! Find your favorite clothes and accessories.")
st.divider()

# Products
products = [
    {
        "id": 1,
        "name": "White T-Shirt",
        "price": 25,
        "image": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab"
    },
    {
        "id": 2,
        "name": "Denim Jacket",
        "price": 55,
        "image": "https://images.unsplash.com/photo-1551028719-00167b16eac5"
    },
    {
        "id": 3,
        "name": "Black Dress",
        "price": 60,
        "image": "https://images.unsplash.com/photo-1595777457583-95e059d581b8"
    },
    {
        "id": 4,
        "name": "Sneakers",
        "price": 70,
        "image": "https://images.unsplash.com/photo-1542291026-7eec264c27ff"
    }
]

# Create shopping cart
if "cart" not in st.session_state:
    st.session_state.cart = []


# Add product
def add_to_cart(product):
    st.session_state.cart.append(product)


# Remove product
def remove_from_cart(index):
    st.session_state.cart.pop(index)


# Products section
st.header("🛍️ Our Products")

columns = st.columns(4)

for i, product in enumerate(products):

    with columns[i]:

        st.image(
            product["image"],
            use_container_width=True
        )

        st.subheader(product["name"])

        st.write(f"**${product['price']}**")

        if st.button(
            "🛒 Add to Cart",
            key=f"add_{product['id']}",
            use_container_width=True
        ):
            add_to_cart(product)
            st.success("Added!")


st.divider()

# Shopping cart
st.header("🛒 Shopping Cart")

if len(st.session_state.cart) == 0:

    st.info("Your shopping cart is empty.")

else:

    total = 0

    for i, item in enumerate(st.session_state.cart):

        col1, col2, col3 = st.columns([4, 2, 1])

        with col1:
            st.write(f"**{item['name']}**")

        with col2:
            st.write(f"${item['price']}")

        with col3:
            if st.button(
                "Remove",
                key=f"remove_{i}"
            ):
                remove_from_cart(i)
                st.rerun()

        total += item["price"]

    st.divider()

    st.subheader(f"💰 Total: ${total}")

    if st.button(
        "💳 Checkout",
        use_container_width=True
    ):
        st.success("🎉 Thank you for shopping!")
        st.info(
            "This is a demo checkout. "
            "No real payment has been processed."
        )


st.divider()

st.write("© 2026 CS Clothing Store")
