import pandas as pd
import pickle

# Load the two CSV files
df_superstore = pd.read_csv('Superstore-Data-1-review (1).csv', encoding='ISO-8859-1')
df_products = pd.read_csv('all products.csv', encoding='ISO-8859-1')

# Merge the two dataframes based on 'Product ID'
merged_df = pd.merge(df_superstore, df_products[['Product ID', 'Product Name', 'Product Description', 'Yahoo Image URL', 'Price']], on='Product ID', how='left')

# اطبع أول 5 صفوف من DataFrame بعد الدمج
print("أول 5 صفوف من DataFrame بعد الدمج:")
print(merged_df.head())

# اطبع معلومات موجزة عن DataFrame بعد الدمج
print("\nمعلومات موجزة عن DataFrame بعد الدمج:")
print(merged_df.info())

# حذف أي صف يحتوي على أي قيمة مفقودة (NaN)
cleaned_df = merged_df.dropna()

# Select only the required columns AFTER dropping NaNs
required_columns = ['Customer ID', 'Product ID', 'Product Name_y', 'Product Description', 'Price', 'Rate', 'Category', 'Yahoo Image URL', 'Sales', 'Order ID']
customer_data = cleaned_df[required_columns]

# Save the cleaned DataFrame to a pickle file
with open('customer_recommendation_data.pkl', 'wb') as f:
    pickle.dump(customer_data, f)

print("\ncustomer_recommendation_data.pkl created successfully after cleaning NaNs.")
print("Columns in saved DataFrame:", customer_data.columns.tolist())
print("customer_data:")
# يمكنك هنا طباعة جزء من customer_data إذا أردت رؤية بعض البيانات الفعلية
# print(customer_data.head())