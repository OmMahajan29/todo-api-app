from flask import Flask, jsonify, request
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.exceptions import BadRequest
import unittest

app = Flask(__name__)

# MongoDB configuration
app.config["MONGO_URI"] = "mongodb://localhost:27017/todo_db"
mongo = PyMongo(app)

todo_collection = mongo.db.todos

@app.route("/")
def home():
    return jsonify({"message": "Welcome to the To-Do API! Use /todos to manage tasks."}), 200

@app.route("/todos", methods=["POST"])
def add_todo():
    data = request.get_json()
    if not data or not data.get("title"):
        raise BadRequest("Task title is required.")
    
    todo = {
        "title": data["title"],
        "description": data.get("description", ""),
        "completed": False
    }
    result = todo_collection.insert_one(todo)
    return jsonify({"message": "Task added successfully", "id": str(result.inserted_id)}), 201

@app.route("/todos", methods=["GET"])
def get_todos():
    todos = []
    for todo in todo_collection.find():
        todos.append({
            "id": str(todo["_id"]),
            "title": todo["title"],
            "description": todo.get("description", ""),
            "completed": todo["completed"]
        })
    return jsonify(todos), 200

@app.route("/todos/<todo_id>", methods=["PUT"])
def update_todo(todo_id):
    data = request.get_json()
    if not data:
        raise BadRequest("No data provided to update.")
    
    update_data = {}
    if "title" in data:
        update_data["title"] = data["title"]
    if "description" in data:
        update_data["description"] = data["description"]
    if "completed" in data:
        update_data["completed"] = data["completed"]

    result = todo_collection.update_one({"_id": ObjectId(todo_id)}, {"$set": update_data})
    if result.matched_count == 0:
        return jsonify({"message": "Task not found"}), 404

    return jsonify({"message": "Task updated successfully"}), 200

@app.route("/todos/<todo_id>", methods=["DELETE"])
def delete_todo(todo_id):
    result = todo_collection.delete_one({"_id": ObjectId(todo_id)})
    if result.deleted_count == 0:
        return jsonify({"message": "Task not found"}), 404

    return jsonify({"message": "Task deleted successfully"}), 200

@app.route("/todos", methods=["DELETE"])
def delete_all_todos():
    todo_collection.delete_many({})
    return jsonify({"message": "All tasks deleted successfully"}), 200

if __name__ == "__main__":
    app.run(debug=True)

# Test cases
class TestTodoAPI(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        todo_collection.delete_many({})

    def test_add_todo(self):
        response = self.app.post("/todos", json={"title": "Test Task", "description": "Test Description"})
        self.assertEqual(response.status_code, 201)

    def test_get_todos(self):
        self.app.post("/todos", json={"title": "Test Task"})
        response = self.app.get("/todos")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.get_json()), 1)

    def test_update_todo(self):
        response = self.app.post("/todos", json={"title": "Test Task"})
        todo_id = response.get_json()["id"]
        response = self.app.put(f"/todos/{todo_id}", json={"title": "Updated Task"})
        self.assertEqual(response.status_code, 200)

    def test_delete_todo(self):
        response = self.app.post("/todos", json={"title": "Test Task"})
        todo_id = response.get_json()["id"]
        response = self.app.delete(f"/todos/{todo_id}")
        self.assertEqual(response.status_code, 200)

    def test_delete_all_todos(self):
        self.app.post("/todos", json={"title": "Test Task 1"})
        self.app.post("/todos", json={"title": "Test Task 2"})
        response = self.app.delete("/todos")
        self.assertEqual(response.status_code, 200)

if __name__ == "__main__":
    unittest.main()
