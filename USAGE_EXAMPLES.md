# MongoDB GUI Application - Usage Examples

## Quick Start Example

### 1. Sample MongoDB Connection

```
Name: Local Development
Host: localhost
Port: 27017
Database: myapp
Username: (leave empty for no auth)
Password: (leave empty for no auth)
```

### 2. Sample Queries

#### Basic Find Query

```javascript
{"status": "active"}
```

#### Find with Conditions

```javascript
{"age": {"$gte": 18, "$lt": 65}, "city": "New York"}
```

#### Find with Projection

```javascript
{"name": 1, "email": 1, "_id": 0}
```

#### Aggregation Pipeline

```javascript
[
  { $match: { status: "active" } },
  { $group: { _id: "$department", count: { $sum: 1 } } },
  { $sort: { count: -1 } },
];
```

#### Complex Aggregation

```javascript
[
  { $match: { date: { $gte: "2024-01-01" } } },
  {
    $group: {
      _id: { year: { $year: "$date" }, month: { $month: "$date" } },
      totalSales: { $sum: "$amount" },
      averageOrder: { $avg: "$amount" },
    },
  },
  { $sort: { "_id.year": 1, "_id.month": 1 } },
];
```

## Testing the Application

### Sample Data Setup

If you have MongoDB running locally, you can insert some test data:

```javascript
// In MongoDB shell or compass
use testdb

// Insert sample users
db.users.insertMany([
  {"name": "John Doe", "age": 30, "city": "New York", "status": "active"},
  {"name": "Jane Smith", "age": 25, "city": "Boston", "status": "active"},
  {"name": "Bob Johnson", "age": 35, "city": "Chicago", "status": "inactive"}
])

// Insert sample orders
db.orders.insertMany([
  {"userId": 1, "amount": 100.50, "date": "2024-01-15", "status": "completed"},
  {"userId": 2, "amount": 75.25, "date": "2024-01-20", "status": "pending"},
  {"userId": 1, "amount": 200.00, "date": "2024-02-01", "status": "completed"}
])
```

### Test Queries

Try these queries in the application:

1. **List all active users**: `{"status": "active"}`
2. **Find users by city**: `{"city": "New York"}`
3. **Users over 25**: `{"age": {"$gt": 25}}`
4. **Count by status**: `[{"$group": {"_id": "$status", "count": {"$sum": 1}}}]`

## Features Demonstration

### Connection Management

1. Click "Add Connection" to create a new connection
2. Fill in your MongoDB details
3. Click "Test Connection" to verify it works
4. Save the connection for future use

### Query Execution

1. Select a saved connection and click "Connect"
2. Choose a collection from the browser (left panel)
3. Enter a query in the query text area
4. Click "Execute Query" to see results

### Results Navigation

- Use pagination controls at the bottom
- Results are displayed in a clean table format
- Large result sets are automatically paginated

### Collection Browser

- Left panel shows all collections in the database
- Click on any collection to see sample documents
- Helps understand your data structure

## Troubleshooting

### Common Issues

1. **Connection Failed**

   - Check if MongoDB is running
   - Verify host and port are correct
   - Check authentication credentials

2. **No Collections Visible**

   - Ensure you're connected to the right database
   - Check if the database has any collections
   - Verify user permissions

3. **Query Errors**

   - Check query syntax (must be valid JSON)
   - For aggregation, use array format `[{...}]`
   - For find queries, use object format `{...}`

4. **GUI Not Responding**
   - Large queries may take time to execute
   - Check the status bar for progress
   - Consider limiting result size

### Getting Help

- Check the README.md for detailed documentation
- Run tests with `python -m pytest tests/ -v`
- Check logs for detailed error messages
