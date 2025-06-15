import re
import os
from dotenv import load_dotenv
import xmlrpc.client
from typing import List, Dict

def extract_ids(text: str) -> list[str]:
    ids = re.findall(r"<<(\d+)>>", text)
    ids += re.findall(r"link\s*-->\s*(\d+)", text)
    return list(set(ids))

def search_odoo_products(product_ids_to_search: List[int]) -> Dict[int, Dict[str, str]]:
    load_dotenv()
    ODOO_URL = os.getenv("ODOO_URL_PUBLIC")
    ODOO_DB = os.getenv("ODOO_DB")
    ODOO_USER = os.getenv("ODOO_USER")
    ODOO_PASSWORD = os.getenv("ODOO_PASSWORD")

    found_product_urls = {}

    try:
        common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
        uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASSWORD, {})
        if not uid:
            raise Exception("Authentication failed.")

        models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')

        for product_id in product_ids_to_search:
            # Get product_product info
            product_product_data = models.execute_kw(
                ODOO_DB,
                uid,
                ODOO_PASSWORD,
                'product.product',
                'read',
                [product_id],
                {'fields': ['product_tmpl_id']}
            )
            if not product_product_data:
                continue

            template_id = product_product_data[0]['product_tmpl_id'][0]

            # Check if published
            is_published = models.execute_kw(
                ODOO_DB,
                uid,
                ODOO_PASSWORD,
                'product.template',
                'search',
                [[['id', '=', template_id], ['website_published', '=', True]]],
                {'limit': 1}
            )
            if not is_published:
                continue

            # Read template data
            template_data = models.execute_kw(
                ODOO_DB,
                uid,
                ODOO_PASSWORD,
                'product.template',
                'read',
                [template_id],
                {'fields': ['website_url', 'name']}
            )
            if template_data and template_data[0].get('website_url'):
                raw_url = f"{ODOO_URL}{template_data[0]['website_url']}"
                cleaned_url = re.sub(r'[.,)]+$', '', raw_url)
                found_product_urls[product_id] = {
                    "url": cleaned_url,
                    "name": template_data[0].get("name", "View Product")
                }
    except Exception as e:
        print(f"Error searching Odoo products: {e}")

    return found_product_urls

def bot_response_with_odoo_url(gemini_response: str) -> str:
    # Extract IDs from entire response text
    extracted_ids = extract_ids(gemini_response)
    if not extracted_ids:
        return gemini_response

    numeric_ids = list(set(int(pid) for pid in extracted_ids))  # unique IDs

    odoo_product_data = search_odoo_products(numeric_ids)

    final_response = gemini_response

    # Replace each <<ID>> with clickable link (or just URL)
    for product_id_str in extracted_ids:
        product_id = int(product_id_str)
        product_info = odoo_product_data.get(product_id)
        if product_info:
            url = product_info['url']
            name = product_info['name']
            # Example replacement: replace <<ID>> with HTML link or markdown
            # For HTML:
            link_html = f'<a href="{url}" target="_blank">{name}</a>'
            final_response = final_response.replace(f"<<{product_id_str}>>", link_html)
        else:
            # If no product info found, remove the token or keep it
            final_response = final_response.replace(f"<<{product_id_str}>>", "[Product not found]")

    return final_response


if __name__ == '__main__':
    example_text = """
        معلش يا فندم، مفيش تليفونات اسمها "تيلفوت" عندنا. بس عندنا تليفونات رخيصة ممكن تعجبك.

        إحنا عندنا نوعين ممكن يناسبوك:

        Nokia Lumia 521 (T-Mobile) link --> <<15142>> تليفون كويس جداً، وشكله حلو كمان. متوفر دلوقتي.
        AT&T 841000 Phone link --> <<14580>> ده كمان اختيار ممتاز، متين وبيشتغل كويس. وده كمان متوفر.
        يا ريت تقولي إيه المواصفات اللي بتدور عليها بالتحديد، عشان أقدر أساعدك أكتر وألاقي اللي يناسبك
        """

    print(bot_response_with_odoo_url(example_text))