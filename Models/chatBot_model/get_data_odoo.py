import xmlrpc.client
import os
from dotenv import load_dotenv

load_dotenv()

def get_ecommerce_products_from_odoo():
    # Odoo configuration
    url = os.getenv("ODOO_URL")
    db = os.getenv("ODOO_DB")
    username = os.getenv("ODOO_USER")
    password = os.getenv("ODOO_PASSWORD")

    print(url)
    # Login to Odoo
    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
    uid = common.authenticate(db, username, password, {})

    if not uid:
        raise Exception("Login failed. Please check your credentials.")

    # Connect to the object service
    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")

    # Model: product.product
    model_name = 'product.product'

    # Get products with non-empty ecommerce description
    product_ids = models.execute_kw(
        db, uid, password,
        model_name, 'search',
        [[('description_ecommerce', '!=', False)]]
    )

    if not product_ids:
        return []

    # Read product fields
    products = models.execute_kw(
        db, uid, password,
        model_name, 'read',
        [product_ids],
        {'fields': ['name', 'id', 'qty_available', 'description_ecommerce', 'categ_id', 'public_categ_ids', 'list_price']}
    )

    # Collect all eCommerce category IDs
    all_cat_ids = set()
    for product in products:
        all_cat_ids.update(product.get('public_categ_ids', []))

    # Fetch eCommerce category names from product.public.category
    cat_id_to_name = {}
    if all_cat_ids:
        category_records = models.execute_kw(
            db, uid, password,
            'product.public.category', 'read',
            [list(all_cat_ids)],
            {'fields': ['name']}
        )
        cat_id_to_name = {cat['id']: cat['name'] for cat in category_records}

    # Build and return the product list
    result = []
    for product in products:
        internal_category = product['categ_id'][1] if product.get('categ_id') else 'N/A'
        ecommerce_cat_ids = product.get('public_categ_ids', [])
        ecommerce_cat_names = ', '.join([cat_id_to_name.get(cid, str(cid)) for cid in ecommerce_cat_ids]) if ecommerce_cat_ids else 'None'

        result.append({
            'name': product['name'],
            'id': product.get('id', 'N/A'),
            'stock_quantity': product.get('qty_available', 0),
            'price': product.get('list_price', 0.0),
            'ecommerce_categories': ecommerce_cat_names,
            'description_ecommerce': product.get('description_ecommerce', '')
        })

    return result

if __name__ == '__main__':
    products = get_ecommerce_products_from_odoo()

    # Example: show the first product
    if products:
        print(products)