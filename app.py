from flask import Flask, jsonify, request
import os
from bson import ObjectId
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# Initialize Flask app
app = Flask(__name__)

# Load environment variables from .env file
load_dotenv()

# MongoDB connection
MONGO_URI = os.getenv('MONGO_URI') 

try:
    # Connect to MongoDB
    client = MongoClient(MONGO_URI)
    client.admin.command('ping')  # Verify connection
    print("Database connected successfully.")
    db = client["FoodDeliveryApp"]
    users = db["user"]
    menus = db["menu"]
    orders = db["order"]
except ConnectionFailure:
    print("Failed to connect to the database.")


###################### User Section #######################
# Root route to display a welcome message
@app.route('/', methods=['GET'])
def welcome():
    return jsonify({"msg": "Welcome to the Food Delivery App"}), 200

# Route to register a new user
@app.route('/register', methods=['POST'])
def register_user():
    # Get form data (for form submission)
    data = request.get_json()

    print(data)
    
    # Check if role is valid
    if data.get('role') not in ["customer", "restaurant_owner", "delivery_personnel", "admin"]:
        return jsonify({"msg": "Invalid role"}), 400

    # Ensure essential fields are provided
    if not data.get('name') or not data.get('email') or not data.get('password'):
        return jsonify({"msg": "Missing required fields"}), 400

    # Check if a user with the same email already exists
    if users.find_one({"email": data.get('email')}):
        return jsonify({"msg": "User with this email already exists"}), 400

    try:
        # Insert the user data into MongoDB
        user_id = users.insert_one(data).inserted_id

        # Fetch the saved user from the database by ID (to get the auto-generated _id)
        saved_user = users.find_one({"_id": ObjectId(user_id)})

        # Convert ObjectId to string
        saved_user['_id'] = str(saved_user['_id'])

        return jsonify({"msg": "User registered successfully", "user_data": saved_user}), 201
    except Exception as e:
        return jsonify({"msg": "Error registering user", "error": str(e)}), 500

# Update user profile
@app.route('/users/<user_id>', methods=['PUT'])
def update_user(user_id):
    # Get the data to update from the request body
    data = request.get_json()
    try:
        # Update only the fields that are provided in the request
        result = users.update_one(
            {"_id": ObjectId(user_id)}, 
            {"$set": data}  # Use $set to update fields
        )

        if result.modified_count > 0:
            # Fetch the updated user data to return
            updated_user = users.find_one({"_id": ObjectId(user_id)})
            # Convert ObjectId to string
            updated_user['_id'] = str(updated_user['_id'])
            return jsonify({"msg": "User updated successfully", "user_data": updated_user}), 200
        else:
            return jsonify({"msg": "No changes made to the user"}), 400

    except Exception as e:
        return jsonify({"msg": "Error updating user", "error": str(e)}), 500

# Get order Track or history
@app.route('/restaurant/orders/<restaurant_id>', methods=['GET'])
def get_restaurant_orders(restaurant_id):
    try:
        # Find all orders associated with the restaurant
        restaurant_orders = list(orders.find({"restaurant_id": ObjectId(restaurant_id)}))

        if not restaurant_orders:
            return jsonify({"msg": "No orders found for this restaurant"}), 404

        # Convert ObjectId fields to strings for each order
        formatted_orders = []
        for order in restaurant_orders:
            order["_id"] = str(order["_id"])
            order["user_id"] = str(order["user_id"])
            order["restaurant_id"] = str(order["restaurant_id"])
            order["delivery_person_id"] = str(order["delivery_person_id"])
            formatted_orders.append(order)

        return jsonify({"msg": "Orders retrieved successfully", "orders": formatted_orders}), 200

    except Exception as e:
        return jsonify({"msg": "Error retrieving orders", "error": str(e)}), 500



# Route to retrieve all users
@app.route('/users', methods=['GET'])
def get_all_users():
    try:
        # Fetch all users from MongoDB
        all_users = list(users.find({}))  # Exclude passwords from response for security

        # Convert MongoDB documents to JSON serializable format
        user_list = []
        for user in all_users:
            user['_id'] = str(user['_id'])  # Convert ObjectId to string
            user_list.append(user)
        
        return jsonify({"msg": "Users retrieved successfully", "users": user_list}), 200
    except Exception as e:
        return jsonify({"msg": "Error fetching users", "error": str(e)}), 500
    
# Route to delete a user by ID
@app.route('/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        # Attempt to delete the user with the specified ID
        result = users.delete_one({"_id": ObjectId(user_id)})

        # Check if a document was deleted
        if result.deleted_count > 0:
            return jsonify({"msg": "User deleted successfully", "user_id": user_id}), 200
        else:
            return jsonify({"msg": "User not found", "user_id": user_id}), 404
    except Exception as e:
        return jsonify({"msg": "Error deleting user", "error": str(e)}), 500

# Route to login (basic authentication simulation)
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = users.find_one({"email": data.get("email"), "password": data.get("password")})
    if user:
        return jsonify({"msg": "Login successful", "user_id": str(user["_id"]), "role": user["role"]})
    return jsonify({"msg": "Invalid credentials"}), 401

# Get restaurant order
@app.route('/restaurant_specific/orders/<restaurant_id>', methods=['GET'])
def get_specific_restaurant_orders(restaurant_id):
    try:
        # Find all orders associated with the restaurant
        restaurant_orders = list(orders.find({"restaurant_id": ObjectId(restaurant_id)}))

        if not restaurant_orders:
            return jsonify({"msg": "No orders found for this restaurant"}), 404

        # Convert ObjectId fields to strings for each order
        formatted_orders = []
        for order in restaurant_orders:
            order["_id"] = str(order["_id"])
            order["user_id"] = str(order["user_id"])
            order["restaurant_id"] = str(order["restaurant_id"])
            order["delivery_person_id"] = str(order["delivery_person_id"])
            formatted_orders.append(order)

        return jsonify({"msg": "Orders retrieved successfully", "orders": formatted_orders}), 200

    except Exception as e:
        return jsonify({"msg": "Error retrieving orders", "error": str(e)}), 500


# Get Delivery Person Order
@app.route('/delivery_person/orders/<delivery_person_id>', methods=['GET'])
def get_delivery_person_orders(delivery_person_id):
    try:
        # Query the database for orders associated with the given delivery_person_id
        order_cursor = orders.find({"delivery_person_id": ObjectId(delivery_person_id)})
        
        # Convert the cursor to a list of orders
        orders_list = list(order_cursor)

        # If no orders are found, return a message
        if not orders_list:
            return jsonify({'message': 'No orders found for this delivery person.'}), 404
        
        # Format the orders list by converting ObjectId to string for each field
        formatted_orders = []
        for order in orders_list:
            order["_id"] = str(order["_id"])
            order["user_id"] = str(order["user_id"])
            order["restaurant_id"] = str(order["restaurant_id"])
            order["delivery_person_id"] = str(order["delivery_person_id"])
            
            # Include menu details
            order["menu_detail"] = order.get("menu_detail", [])

            formatted_orders.append(order)

        # Return the formatted orders list in the response
        return jsonify({'orders': formatted_orders}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
####### Menu API Section #################################

# Route to add menu items for a restaurant
@app.route('/menu/<restaurant_id>', methods=['POST'])
def add_menu(restaurant_id):
    # Get menu data from request
    data = request.get_json()

    # Validate the incoming data
    if not data.get('product_name') or not data.get('price') or not data.get('detail'):
        return jsonify({"msg": "Missing required fields (product_name, price, detail)"}), 400
    
    # Prepare the new product to be added
    new_menu_item = {
        "product_name": data.get('product_name'),
        "price": data.get('price'),
        "detail": data.get('detail')
    }

    try:
        # Check if the restaurant already has a menu
        existing_menu = menus.find_one({"restaurant_id": ObjectId(restaurant_id)})

        if existing_menu:
            # If menu exists, update by appending the new menu item to the existing list
            menus.update_one(
                {"restaurant_id": ObjectId(restaurant_id)}, 
                {"$push": {"menu_items": new_menu_item}}  # $push adds the item to the array
            )

            return jsonify({"msg": "Menu item added successfully to existing menu"}), 200
        else:
            # If no menu exists, create a new menu document with the restaurant_id
            new_menu = {
                "restaurant_id": ObjectId(restaurant_id),
                "menu_items": [new_menu_item]  # Create a new list with the first item
            }

            # Insert the new menu for the restaurant
            menus.insert_one(new_menu)

            return jsonify({"msg": "New menu created and item added successfully"}), 201

    except Exception as e:
        return jsonify({"msg": "Error adding menu item", "error": str(e)}), 500

# Route to get all menu items for a specific restaurant
@app.route('/menu/<restaurant_id>', methods=['GET'])
def get_menu(restaurant_id):
    try:
        # Query the menu collection to find the menu of the restaurant by restaurant_id
        restaurant_menu = menus.find_one({"restaurant_id": ObjectId(restaurant_id)})

        if restaurant_menu:
            # Convert ObjectId to string for the response
            restaurant_menu['_id'] = str(restaurant_menu['_id'])
            # Return the menu items
            return jsonify({"msg": "Menu retrieved successfully", "menu": restaurant_menu['menu_items']}), 200
        else:
            return jsonify({"msg": "No menu found for the given restaurant_id"}), 404

    except Exception as e:
        return jsonify({"msg": "Error retrieving menu", "error": str(e)}), 500

# Update menu items
@app.route('/menu/<restaurant_id>', methods=['PUT'])
def update_menu(restaurant_id):
    data = request.get_json()

    try:
        # Find the restaurant menu using restaurant_id
        restaurant_menu = menus.find_one({"restaurant_id": ObjectId(restaurant_id)})

        if not restaurant_menu:
            return jsonify({"msg": "Restaurant menu not found"}), 404

        # Check if product_name is provided in the data
        if not data.get('product_name'):
            return jsonify({"msg": "Product name is required"}), 400

        # Find the product inside the menu_items array by product_name
        existing_product = next((item for item in restaurant_menu['menu_items'] if item['product_name'] == data['product_name']), None)

        if existing_product:
            # Prepare the update object to only include fields that are provided in the data
            update_data = {}

            # Only update the fields that are present in the request data
            if 'price' in data:
                update_data["menu_items.$.price"] = data['price']
            if 'detail' in data:
                update_data["menu_items.$.detail"] = data['detail']

            # Update the menu with the provided fields
            result = menus.update_one(
                {"restaurant_id": ObjectId(restaurant_id), "menu_items.product_name": data['product_name']},
                {"$set": update_data}  # Dynamically set the fields to update
            )

            if result.modified_count > 0:
                return jsonify({"msg": "Menu item updated successfully"}), 200
            else:
                return jsonify({"msg": "No changes made to the product"}), 400
        else:
            return jsonify({"msg": "Product not found in the menu"}), 404

    except Exception as e:
        return jsonify({"msg": "Error updating menu", "error": str(e)}), 500

# Deleting a item from the menu
@app.route('/menu/<restaurant_id>/<product_name>', methods=['DELETE'])
def delete_menu_item(restaurant_id, product_name):
    try:
        # Find the restaurant menu using restaurant_id
        restaurant_menu = menus.find_one({"restaurant_id": ObjectId(restaurant_id)})

        if not restaurant_menu:
            return jsonify({"msg": "Restaurant menu not found"}), 404

        # Find the menu item by product_name
        menu_items = restaurant_menu['menu_items']
        item_to_remove = next((item for item in menu_items if item['product_name'] == product_name), None)

        if not item_to_remove:
            return jsonify({"msg": "Product not found in the menu"}), 404

        # Remove the item from the menu_items list
        result = menus.update_one(
            {"restaurant_id": ObjectId(restaurant_id)},
            {"$pull": {"menu_items": {"product_name": product_name}}}  # Use $pull to remove item by product_name
        )

        if result.modified_count > 0:
            return jsonify({"msg": "Menu item deleted successfully"}), 200
        else:
            return jsonify({"msg": "No changes made to the menu"}), 400

    except Exception as e:
        return jsonify({"msg": "Error deleting menu item", "error": str(e)}), 500

# Get  All Menu
@app.route('/menu', methods=['GET'])
def get_all_menus():
    try:
        # Retrieve all menus from the collection
        all_menus = list(menus.find({}))

        if not all_menus:
            return jsonify({"msg": "No menus found"}), 404

        # Format the response: convert ObjectId to string and include menu items
        formatted_menus = []
        for menu in all_menus:
            formatted_menus.append({
                "_id": str(menu["_id"]),
                "restaurant_id": str(menu["restaurant_id"]),
                "menu_items": menu["menu_items"]
            })

        return jsonify({"msg": "Menus retrieved successfully", "menus": formatted_menus}), 200

    except Exception as e:
        return jsonify({"msg": "Error fetching menus", "error": str(e)}), 500


############### Order Section #################################

# Add a new order
@app.route('/order/<user_id>/<restaurant_id>', methods=['POST'])
def add_order(user_id, restaurant_id):
    try:
        # Get data from request body
        data = request.get_json()

        # Validate required fields
        required_fields = ["status", "menu_detail", "total_price", "delivery_person_id"]
        for field in required_fields:
            if field not in data:
                return jsonify({"msg": f"Missing required field: {field}"}), 400

        # Prepare the order document
        order_data = {
            "user_id": ObjectId(user_id),
            "restaurant_id": ObjectId(restaurant_id),
            "status": data["status"],
            "menu_detail": data["menu_detail"],  # Assume this is a list or detailed object
            "total_price": data["total_price"],
            "delivery_person_id": ObjectId(data["delivery_person_id"])
        }

        # Insert the order into the database
        order_id = orders.insert_one(order_data).inserted_id

        # Fetch the inserted order to include all fields
        inserted_order = orders.find_one({"_id": order_id})

        # Convert ObjectId fields to strings for the response
        inserted_order["_id"] = str(inserted_order["_id"])
        inserted_order["user_id"] = str(inserted_order["user_id"])
        inserted_order["restaurant_id"] = str(inserted_order["restaurant_id"])
        inserted_order["delivery_person_id"] = str(inserted_order["delivery_person_id"])

        return jsonify({"msg": "Order added successfully", "order_data": inserted_order}), 201

    except Exception as e:
        return jsonify({"msg": "Error adding order", "error": str(e)}), 500

# Change status of order
@app.route('/order/<order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    try:
        # Get the delivery_person_id and new status from the request body
        data = request.get_json()

        # Validate the required fields
        if "delivery_person_id" not in data or "status" not in data:
            return jsonify({"msg": "Missing required fields: 'delivery_person_id' and 'status'"}), 400

        # Fetch the order by order_id
        order = orders.find_one({"_id": ObjectId(order_id)})

        if not order:
            return jsonify({"msg": "Order not found"}), 404

        # Check if the delivery person is valid for this order
        if str(order["delivery_person_id"]) != data["delivery_person_id"]:
            return jsonify({"msg": "Unauthorized: You are not assigned to this order"}), 403

        # Update the order status
        result = orders.update_one(
            {"_id": ObjectId(order_id)},
            {"$set": {"status": data["status"]}}
        )

        if result.modified_count > 0:
            # Fetch the updated order to return
            updated_order = orders.find_one({"_id": ObjectId(order_id)})
            updated_order["_id"] = str(updated_order["_id"])
            updated_order["user_id"] = str(updated_order["user_id"])
            updated_order["restaurant_id"] = str(updated_order["restaurant_id"])
            updated_order["delivery_person_id"] = str(updated_order["delivery_person_id"])

            return jsonify({"msg": "Order status updated successfully", "order": updated_order}), 200
        else:
            return jsonify({"msg": "No changes made to the order"}), 400

    except Exception as e:
        return jsonify({"msg": "Error updating order status", "error": str(e)}), 500


################## Admin Section #################
# Admin Get all user details
@app.route('/admin/all_users', methods=['GET'])
def get_all_users_admin():
    try:
        all_users = list(users.find({}))
        for user in all_users:
            user['_id'] = str(user['_id'])  # Convert ObjectId to string
        return jsonify({"msg": "All users retrieved successfully", "users": all_users}), 200
    except Exception as e:
        return jsonify({"msg": "Error retrieving users", "error": str(e)}), 500

# admin get all restaurant
@app.route('/admin/all_restaurants', methods=['GET'])
def get_all_restaurants_admin():
    try:
        all_restaurants = list(menus.find({}))
        for restaurant in all_restaurants:
            restaurant['_id'] = str(restaurant['_id'])
            restaurant['restaurant_id'] = str(restaurant['restaurant_id'])
        return jsonify({"msg": "All restaurants retrieved successfully", "restaurants": all_restaurants}), 200
    except Exception as e:
        return jsonify({"msg": "Error retrieving restaurants", "error": str(e)}), 500

# admin get all orders
@app.route('/admin/all_orders', methods=['GET'])
def get_all_orders_admin():
    try:
        all_orders = list(orders.find({}))
        for order in all_orders:
            order['_id'] = str(order['_id'])
            order['user_id'] = str(order['user_id'])
            order['restaurant_id'] = str(order['restaurant_id'])
            order['delivery_person_id'] = str(order['delivery_person_id'])
        return jsonify({"msg": "All orders retrieved successfully", "orders": all_orders}), 200
    except Exception as e:
        return jsonify({"msg": "Error retrieving orders", "error": str(e)}), 500

# Admin delete user
@app.route('/admin/user/<user_id>', methods=['DELETE'])
def admin_delete_user(user_id):
    try:
        result = users.delete_one({"_id": ObjectId(user_id)})
        if result.deleted_count > 0:
            return jsonify({"msg": "User deleted successfully", "user_id": user_id}), 200
        else:
            return jsonify({"msg": "User not found"}), 404
    except Exception as e:
        return jsonify({"msg": "Error deleting user", "error": str(e)}), 500

#Admin delete restaurant
@app.route('/admin/restaurant/<restaurant_id>', methods=['DELETE'])
def admin_delete_restaurant(restaurant_id):
    try:
        # Validate ObjectId
        if not ObjectId.is_valid(restaurant_id):
            return jsonify({"msg": "Invalid restaurant ID"}), 400
        
        # Convert string to ObjectId
        restaurant_object_id = ObjectId(restaurant_id)
        
        # Delete from users collection (assuming _id matches restaurant_id)
        user_result = users.delete_one({"_id": restaurant_object_id, "role": "restaurant_owner"})
        
        # Delete from menus collection (using restaurant_id reference)
        menu_result = menus.delete_many({"restaurant_id": restaurant_object_id})
        
        # Check if anything was deleted
        if user_result.deleted_count > 0 or menu_result.deleted_count > 0:
            return jsonify({
                "msg": "Restaurant deleted successfully",
                "user_deleted": user_result.deleted_count,
                "menu_entries_deleted": menu_result.deleted_count,
                "restaurant_id": restaurant_id
            }), 200
        else:
            return jsonify({"msg": "Restaurant not found"}), 404
    except Exception as e:
        app.logger.error(f"Error deleting restaurant: {e}")
        return jsonify({"msg": "Error deleting restaurant", "error": str(e)}), 500

# Admin delete order
@app.route('/admin/order/<order_id>', methods=['DELETE'])
def admin_delete_order(order_id):
    try:
        result = orders.delete_one({"_id": ObjectId(order_id)})
        if result.deleted_count > 0:
            return jsonify({"msg": "Order deleted successfully", "order_id": order_id}), 200
        else:
            return jsonify({"msg": "Order not found"}), 404
    except Exception as e:
        return jsonify({"msg": "Error deleting order", "error": str(e)}), 500


# Start the Flask app
if __name__ == "__main__":
    print("Starting the server...")
    app.run(debug=True)
