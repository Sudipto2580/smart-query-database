from faker import Faker
import random
import pymysql

fake = Faker()

connection = pymysql.connect(
    host='localhost',
    user='root',
    password='Sudipto2580@',
    database='smart_query_db'
)

cursor = connection.cursor()

product_types = [
    "Laptop", "Phone", "Keyboard", "Shoes", "T-Shirt",
    "Book", "Mouse", "Monitor", "Camera", "Watch",
    "Speaker", "Bag", "Headphones", "Tablet", "Printer"
]

for i in range(500):

    category_id = random.randint(1, 10)
    supplier_id = random.randint(1, 5)

    product_name = random.choice(product_types) + " " + fake.word().capitalize()

    description = fake.text(max_nb_chars=100)

    price = round(random.uniform(100, 100000), 2)

    stock = random.randint(1, 200)

    rating = round(random.uniform(1, 5), 1)

    sql = """
    INSERT INTO products
    (category_id, supplier_id, product_name, description, price, stock, rating)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """

    values = (
        category_id,
        supplier_id,
        product_name,
        description,
        price,
        stock,
        rating
    )

    cursor.execute(sql, values)

    image_urls = [
    "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9",
    "https://images.unsplash.com/photo-1517336714739-489689fd1ca8",
    "https://images.unsplash.com/photo-1523275335684-37898b6baf30"
]

image_url = random.choice(image_urls)

connection.commit()

print("500 products inserted successfully!")